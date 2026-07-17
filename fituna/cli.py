"""fituna.cli
=============

argparse-based CLI. Subcommands: ``run``, ``detect-hw``, ``list-binaries``.

CLI <-> dataclass field mapping (see fituna/config.py for the dataclasses):

    --model              -> TargetSpec.model_path
    --target-tps         -> TargetSpec.target_tokens_per_sec
    --max-quality-loss   -> TargetSpec.max_quality_loss_pct
    --ctx (comma-sep ok) -> TargetSpec.ctx_candidates (first value is .ctx)
    --quant (comma-sep)  -> TargetSpec.quant_candidates
                             (always re-sorted to quality-descending order)
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
from typing import Optional, Sequence

logger = logging.getLogger("fituna")


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


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse argv, dispatch to the requested subcommand, map exceptions to
    exit codes.

    TODO: implement dispatch to hardware/binaries/model_info/search/report
    modules per the docstring mapping above. Wrap in try/except:
        BinaryNotFoundError  -> log + return 2
        NoFeasibleConfigError -> log + return 3
        FiTunaError (other)  -> log + return 1
        else success         -> return 0 if result.meets_target else 1
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    raise NotImplementedError(f"subcommand '{args.command}' not yet implemented")


if __name__ == "__main__":
    sys.exit(main())
