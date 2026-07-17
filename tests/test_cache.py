"""sqlite3 ResultCache read/write + resume-scenario tests.

Skeleton only: fituna.cache.ResultCache currently raises NotImplementedError
in __init__. Un-skip as it's implemented.
"""

from pathlib import Path

import pytest

from fituna.cache import ResultCache
from fituna.config import BenchResult, CandidateConfig


@pytest.mark.xfail(reason="cache.ResultCache not yet implemented", strict=False)
def test_bench_roundtrip(tmp_path: Path):
    cache = ResultCache(tmp_path / "cache.sqlite3")
    cand = CandidateConfig(quant="Q4_K_M", ngl=32, ctx=4096)
    result = BenchResult(
        candidate=cand,
        prompt_tok_per_sec=100.0,
        gen_tok_per_sec=25.0,
        vram_used_mb=6000,
        raw_stdout="{}",
    )
    cache.put_bench("model-fp", "hw-fp", result)
    fetched = cache.get_bench("model-fp", "hw-fp", cand)
    assert fetched == result


@pytest.mark.xfail(reason="cache.ResultCache not yet implemented", strict=False)
def test_get_bench_miss_returns_none(tmp_path: Path):
    cache = ResultCache(tmp_path / "cache.sqlite3")
    cand = CandidateConfig(quant="Q4_K_M", ngl=32, ctx=4096)
    assert cache.get_bench("no-such-model", "no-such-hw", cand) is None
