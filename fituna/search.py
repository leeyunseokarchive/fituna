"""fituna.search
================

The core orchestrator: quality-first filtering over ``quant_candidates``
(highest quality first), grid search over ``ctx_candidates``, binary search
over ``ngl`` (bounded by ``ngl_max_calls``), with early-exit as soon as a
candidate meets both the target throughput and the quality-loss ceiling.

Algorithm sketch (to be implemented):
    1. Compute/lookup baseline perplexity on the unquantized base GGUF.
    2. For each quant in target.quant_candidates (quality-descending order):
         a. quantize() (idempotent) -> quantized_gguf
         b. evaluate_quality() (cache-aware) -- if quality_loss_pct exceeds
            max_quality_loss_pct, skip this quant entirely (it can only get
            worse at lower quant levels... actually it's evaluated per-quant,
            independent of ngl/ctx, so this check gates the whole quant tier).
         c. For each ctx in target.ctx_candidates:
              - binary search ngl in [0, model_info.n_layers] (<= ngl_max_calls
                bench calls) to find the minimal ngl meeting target_tokens_per_sec,
                or the best achievable if none meets it.
              - run_bench() (cache-aware) at candidate ngl/ctx.
              - if gen_tok_per_sec >= target_tokens_per_sec: record as a hit,
                early-exit the whole search (first quality-ranked hit wins).
    3. If no hit, return the best-effort SearchResult (closest to target)
       with meets_target=False, or raise NoFeasibleConfigError if nothing at
       all could be benchmarked (e.g. every quant tier failed quality check).
    4. Respect target.max_bench_seconds as a wall-clock budget throughout;
       return best-effort on expiry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from fituna.config import (
    BinaryPaths,
    HardwareProfile,
    ModelInfo,
    SearchResult,
    TargetSpec,
)
from fituna.cache import ResultCache


def search(
    target: TargetSpec,
    model_info: ModelInfo,
    hw: HardwareProfile,
    binaries: BinaryPaths,
    work_dir: Path,
    wikitext_path: Path,
    cache: Optional[ResultCache] = None,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> SearchResult:
    """Run the quality-first / grid-search / ngl-binary-search algorithm
    described in the module docstring.

    TODO: implement. Report progress via progress_cb(str) if provided.
    """
    raise NotImplementedError
