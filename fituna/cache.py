"""fituna.cache
===============

sqlite3-backed cache for bench/quality results, keyed by
(model_fingerprint, hardware_fingerprint, candidate) so re-running the same
search (``--resume``) skips subprocess calls that already have an answer.

Schema::

    bench_cache(model_fp, hw_fp, quant, ngl, ctx,
                prompt_tps, gen_tps, vram_mb, raw_stdout, created_at,
                PRIMARY KEY(model_fp, hw_fp, quant, ngl, ctx))

    quality_cache(model_fp, quant, perplexity, baseline_perplexity, loss_pct,
                  created_at,
                  PRIMARY KEY(model_fp, quant))
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fituna.config import BenchResult, CandidateConfig, QualityResult

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bench_cache (
    model_fp TEXT NOT NULL,
    hw_fp TEXT NOT NULL,
    quant TEXT NOT NULL,
    ngl INTEGER NOT NULL,
    ctx INTEGER NOT NULL,
    prompt_tps REAL NOT NULL,
    gen_tps REAL NOT NULL,
    vram_mb INTEGER,
    raw_stdout TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (model_fp, hw_fp, quant, ngl, ctx)
);

CREATE TABLE IF NOT EXISTS quality_cache (
    model_fp TEXT NOT NULL,
    quant TEXT NOT NULL,
    perplexity REAL NOT NULL,
    baseline_perplexity REAL NOT NULL,
    loss_pct REAL NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (model_fp, quant)
);
"""


class ResultCache:
    """sqlite3-backed cache. One connection per instance; caller owns
    lifecycle (no context-manager requirement, but callers may close()).
    """

    def __init__(self, db_path: Path) -> None:
        # TODO: open sqlite3 connection, executescript(_SCHEMA), commit.
        raise NotImplementedError

    def get_bench(
        self, model_fp: str, hw_fp: str, cand: CandidateConfig
    ) -> Optional[BenchResult]:
        # TODO: SELECT by primary key, reconstruct BenchResult or return None.
        raise NotImplementedError

    def put_bench(self, model_fp: str, hw_fp: str, result: BenchResult) -> None:
        # TODO: INSERT OR REPLACE.
        raise NotImplementedError

    def get_quality(self, model_fp: str, quant: str) -> Optional[QualityResult]:
        # TODO: SELECT by primary key, reconstruct QualityResult or return None.
        raise NotImplementedError

    def put_quality(self, model_fp: str, result: QualityResult) -> None:
        # TODO: INSERT OR REPLACE.
        raise NotImplementedError
