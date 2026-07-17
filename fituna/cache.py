"""fituna.cache
================

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

import sqlite3
from datetime import datetime, timezone
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResultCache:
    """sqlite3-backed cache. One connection per instance; caller owns
    lifecycle (no context-manager requirement, but callers may close()).
    """

    def __init__(self, db_path: Path) -> None:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # ponytail: single connection, no pooling -- this is a local CLI tool,
        # not a server; check_same_thread=False costs nothing since search()
        # runs sequentially anyway.
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def get_bench(
        self, model_fp: str, hw_fp: str, cand: CandidateConfig
    ) -> Optional[BenchResult]:
        row = self._conn.execute(
            """SELECT prompt_tps, gen_tps, vram_mb, raw_stdout
               FROM bench_cache
               WHERE model_fp=? AND hw_fp=? AND quant=? AND ngl=? AND ctx=?""",
            (model_fp, hw_fp, cand.quant, cand.ngl, cand.ctx),
        ).fetchone()
        if row is None:
            return None
        prompt_tps, gen_tps, vram_mb, raw_stdout = row
        return BenchResult(
            candidate=cand,
            prompt_tok_per_sec=prompt_tps,
            gen_tok_per_sec=gen_tps,
            vram_used_mb=vram_mb,
            raw_stdout=raw_stdout,
        )

    def put_bench(self, model_fp: str, hw_fp: str, result: BenchResult) -> None:
        cand = result.candidate
        self._conn.execute(
            """INSERT OR REPLACE INTO bench_cache
               (model_fp, hw_fp, quant, ngl, ctx, prompt_tps, gen_tps, vram_mb,
                raw_stdout, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                model_fp,
                hw_fp,
                cand.quant,
                cand.ngl,
                cand.ctx,
                result.prompt_tok_per_sec,
                result.gen_tok_per_sec,
                result.vram_used_mb,
                result.raw_stdout,
                _now(),
            ),
        )
        self._conn.commit()

    def get_quality(self, model_fp: str, quant: str) -> Optional[QualityResult]:
        row = self._conn.execute(
            """SELECT perplexity, baseline_perplexity, loss_pct
               FROM quality_cache WHERE model_fp=? AND quant=?""",
            (model_fp, quant),
        ).fetchone()
        if row is None:
            return None
        perplexity, baseline_perplexity, loss_pct = row
        return QualityResult(
            candidate_quant=quant,
            perplexity=perplexity,
            baseline_perplexity=baseline_perplexity,
            quality_loss_pct=loss_pct,
        )

    def put_quality(self, model_fp: str, result: QualityResult) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO quality_cache
               (model_fp, quant, perplexity, baseline_perplexity, loss_pct, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                model_fp,
                result.candidate_quant,
                result.perplexity,
                result.baseline_perplexity,
                result.quality_loss_pct,
                _now(),
            ),
        )
        self._conn.commit()


def _self_check() -> None:
    """Minimal assert-based sanity check -- roundtrip + miss + resume-reopen.

    Full behavioral coverage lives in tests/test_cache.py; this is just a
    runnable guard against the two ways this file regresses silently: schema
    drift and a cache that doesn't survive being reopened (the whole point of
    ``--resume`` is a fresh ResultCache() over the same db_path).
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "cache.sqlite3"
        cache = ResultCache(db_path)

        cand = CandidateConfig(quant="Q4_K_M", ngl=32, ctx=4096)
        bench = BenchResult(
            candidate=cand,
            prompt_tok_per_sec=100.0,
            gen_tok_per_sec=25.0,
            vram_used_mb=6000,
            raw_stdout="{}",
        )

        # 1. Miss before write.
        assert cache.get_bench("model-fp", "hw-fp", cand) is None

        # 2. Roundtrip.
        cache.put_bench("model-fp", "hw-fp", bench)
        fetched = cache.get_bench("model-fp", "hw-fp", cand)
        assert fetched == bench

        # 3. Different hw_fp/candidate is a distinct key (miss).
        assert cache.get_bench("model-fp", "other-hw", cand) is None
        other_cand = CandidateConfig(quant="Q4_K_M", ngl=0, ctx=4096)
        assert cache.get_bench("model-fp", "hw-fp", other_cand) is None

        # 4. INSERT OR REPLACE: put_bench again with new numbers overwrites, no
        #    duplicate-key crash.
        bench2 = BenchResult(
            candidate=cand,
            prompt_tok_per_sec=110.0,
            gen_tok_per_sec=30.0,
            vram_used_mb=6100,
            raw_stdout="{}",
        )
        cache.put_bench("model-fp", "hw-fp", bench2)
        assert cache.get_bench("model-fp", "hw-fp", cand).gen_tok_per_sec == 30.0

        # 5. Quality cache roundtrip + miss.
        quality = QualityResult(
            candidate_quant="Q4_K_M",
            perplexity=6.1,
            baseline_perplexity=6.0,
            quality_loss_pct=1.67,
        )
        assert cache.get_quality("model-fp", "Q4_K_M") is None
        cache.put_quality("model-fp", quality)
        assert cache.get_quality("model-fp", "Q4_K_M") == quality
        assert cache.get_quality("model-fp", "Q8_0") is None

        cache.close()

        # 6. --resume scenario: reopening the same db_path must see prior data.
        reopened = ResultCache(db_path)
        assert reopened.get_bench("model-fp", "hw-fp", cand).gen_tok_per_sec == 30.0
        assert reopened.get_quality("model-fp", "Q4_K_M") == quality
        reopened.close()


if __name__ == "__main__":
    _self_check()
    print("fituna.cache self-check OK")
