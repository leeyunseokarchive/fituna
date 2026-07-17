"""search() orchestration tests -- quantize/bench/quality are faked so this
suite exercises only the early-exit / binary-search / grid-search logic, no
real llama.cpp binaries required.

Skeleton only: fituna.search.search() currently raises NotImplementedError.
Un-skip as it's implemented; replace real quantize/run_bench/evaluate_quality
calls inside search() with monkeypatched fakes here.
"""

import pytest

from fituna.search import search


@pytest.mark.xfail(reason="search.search not yet implemented", strict=False)
def test_search_early_exits_on_first_hit(monkeypatch):
    # TODO: monkeypatch fituna.quantize.quantize, fituna.bench.run_bench,
    # fituna.quality.evaluate_quality with deterministic fakes, then assert
    # search() returns a SearchResult with meets_target=True using the
    # highest-quality quant that satisfies both constraints.
    pass


@pytest.mark.xfail(reason="search.search not yet implemented", strict=False)
def test_search_returns_best_effort_when_no_candidate_meets_target(monkeypatch):
    # TODO: fake all candidates below target_tokens_per_sec, assert
    # meets_target=False on the returned best-effort SearchResult.
    pass
