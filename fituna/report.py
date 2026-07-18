"""fituna.report
================

Turns a :class:`~fituna.config.SearchResult` into a ready-to-run
``llama-cli`` command and a JSON / human-readable report.

Pure functions only -- no subprocess calls, no file I/O. Every function here
takes already-computed dataclasses (see fituna/config.py) and returns a
value (str or list[str]).
"""

from __future__ import annotations

import dataclasses
import json
import shutil
from pathlib import Path

from fituna.config import BinaryPaths, CandidateConfig, SearchResult

_LLAMA_CLI_NAMES = ("llama-cli", "llama-cli.exe", "main", "main.exe")


def _find_llama_cli(binaries: BinaryPaths) -> str:
    """Best-effort locate llama-cli next to the known binaries, else PATH.

    llama.cpp does not expose llama-cli in BinaryPaths (it's not needed for
    search/bench/quantize/quality), so we look for it: 1) alongside the
    binaries we do know about (same install dir), 2) on PATH, 3) fall back
    to the bare name so the printed command is still copy-pasteable even if
    this machine happens not to have it installed.
    """
    candidate_dirs = {
        binaries.llama_quantize.parent,
        binaries.llama_bench.parent,
        binaries.llama_perplexity.parent,
    }
    for d in candidate_dirs:
        for name in _LLAMA_CLI_NAMES:
            p = d / name
            if p.is_file():
                return str(p)

    found = shutil.which("llama-cli") or shutil.which("main")
    if found:
        return found

    # no llama-cli found anywhere -- return the bare command name
    # rather than raising. The command is advisory (user copy-pastes it);
    # search/bench/quantize already succeeded without needing llama-cli.
    return "llama-cli"


def build_run_command(
    gguf_path: Path, config: CandidateConfig, binaries: BinaryPaths
) -> list[str]:
    """Build a ready-to-run llama-cli invocation for the chosen config."""
    llama_cli = _find_llama_cli(binaries)
    return [
        llama_cli,
        "-m",
        str(gguf_path),
        "-ngl",
        str(config.ngl),
        "-c",
        str(config.ctx),
    ]


def _to_jsonable(obj):
    """Recursively convert dataclasses/Path into plain JSON-safe values."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _to_jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


def to_json(result: SearchResult) -> str:
    """Serialize SearchResult (and nested dataclasses) to a JSON string."""
    return json.dumps(_to_jsonable(result), indent=2, ensure_ascii=False)


def to_human(result: SearchResult) -> str:
    """Render a short human-readable summary: config, throughput, quality
    loss, meets_target, and the run command."""
    cfg = result.config
    bench = result.bench
    quality = result.quality
    status = "MEETS TARGET" if result.meets_target else "BEST EFFORT (target not met)"

    lines = [
        f"FiTuna result: {status}",
        "",
        f"  quant           : {cfg.quant}",
        f"  ngl             : {cfg.ngl}",
        f"  ctx             : {cfg.ctx}",
        f"  gguf            : {result.gguf_path}",
        "",
        f"  prompt tok/s (pp): {bench.prompt_tok_per_sec:.2f}",
        f"  gen tok/s    (tg): {bench.gen_tok_per_sec:.2f}",
    ]
    if bench.vram_used_mb is not None:
        lines.append(f"  vram used       : {bench.vram_used_mb} MB")
    lines += [
        "",
        f"  perplexity      : {quality.perplexity:.4f} "
        f"(baseline {quality.baseline_perplexity:.4f})",
        f"  quality loss    : {quality.quality_loss_pct:.2f}%",
        "",
        "  run command:",
        f"    {' '.join(result.run_command)}",
    ]
    return "\n".join(lines)


def _self_check() -> None:
    """Minimal assert-based sanity check for this module's core contract."""
    cand = CandidateConfig(quant="Q4_K_M", ngl=20, ctx=4096)

    from fituna.config import BenchResult, QualityResult

    bench = BenchResult(
        candidate=cand,
        prompt_tok_per_sec=123.45,
        gen_tok_per_sec=30.5,
        vram_used_mb=2048,
        raw_stdout="{}",
    )
    quality = QualityResult(
        candidate_quant="Q4_K_M",
        perplexity=6.15,
        baseline_perplexity=6.0,
        quality_loss_pct=2.5,
    )

    # 1. build_run_command: PATH-fallback branch when llama-cli sits nowhere
    #    we know about and isn't on PATH -- must still return a usable,
    #    non-empty command instead of raising. This must hold regardless of
    #    whatever the machine actually running this self-check happens to
    #    have installed (e.g. llama.cpp via Homebrew), so PATH is blanked
    #    for the duration of this one call rather than assumed empty.
    import os as _os

    binaries = BinaryPaths(
        llama_quantize=Path("/nonexistent/llama-quantize"),
        llama_bench=Path("/nonexistent/llama-bench"),
        llama_perplexity=Path("/nonexistent/llama-perplexity"),
    )
    saved_path = _os.environ.get("PATH")
    try:
        _os.environ["PATH"] = ""
        cmd = build_run_command(Path("out/model-Q4_K_M.gguf"), cand, binaries)
    finally:
        if saved_path is None:
            _os.environ.pop("PATH", None)
        else:
            _os.environ["PATH"] = saved_path
    assert cmd[0] == "llama-cli"  # bare-name fallback, no crash
    assert cmd == ["llama-cli", "-m", "out/model-Q4_K_M.gguf", "-ngl", "20", "-c", "4096"]

    # 2. build_run_command: finds llama-cli sitting next to a known binary.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "llama-quantize").touch()
        (tdp / "llama-cli").touch()
        binaries2 = BinaryPaths(
            llama_quantize=tdp / "llama-quantize",
            llama_bench=tdp / "llama-bench",
            llama_perplexity=tdp / "llama-perplexity",
        )
        cmd2 = build_run_command(Path("m.gguf"), cand, binaries2)
        assert cmd2[0] == str(tdp / "llama-cli")

    result = SearchResult(
        config=cand,
        bench=bench,
        quality=quality,
        gguf_path=Path("out/model-Q4_K_M.gguf"),
        run_command=cmd,
        meets_target=True,
    )

    # 3. to_json: round-trips through json.loads, Path becomes a plain str,
    #    nested dataclasses become nested dicts.
    js = to_json(result)
    parsed = json.loads(js)
    assert parsed["gguf_path"] == "out/model-Q4_K_M.gguf"
    assert parsed["config"]["quant"] == "Q4_K_M"
    assert parsed["bench"]["gen_tok_per_sec"] == 30.5
    assert parsed["quality"]["quality_loss_pct"] == 2.5
    assert parsed["meets_target"] is True
    assert parsed["run_command"] == cmd

    # 4. to_human: must surface the key numbers and the run command as text.
    human = to_human(result)
    assert "MEETS TARGET" in human
    assert "Q4_K_M" in human
    assert "30.50" in human
    assert " ".join(cmd) in human

    # 5. best-effort (meets_target=False) must say so, not claim success.
    result_bad = dataclasses.replace(result, meets_target=False)
    assert "BEST EFFORT" in to_human(result_bad)
    assert json.loads(to_json(result_bad))["meets_target"] is False


if __name__ == "__main__":
    _self_check()
    print("fituna.report self-check OK")
