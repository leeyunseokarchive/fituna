"""fituna.quality
=================

Runs ``llama-perplexity`` against a wikitext corpus to measure quality loss
of a quantized GGUF relative to the unquantized baseline.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

from fituna.config import BinaryPaths, FiTunaError, QualityResult

# llama-perplexity has no built-in timeout of its own and a full
# wikitext-2 pass on a large model can run long; 30 min is a generous default
# ceiling. Bump via PPL_TIMEOUT_SEC module attribute if a caller needs more.
PPL_TIMEOUT_SEC = 1800

_PPL_RE = re.compile(r"Final estimate:\s*PPL\s*=\s*([\d.]+)")


def _parse_perplexity(text: str) -> Optional[float]:
    """Extract the final PPL value from llama-perplexity's combined
    stdout/stderr, e.g. a line like:
        Final estimate: PPL = 5.9070 +/- 0.03170
    Returns None if no such line is present.
    """
    match = _PPL_RE.search(text)
    if match is None:
        return None
    return float(match.group(1))


def compute_perplexity(
    gguf_path: Path,
    wikitext_path: Path,
    binaries: BinaryPaths,
    chunks: Optional[int] = None,
) -> float:
    """Run `llama-perplexity -m <gguf_path> -f <wikitext_path>` (optionally
    limited to `chunks` chunks to save time) and parse the final PPL value
    from stdout.
    """
    if not gguf_path.exists():
        raise FiTunaError(f"GGUF file not found: {gguf_path}")
    if not wikitext_path.exists():
        raise FiTunaError(
            f"wikitext corpus not found: {wikitext_path} "
            "(see README for the wikitext-2 download link)"
        )

    cmd = [
        str(binaries.llama_perplexity),
        "-m", str(gguf_path),
        "-f", str(wikitext_path),
    ]
    if chunks is not None:
        cmd += ["--chunks", str(chunks)]

    try:
        # encoding/errors explicit: see hardware.py's _run for why.
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=PPL_TIMEOUT_SEC,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise FiTunaError(
            f"llama-perplexity binary not found: {binaries.llama_perplexity}"
        ) from exc
    except OSError as exc:
        # e.g. PermissionError -- binary exists but isn't executable.
        raise FiTunaError(
            f"failed to launch llama-perplexity ({binaries.llama_perplexity}): {exc}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise FiTunaError(
            f"llama-perplexity timed out after {PPL_TIMEOUT_SEC}s on {gguf_path.name}"
        ) from exc

    output = proc.stdout + "\n" + proc.stderr
    if proc.returncode != 0:
        tail = output.strip()[-2000:]
        raise FiTunaError(
            f"llama-perplexity exited with code {proc.returncode} on {gguf_path.name}:\n{tail}"
        )

    ppl = _parse_perplexity(output)
    if ppl is None:
        tail = output.strip()[-2000:]
        raise FiTunaError(
            f"could not parse 'Final estimate: PPL = ...' from llama-perplexity output "
            f"for {gguf_path.name}:\n{tail}"
        )
    return ppl


def evaluate_quality(
    quant: str,
    quantized_gguf: Path,
    baseline_ppl: float,
    wikitext_path: Path,
    binaries: BinaryPaths,
    chunks: Optional[int] = None,
) -> QualityResult:
    """compute_perplexity(quantized_gguf, ...) then derive quality_loss_pct =
    (ppl - baseline_ppl) / baseline_ppl * 100.
    """
    ppl = compute_perplexity(quantized_gguf, wikitext_path, binaries, chunks)
    loss_pct = (ppl - baseline_ppl) / baseline_ppl * 100.0
    return QualityResult(
        candidate_quant=quant,
        perplexity=ppl,
        baseline_perplexity=baseline_ppl,
        quality_loss_pct=loss_pct,
    )


def _self_check() -> None:
    """Assert-based sanity check, no real llama.cpp binary required.

    Covers: (1) PPL regex parsing against realistic output, including the
    "no match" case; (2) quality_loss_pct arithmetic; (3) that a missing
    binary/corpus is surfaced as FiTunaError rather than a raw OSError.
    """
    # 1. Parsing.
    sample = (
        "system_info: n_threads = 8\n"
        "perplexity: calculating perplexity over 655 chunks\n"
        "[1]4.5987,[2]5.1234,...\n"
        "Final estimate: PPL = 5.9070 +/- 0.03170\n"
    )
    assert _parse_perplexity(sample) == 5.9070
    assert _parse_perplexity("no ppl line here") is None

    # 2. quality_loss_pct arithmetic, mirrored from evaluate_quality's formula.
    baseline = 5.80
    ppl = 5.9070
    expected_loss = (ppl - baseline) / baseline * 100.0
    result = QualityResult(
        candidate_quant="Q4_K_M",
        perplexity=ppl,
        baseline_perplexity=baseline,
        quality_loss_pct=expected_loss,
    )
    assert abs(result.quality_loss_pct - 1.8448) < 1e-3

    # 3. Missing wikitext corpus -> FiTunaError, not a bare exception.
    fake_binaries = BinaryPaths(
        llama_quantize=Path("/nonexistent/llama-quantize"),
        llama_bench=Path("/nonexistent/llama-bench"),
        llama_perplexity=Path("/nonexistent/llama-perplexity"),
    )
    try:
        compute_perplexity(
            gguf_path=Path(__file__),  # exists, just not a real gguf
            wikitext_path=Path("/nonexistent/wikitext.txt"),
            binaries=fake_binaries,
        )
        raise AssertionError("expected FiTunaError for missing wikitext corpus")
    except FiTunaError:
        pass

    # 4. Missing binary -> FiTunaError (via FileNotFoundError translation).
    try:
        compute_perplexity(
            gguf_path=Path(__file__),
            wikitext_path=Path(__file__),  # any existing file stands in for corpus
            binaries=fake_binaries,
        )
        raise AssertionError("expected FiTunaError for missing llama-perplexity binary")
    except FiTunaError:
        pass


if __name__ == "__main__":
    _self_check()
    print("fituna.quality self-check OK")
