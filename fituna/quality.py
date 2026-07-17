"""fituna.quality
=================

Runs ``llama-perplexity`` against a wikitext corpus to measure quality loss
of a quantized GGUF relative to the unquantized baseline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fituna.config import BinaryPaths, QualityResult


def compute_perplexity(
    gguf_path: Path,
    wikitext_path: Path,
    binaries: BinaryPaths,
    chunks: Optional[int] = None,
) -> float:
    """Run `llama-perplexity -m <gguf_path> -f <wikitext_path>` (optionally
    limited to `chunks` chunks to save time) and parse the final PPL value
    from stdout.

    TODO: implement subprocess call + regex parse of "Final estimate: PPL = X".
    """
    raise NotImplementedError


def evaluate_quality(
    quant: str,
    quantized_gguf: Path,
    baseline_ppl: float,
    wikitext_path: Path,
    binaries: BinaryPaths,
) -> QualityResult:
    """compute_perplexity(quantized_gguf, ...) then derive quality_loss_pct =
    (ppl - baseline_ppl) / baseline_ppl * 100.

    TODO: implement.
    """
    raise NotImplementedError
