"""Tests for fituna.corpus (the `fituna fetch-corpus` subcommand).

`urllib.request.urlopen` is monkeypatched throughout -- CI has no network
access for this suite. Fakes mirror the real HuggingFace dataset-viewer API
response shape verified by hand (see fituna/corpus.py's module docstring and
.superpowers/sdd/task-2-report.md for the raw request/response this was
checked against).

Covers the four scenarios the task brief calls out explicitly: normal
pagination assembly, behavior when the split has fewer rows than requested,
an HTTP error surfacing as FiTunaError with actionable guidance, and the
atomic-write guarantee (no partial file ever left at the target path) --
plus the preset/override resolution rules and the CLI's stdout license
notice, both of which are also part of the brief's contract.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

import pytest

from fituna import cli, corpus
from fituna.config import FiTunaError


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _page(total: int, offset: int, length: int, field: str = "text") -> dict:
    """Build one page in the real API's verified response shape."""
    remaining = max(0, total - offset)
    n = min(length, remaining)
    rows = [
        {"row_idx": offset + i, "row": {field: f"row{offset + i}"}, "truncated_cells": []}
        for i in range(n)
    ]
    return {
        "features": [{"feature_idx": 0, "name": field, "type": {"dtype": "string", "_type": "Value"}}],
        "rows": rows,
        "num_rows_total": total,
        "num_rows_per_page": corpus.PAGE_SIZE,
        "partial": False,
    }


def _fake_urlopen_factory(total: int, field: str = "text", fail_at_offset: Optional[int] = None):
    """urlopen stand-in serving `total` fake rows, paginating exactly like
    the real API (offset/length query params). If `fail_at_offset` is set,
    any request whose offset is >= that value raises URLError instead of
    returning data -- used to simulate a connection drop mid-fetch."""

    def _fake_urlopen(url, timeout=None):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        offset = int(qs["offset"][0])
        length = int(qs["length"][0])
        if fail_at_offset is not None and offset >= fail_at_offset:
            raise urllib.error.URLError("simulated connection drop")
        payload = _page(total, offset, length, field=field)
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    return _fake_urlopen


@pytest.fixture
def fake_urlopen(monkeypatch):
    """Patch urllib.request.urlopen for one test; returns a setter so each
    test can plug in whatever fake response sequence it needs."""

    def _set(fn):
        monkeypatch.setattr(urllib.request, "urlopen", fn)

    return _set


# ---------------------------------------------------------------------------
# normal pagination assembly
# ---------------------------------------------------------------------------


def test_fetch_corpus_assembles_multiple_pages(fake_urlopen, tmp_path):
    # 250 rows needs 3 requests at PAGE_SIZE=100 (100 + 100 + 50).
    fake_urlopen(_fake_urlopen_factory(total=250))
    out = tmp_path / "corpus.txt"

    n = corpus.fetch_corpus(out, lang="en", rows=250)

    assert n == 250
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines == [f"row{i}" for i in range(250)]


def test_fetch_corpus_reports_progress_once_per_page(fake_urlopen, tmp_path):
    fake_urlopen(_fake_urlopen_factory(total=250))
    out = tmp_path / "corpus.txt"
    messages: list = []

    corpus.fetch_corpus(out, lang="en", rows=250, progress_cb=messages.append)

    assert messages == [
        "fetched 100/250 rows",
        "fetched 200/250 rows",
        "fetched 250/250 rows",
    ]


def test_fetch_corpus_single_page_under_page_size(fake_urlopen, tmp_path):
    fake_urlopen(_fake_urlopen_factory(total=1000))
    out = tmp_path / "corpus.txt"

    n = corpus.fetch_corpus(out, lang="ko", rows=20)

    assert n == 20
    assert out.read_text(encoding="utf-8").splitlines() == [f"row{i}" for i in range(20)]


def test_fetch_corpus_rows_none_defaults_to_lang_preset_row_count(fake_urlopen, tmp_path):
    # en default is 1000, ko default is 500 (task brief) -- rows=None must
    # resolve to the preset's default_rows, not to some other constant.
    fake_urlopen(_fake_urlopen_factory(total=2000))
    out_en = tmp_path / "en.txt"
    out_ko = tmp_path / "ko.txt"

    assert corpus.fetch_corpus(out_en, lang="en", rows=None) == 1000
    assert corpus.fetch_corpus(out_ko, lang="ko", rows=None) == 500


# ---------------------------------------------------------------------------
# row-count shortfall: split has fewer rows than requested (not an error)
# ---------------------------------------------------------------------------


def test_fetch_corpus_stops_early_when_split_is_smaller_than_requested(fake_urlopen, tmp_path):
    fake_urlopen(_fake_urlopen_factory(total=30))
    out = tmp_path / "corpus.txt"

    n = corpus.fetch_corpus(out, lang="en", rows=1000)

    assert n == 30
    assert out.read_text(encoding="utf-8").splitlines() == [f"row{i}" for i in range(30)]


def test_fetch_corpus_handles_an_entirely_empty_split(fake_urlopen, tmp_path):
    fake_urlopen(_fake_urlopen_factory(total=0))
    out = tmp_path / "corpus.txt"

    n = corpus.fetch_corpus(out, lang="en", rows=100)

    assert n == 0
    assert out.read_text(encoding="utf-8") == ""


# ---------------------------------------------------------------------------
# HTTP error -> FiTunaError with actionable guidance, not a raw traceback
# ---------------------------------------------------------------------------


def test_fetch_corpus_wraps_http_error_in_fituna_error_with_guidance(monkeypatch, tmp_path):
    def _fake_urlopen(url, timeout=None):
        raise urllib.error.HTTPError(
            url,
            422,
            "Unprocessable Entity",
            None,
            io.BytesIO(b'{"error": "Parameter \'length\' must not be greater than 100"}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    out = tmp_path / "corpus.txt"

    with pytest.raises(FiTunaError) as exc_info:
        corpus.fetch_corpus(out, lang="en", rows=10)

    message = str(exc_info.value)
    assert "422" in message
    # actionable guidance: the manual-download / --quality-corpus escape hatch
    assert "--quality-corpus" in message
    assert not out.exists()


def test_fetch_corpus_wraps_connection_failure_in_fituna_error(monkeypatch, tmp_path):
    def _fake_urlopen(url, timeout=None):
        raise urllib.error.URLError("Name or service not known")

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    out = tmp_path / "corpus.txt"

    with pytest.raises(FiTunaError) as exc_info:
        corpus.fetch_corpus(out, lang="ko", rows=10)

    assert "--quality-corpus" in str(exc_info.value)
    assert not out.exists()


def test_fetch_corpus_wraps_malformed_json_in_fituna_error(monkeypatch, tmp_path):
    def _fake_urlopen(url, timeout=None):
        return io.BytesIO(b"not json at all")

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    out = tmp_path / "corpus.txt"

    with pytest.raises(FiTunaError):
        corpus.fetch_corpus(out, lang="en", rows=10)
    assert not out.exists()


# ---------------------------------------------------------------------------
# atomic write: a partial download must never leave a file at the target path
# ---------------------------------------------------------------------------


def test_fetch_corpus_leaves_no_partial_file_on_mid_fetch_failure(fake_urlopen, tmp_path):
    # 250 rows needs 3 pages; the connection drops starting on the 2nd.
    fake_urlopen(_fake_urlopen_factory(total=500, fail_at_offset=100))
    out = tmp_path / "corpus.txt"

    with pytest.raises(FiTunaError):
        corpus.fetch_corpus(out, lang="en", rows=250)

    assert not out.exists()
    assert list(tmp_path.iterdir()) == [], "no leftover temp file should remain"


def test_fetch_corpus_does_not_clobber_an_existing_file_on_failure(fake_urlopen, tmp_path):
    out = tmp_path / "corpus.txt"
    out.write_text("previous successful fetch\n", encoding="utf-8")

    fake_urlopen(_fake_urlopen_factory(total=500, fail_at_offset=0))
    with pytest.raises(FiTunaError):
        corpus.fetch_corpus(out, lang="en", rows=250)

    # a failed re-fetch must not touch a pre-existing file at the target path
    assert out.read_text(encoding="utf-8") == "previous successful fetch\n"


def test_fetch_corpus_writes_utf8_with_no_partial_file_possible_mid_write(fake_urlopen, tmp_path):
    """The file that ends up at `out` is only ever the fully-fetched temp
    file, renamed -- never something opened and partially written in place."""
    fake_urlopen(_fake_urlopen_factory(total=3))
    out = tmp_path / "corpus.txt"

    corpus.fetch_corpus(out, lang="en", rows=3)

    assert out.read_text(encoding="utf-8") == "row0\nrow1\nrow2\n"
    # nothing else left behind in the directory besides the final file
    assert [p.name for p in tmp_path.iterdir()] == ["corpus.txt"]


# ---------------------------------------------------------------------------
# preset / override resolution
# ---------------------------------------------------------------------------


def test_resolve_source_uses_the_lang_preset_by_default():
    assert corpus._resolve_source("en", None, None, None) == (
        "Salesforce/wikitext",
        "wikitext-2-raw-v1",
        "test",
        "text",
    )
    assert corpus._resolve_source("ko", None, None, None) == (
        "wikimedia/wikipedia",
        "20231101.ko",
        "train",
        "text",
    )


def test_resolve_source_full_override_ignores_the_preset():
    assert corpus._resolve_source("en", "org/name", "cfg", "split") == (
        "org/name",
        "cfg",
        "split",
        "text",
    )


@pytest.mark.parametrize(
    "dataset, config, split",
    [
        ("org/name", None, None),
        (None, "cfg", None),
        (None, None, "split"),
        ("org/name", "cfg", None),
        ("org/name", None, "split"),
        (None, "cfg", "split"),
    ],
)
def test_resolve_source_rejects_a_partial_override(dataset, config, split):
    with pytest.raises(FiTunaError):
        corpus._resolve_source("en", dataset, config, split)


def test_resolve_source_rejects_unknown_lang():
    with pytest.raises(FiTunaError):
        corpus._resolve_source("de", None, None, None)


def test_fetch_corpus_uses_custom_dataset_when_fully_overridden(fake_urlopen, tmp_path):
    fake_urlopen(_fake_urlopen_factory(total=10))
    out = tmp_path / "corpus.txt"

    n = corpus.fetch_corpus(
        out, lang="en", rows=10, dataset="org/name", config="cfg", split="train"
    )

    assert n == 10


# ---------------------------------------------------------------------------
# missing text field: a custom override pointed at an incompatible dataset
# must fail clearly instead of silently writing a blank-lines corpus
# ---------------------------------------------------------------------------


def test_fetch_corpus_errors_clearly_when_dataset_has_no_text_field(monkeypatch, tmp_path):
    def _fake_urlopen(url, timeout=None):
        payload = {
            "features": [
                {"feature_idx": 0, "name": "content", "type": {"dtype": "string", "_type": "Value"}}
            ],
            "rows": [{"row_idx": 0, "row": {"content": "hello"}, "truncated_cells": []}],
            "num_rows_total": 1,
            "num_rows_per_page": 100,
            "partial": False,
        }
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    out = tmp_path / "corpus.txt"

    with pytest.raises(FiTunaError) as exc_info:
        corpus.fetch_corpus(
            out, lang="en", rows=10, dataset="org/name", config="cfg", split="train"
        )

    assert "content" in str(exc_info.value)  # names the field that IS available
    assert not out.exists()


# ---------------------------------------------------------------------------
# CLI wiring (fituna/cli.py's `fetch-corpus` subcommand)
# ---------------------------------------------------------------------------


def test_cli_fetch_corpus_prints_license_notice_for_a_preset(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli.corpus, "fetch_corpus", lambda *a, **k: 5)
    out = tmp_path / "corpus.txt"

    exit_code = cli.main(["fetch-corpus", "--lang", "en", "--out", str(out), "--rows", "5"])

    assert exit_code == 0
    captured_out = capsys.readouterr().out
    assert "Wrote 5 rows" in captured_out
    assert "CC BY-SA" in captured_out
    assert "Salesforce/wikitext" in captured_out


def test_cli_fetch_corpus_prints_generic_notice_for_a_custom_dataset(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli.corpus, "fetch_corpus", lambda *a, **k: 5)
    out = tmp_path / "corpus.txt"

    exit_code = cli.main(
        [
            "fetch-corpus", "--out", str(out), "--rows", "5",
            "--dataset", "org/name", "--config", "cfg", "--split", "train",
        ]
    )

    assert exit_code == 0
    captured_out = capsys.readouterr().out
    assert "CC BY-SA" not in captured_out  # no unverified license claim for a custom dataset
    assert "org/name" in captured_out


def test_cli_fetch_corpus_passes_parsed_args_through_to_corpus_module(monkeypatch, tmp_path):
    captured = {}

    def _fake_fetch_corpus(out, lang, rows, dataset, config, split, progress_cb=None):
        captured.update(
            out=out, lang=lang, rows=rows, dataset=dataset, config=config, split=split
        )
        return 42

    monkeypatch.setattr(cli.corpus, "fetch_corpus", _fake_fetch_corpus)
    out = tmp_path / "corpus.txt"
    cli.main(["fetch-corpus", "--lang", "ko", "--out", str(out), "--rows", "500"])

    assert captured == {
        "out": out,
        "lang": "ko",
        "rows": 500,
        "dataset": None,
        "config": None,
        "split": None,
    }


def test_cli_fetch_corpus_network_failure_is_a_generic_error_exit_code(monkeypatch, tmp_path):
    def _boom(*a, **k):
        raise FiTunaError("simulated network failure")

    monkeypatch.setattr(cli.corpus, "fetch_corpus", _boom)
    out = tmp_path / "corpus.txt"

    exit_code = cli.main(["fetch-corpus", "--out", str(out)])

    assert exit_code == 1  # generic error -- not one of the special-cased exit codes (2/3)
