# Contributing to FiTuna

Thanks for your interest! FiTuna is a small, dependency-free Python CLI — the
bar to contribute is deliberately low.

## Development setup

```bash
git clone <repo-url>
cd fituna
python3.11 -m venv .venv && source .venv/bin/activate   # 3.11+ required
pip install -e .
pip install pytest
```

No runtime dependencies. `pytest` is the only dev dependency.

## Running tests

```bash
pytest -q                      # unit tests (mock subprocess, fast)
python -m fituna.search        # per-module self-checks, e.g.
python -m fituna.cli --selfcheck
```

Real-binary integration testing requires a llama.cpp build on PATH (or
`--llama-bin-dir`); see README "Verify your setup".

## Making changes

- **Contract first**: cross-module data shapes live in `fituna/config.py`
  (frozen dataclasses). If your change alters what modules exchange, change
  the dataclass there and update every consumer in the same PR.
- **Keep zero dependencies**: PRs adding runtime dependencies need a strong
  justification. stdlib-only is a project feature, not an accident.
- **Tests**: every behavior change needs a unit test (mock the subprocess
  layer like `tests/test_search.py` does) or a self-check assertion.
- **Style**: match surrounding code. No new abstractions for single call
  sites.

## Reporting bugs

Open an issue with:
- the full `fituna` command you ran,
- OS / hardware (`fituna detect-hw` output),
- llama.cpp build (`fituna list-binaries` output),
- the error output.

## License

By contributing you agree your contributions are licensed under the MIT
License (see `LICENSE`).
