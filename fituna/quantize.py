"""fituna.quantize
==================

Thin, idempotent wrapper around the ``llama-quantize`` subprocess.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from fituna.config import BinaryPaths, BinaryNotFoundError, FiTunaError

# ponytail: base GGUF files produced by model_info.ensure_base_gguf are named
# like "<model>-f16.gguf" / "<model>-f32.gguf" (see model_info.py contract:
# work_dir/base-f16.gguf). Strip that float-precision suffix so the quantized
# output reads as "<model>-<quant>.gguf" instead of "<model>-f16-<quant>.gguf".
# If the base file doesn't match the pattern, just use its stem as-is.
_BASE_SUFFIX_RE = re.compile(r"-f(?:16|32)$", re.IGNORECASE)


def _model_stem(base_gguf: Path) -> str:
    stem = base_gguf.stem
    return _BASE_SUFFIX_RE.sub("", stem) or stem


def quantize(base_gguf: Path, quant: str, out_dir: Path, binaries: BinaryPaths) -> Path:
    """Run `llama-quantize <base_gguf> <out_dir>/<model>-<quant>.gguf <quant>`.

    If the target file already exists in out_dir, skip the subprocess call
    and return its path directly (idempotent / cache-friendly).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{_model_stem(base_gguf)}-{quant}.gguf"

    # Idempotent: a previous run already produced this exact quant. A
    # zero-byte file means a prior run was killed mid-write; don't trust it.
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path

    cmd = [str(binaries.llama_quantize), str(base_gguf), str(out_path), quant]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise BinaryNotFoundError(
            f"llama-quantize not found at '{binaries.llama_quantize}'. "
            "Build llama.cpp (https://github.com/ggerganov/llama.cpp) and either "
            "put its binaries on PATH or pass --llama-bin-dir to fituna."
        ) from exc
    except OSError as exc:
        # e.g. PermissionError -- binary exists but isn't executable. Distinct
        # from BinaryNotFoundError (which means "go build/install it"): this
        # means "it's there, but something's wrong with it".
        raise FiTunaError(
            f"failed to launch llama-quantize ({binaries.llama_quantize}): {exc}"
        ) from exc

    if proc.returncode != 0 or not out_path.exists():
        # Clean up a partial/failed output so a later call doesn't think it's cached.
        if out_path.exists() and out_path.stat().st_size == 0:
            out_path.unlink()
        raise FiTunaError(
            f"llama-quantize failed for quant={quant!r} (exit code {proc.returncode}).\n"
            f"command: {' '.join(cmd)}\n"
            f"stderr:\n{proc.stderr}"
        )

    return out_path


def _self_check() -> None:
    """Minimal assert-based sanity check: idempotency, failure handling,
    missing-binary handling, and the base-suffix-stripping naming rule.
    """
    import stat
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        out_dir = tmp / "out"
        base_gguf = tmp / "base-f16.gguf"
        base_gguf.write_bytes(b"fake-gguf-bytes")

        # --- fake llama-quantize that writes the output file and records
        # how many times it was invoked (to prove idempotency skips the 2nd call).
        counter_file = tmp / "calls.txt"
        fake_quantize = tmp / "fake_llama_quantize.sh"
        fake_quantize.write_text(
            "#!/bin/sh\n"
            f'echo x >> "{counter_file}"\n'
            'cp "$1" "$2"\n'
            "exit 0\n"
        )
        fake_quantize.chmod(fake_quantize.stat().st_mode | stat.S_IEXEC)

        binaries = BinaryPaths(
            llama_quantize=fake_quantize,
            llama_bench=Path("unused"),
            llama_perplexity=Path("unused"),
        )

        # 1. First call invokes the subprocess and produces the expected path,
        #    with the "-f16" base suffix stripped from the model name.
        p1 = quantize(base_gguf, "Q4_K_M", out_dir, binaries)
        assert p1 == out_dir / "base-Q4_K_M.gguf", p1
        assert p1.exists()
        assert counter_file.read_text().count("x") == 1

        # 2. Second call with identical args is idempotent: no re-invocation.
        p2 = quantize(base_gguf, "Q4_K_M", out_dir, binaries)
        assert p2 == p1
        assert counter_file.read_text().count("x") == 1, "must not re-run when cached"

        # 3. A different quant produces a different, independently-generated file.
        p3 = quantize(base_gguf, "Q8_0", out_dir, binaries)
        assert p3 == out_dir / "base-Q8_0.gguf"
        assert counter_file.read_text().count("x") == 2

        # --- failure path: fake binary that always exits non-zero.
        fake_fail = tmp / "fake_fail.sh"
        fake_fail.write_text("#!/bin/sh\necho boom 1>&2\nexit 1\n")
        fake_fail.chmod(fake_fail.stat().st_mode | stat.S_IEXEC)
        fail_binaries = BinaryPaths(
            llama_quantize=fake_fail, llama_bench=Path("unused"), llama_perplexity=Path("unused")
        )
        try:
            quantize(base_gguf, "Q3_K_M", out_dir, fail_binaries)
            raise AssertionError("expected FiTunaError on non-zero exit")
        except FiTunaError as exc:
            assert not isinstance(exc, BinaryNotFoundError)
            assert "Q3_K_M" in str(exc)
        assert not (out_dir / "base-Q3_K_M.gguf").exists()

        # --- missing binary path: BinaryNotFoundError with an install hint.
        missing_binaries = BinaryPaths(
            llama_quantize=tmp / "does-not-exist",
            llama_bench=Path("unused"),
            llama_perplexity=Path("unused"),
        )
        try:
            quantize(base_gguf, "Q2_K", out_dir, missing_binaries)
            raise AssertionError("expected BinaryNotFoundError for missing binary")
        except BinaryNotFoundError as exc:
            assert "llama-quantize" in str(exc)

        # --- stem stripping: a base file without the -f16/-f32 suffix keeps its stem.
        other_base = tmp / "mymodel.gguf"
        other_base.write_bytes(b"x")
        assert _model_stem(other_base) == "mymodel"
        assert _model_stem(base_gguf) == "base"


if __name__ == "__main__":
    _self_check()
    print("fituna.quantize self-check OK")
