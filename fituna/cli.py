"""fituna.cli
=============

argparse-based CLI. Subcommands: ``run``, ``detect-hw``, ``list-binaries``.

CLI <-> dataclass field mapping (see fituna/config.py for the dataclasses):

    --model              -> TargetSpec.model_path
    --target-tps         -> TargetSpec.target_tokens_per_sec
    --max-quality-loss   -> TargetSpec.max_quality_loss_pct
    --ctx (comma-sep ok) -> TargetSpec.ctx_candidates (first value is .ctx)
    --quant (comma-sep)  -> TargetSpec.quant_candidates
                             (always re-sorted to quality-descending order,
                             using the canonical order documented on
                             TargetSpec.quant_candidates' default)
    --gpu / --vram-mb    -> hardware.parse_manual_hardware(...)
    --llama-bin-dir      -> binaries.locate_binaries(bin_dir=...)
    --wikitext           -> quality module input corpus path (required)
    --out                -> work_dir
    --json                -> report.to_json(...) instead of to_human(...)
    --resume              -> activates a ResultCache at <out>/.fituna_cache.sqlite3

Exit codes:
    0 = success (meets_target)
    1 = generic error
    2 = BinaryNotFoundError
    3 = NoFeasibleConfigError
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import asdict, fields
from pathlib import Path
from typing import Optional, Sequence

from fituna import binaries, hardware, model_info, report, search
from fituna.cache import ResultCache
from fituna.config import BinaryPaths, HardwareProfile, TargetSpec
from fituna.errors import BinaryNotFoundError, FiTunaError, NoFeasibleConfigError

logger = logging.getLogger("fituna")

# Canonical quality-descending quant order, reused (not re-hardcoded) from
# TargetSpec.quant_candidates' documented default ("품질 내림차순 고정 순서").
_QUANT_QUALITY_ORDER: tuple[str, ...] = next(
    f.default for f in fields(TargetSpec) if f.name == "quant_candidates"
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fituna", description=__doc__)
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug logging"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="search for a config meeting the target spec")
    run.add_argument("--model", required=True, help="path to .gguf file or HF model dir")
    run.add_argument("--target-tps", type=float, required=True, dest="target_tps")
    run.add_argument(
        "--max-quality-loss", type=float, required=True, dest="max_quality_loss"
    )
    run.add_argument("--ctx", default="4096", help="comma-separated context length(s)")
    run.add_argument(
        "--quant",
        default="Q8_0,Q6_K,Q5_K_M,Q4_K_M,Q3_K_M,Q2_K",
        help="comma-separated quant type candidates",
    )
    run.add_argument("--gpu", choices=["none", "nvidia", "amd", "apple"], default=None)
    run.add_argument("--vram-mb", type=int, default=None, dest="vram_mb")
    run.add_argument("--llama-bin-dir", default=None, dest="llama_bin_dir")
    run.add_argument("--wikitext", required=True, help="path to wikitext corpus")
    run.add_argument("--out", default="./out", help="working/output directory")
    run.add_argument("--json", action="store_true", help="emit JSON report to stdout")
    run.add_argument(
        "--resume", action="store_true", help="reuse cached bench/quality results"
    )

    sub.add_parser("detect-hw", help="print auto-detected hardware profile")

    lb = sub.add_parser("list-binaries", help="show resolved llama.cpp binaries")
    lb.add_argument("--llama-bin-dir", default=None, dest="llama_bin_dir")

    return parser


def _parse_ctx_candidates(raw: str) -> tuple[int, ...]:
    """Comma-separated ints -> de-duplicated tuple, order preserved (first
    entry becomes TargetSpec.ctx)."""
    seen: set[int] = set()
    ordered: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        value = int(part)
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    if not ordered:
        raise ValueError("--ctx must contain at least one context length")
    return tuple(ordered)


def _sort_quants_by_quality(raw: str) -> tuple[str, ...]:
    """Comma-separated quant names -> de-duplicated tuple sorted by the
    canonical quality-descending order. Unrecognized quant strings sort
    last, in their original relative order (stable sort)."""
    order = {q: i for i, q in enumerate(_QUANT_QUALITY_ORDER)}
    seen: set[str] = set()
    quants: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if part and part not in seen:
            seen.add(part)
            quants.append(part)
    if not quants:
        raise ValueError("--quant must contain at least one quant type")
    return tuple(sorted(quants, key=lambda q: order.get(q, len(order))))


def _format_hardware(hw: HardwareProfile) -> str:
    d = asdict(hw)
    d["gpu_vendor"] = hw.gpu_vendor.value
    return "\n".join(f"{k}: {v}" for k, v in d.items())


def _format_binaries(
    paths: BinaryPaths, quant_types: list[str], version: Optional[str]
) -> str:
    lines = [
        f"llama_quantize: {paths.llama_quantize}",
        f"llama_bench: {paths.llama_bench}",
        f"llama_perplexity: {paths.llama_perplexity}",
        f"llama_imatrix: {paths.llama_imatrix or '(not found)'}",
        f"convert_script: {paths.convert_script or '(not found)'}",
        f"llama.cpp version: {version or 'unknown'}",
        "supported quant types: "
        + (", ".join(quant_types) if quant_types else "unknown"),
    ]
    return "\n".join(lines)


def _cmd_detect_hw(args: argparse.Namespace) -> int:
    hw = hardware.detect_hardware()
    print(_format_hardware(hw))
    return 0


def _cmd_list_binaries(args: argparse.Namespace) -> int:
    bin_dir = Path(args.llama_bin_dir) if args.llama_bin_dir else None
    paths = binaries.locate_binaries(bin_dir=bin_dir)
    quant_types = binaries.list_supported_quant_types(paths)
    version = binaries.get_llama_cpp_version(paths)
    print(_format_binaries(paths, quant_types, version))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    ctx_candidates = _parse_ctx_candidates(args.ctx)
    quant_candidates = _sort_quants_by_quality(args.quant)

    bin_dir = Path(args.llama_bin_dir) if args.llama_bin_dir else None
    bins = binaries.locate_binaries(bin_dir=bin_dir)

    hw = hardware.parse_manual_hardware(args.gpu, args.vram_mb)

    work_dir = Path(args.out)
    work_dir.mkdir(parents=True, exist_ok=True)

    model_path = Path(args.model)
    base_gguf = model_info.ensure_base_gguf(model_path, work_dir, bins)
    minfo = model_info.read_model_info(base_gguf, bins)

    target = TargetSpec(
        model_path=model_path,
        target_tokens_per_sec=args.target_tps,
        max_quality_loss_pct=args.max_quality_loss,
        ctx=ctx_candidates[0],
        ctx_candidates=ctx_candidates,
        quant_candidates=quant_candidates,
    )

    cache = ResultCache(work_dir / ".fituna_cache.sqlite3") if args.resume else None
    wikitext_path = Path(args.wikitext)

    result = search.search(
        target,
        minfo,
        hw,
        bins,
        work_dir,
        wikitext_path,
        cache=cache,
        progress_cb=logger.info,
    )

    print(report.to_json(result) if args.json else report.to_human(result))
    return 0 if result.meets_target else 1


_DISPATCH = {
    "run": _cmd_run,
    "detect-hw": _cmd_detect_hw,
    "list-binaries": _cmd_list_binaries,
}


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse argv, dispatch to the requested subcommand, map exceptions to
    exit codes:
        BinaryNotFoundError   -> log + return 2
        NoFeasibleConfigError -> log + return 3
        FiTunaError (other)   -> log + return 1
        unexpected Exception  -> log + return 1
        success               -> return 0 if result.meets_target else 1
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        return _DISPATCH[args.command](args)
    except BinaryNotFoundError as e:
        logger.error(str(e))
        return 2
    except NoFeasibleConfigError as e:
        logger.error(str(e))
        if e.closest is not None:
            try:
                logger.info(
                    "closest best-effort attempt:\n%s", report.to_human(e.closest)
                )
            except Exception:  # pragma: no cover - reporting must not mask exit code
                pass
        return 3
    except FiTunaError as e:
        logger.error(str(e))
        return 1
    except Exception:
        logger.exception("unexpected error")
        return 1


def _selfcheck() -> None:
    """Pure-logic sanity check for parser wiring and the CLI<->dataclass
    mapping described in the module docstring. No subprocess/filesystem/
    network I/O -- safe to run anywhere.

    Run directly: ``python -m fituna.cli --selfcheck`` (running the file
    path directly, e.g. ``python fituna/cli.py``, fails to import the
    ``fituna`` package itself -- the script's own directory *is* the
    package, so it doesn't appear on ``sys.path``).
    """
    parser = _build_parser()

    run_args = parser.parse_args(
        [
            "run",
            "--model",
            "m.gguf",
            "--target-tps",
            "20",
            "--max-quality-loss",
            "5",
            "--ctx",
            "8192,4096,2048,4096",
            "--quant",
            "Q2_K,Q8_0,FOO,Q6_K",
            "--wikitext",
            "wiki.txt",
        ]
    )
    assert run_args.command == "run"
    assert run_args.target_tps == 20.0
    assert run_args.max_quality_loss == 5.0

    ctxs = _parse_ctx_candidates(run_args.ctx)
    assert ctxs == (8192, 4096, 2048), ctxs  # de-duplicated, order preserved
    assert ctxs[0] == 8192  # first value becomes TargetSpec.ctx

    quants = _sort_quants_by_quality(run_args.quant)
    # quality-descending: Q8_0 before Q6_K before Q2_K; unknown "FOO" sorts last
    assert quants == ("Q8_0", "Q6_K", "Q2_K", "FOO"), quants

    dh_args = parser.parse_args(["detect-hw"])
    assert dh_args.command == "detect-hw"

    lb_args = parser.parse_args(["list-binaries", "--llama-bin-dir", "/opt/llama"])
    assert lb_args.command == "list-binaries"
    assert lb_args.llama_bin_dir == "/opt/llama"

    try:
        _parse_ctx_candidates("")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for empty --ctx")

    print("fituna.cli self-check OK")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selfcheck":
        _selfcheck()
        sys.exit(0)
    sys.exit(main())
