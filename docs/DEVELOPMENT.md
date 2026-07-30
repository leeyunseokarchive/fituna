# Development methodology

This document describes how FiTuna is actually built and verified. Everything
here is a habit the repository already follows and that you can check against
the code, the CI configuration, or the pull-request history. Where something is
a plan rather than a practice it is labelled **(plan)**.

For *what* the code does, see [ARCHITECTURE.md](ARCHITECTURE.md); for how to
set up and contribute, see [CONTRIBUTING.md](../CONTRIBUTING.md); for the
release history, see [CHANGELOG.md](../CHANGELOG.md).

## 1. Contract-first design

Every data shape that crosses a module boundary is a frozen dataclass or enum
in [`fituna/config.py`](../fituna/config.py): `HardwareProfile`, `TargetSpec`,
`BinaryPaths`, `ModelInfo`, `CandidateConfig`, `BenchResult`, `QualityResult`,
`SearchResult`, `DoctorCheck`, `CorpusPreset`. That module is the single source
of truth for the interface; the modules around it (`hardware`, `binaries`,
`quantize`, `quality`, `bench`, `search`, `cache`, `report`) exchange those
types and nothing else.

They are `frozen=True` deliberately: a result that has been measured, cached
and reported must not be mutable further down the pipeline. `config.py`'s own
self-check asserts the freeze — mutating a `HardwareProfile` or a
`SearchResult` has to raise, not silently succeed — so the immutability is a
tested property, not a convention.

Practical consequence, stated in `CONTRIBUTING.md`: a change to what modules
exchange means changing the dataclass in `config.py` and updating every
consumer in the same pull request.

## 2. Per-module self-checks

All sixteen modules in `fituna/` (everything but the three-line `__main__.py`
shim) are runnable on their own and assert their own core invariants:

```bash
python -m fituna.config          # frozen-dataclass contract
python -m fituna.search          # search-order and early-exit logic
python -m fituna.cli --selfcheck # entry points take an explicit flag
```

The two modules whose `__main__` is a real entry point (`cli`, `mcp_server`)
gate their check behind an explicit `--selfcheck` flag, so that
`python -m fituna.cli` still runs the CLI. Every other module — `doctor` and
`corpus` included — runs its check unconditionally under
`if __name__ == "__main__":` and ignores any argument. CI passes
`--selfcheck` to `doctor` and `corpus` too, which is harmless and keeps the
four argument-taking modules' invocations uniform. These are assertion-based checks embedded
next to the code they cover, not a second test framework — they exist so that a
single module can be verified in isolation, including on a machine that has not
installed pytest.

They are not optional or informational: [CI](../.github/workflows/ci.yml) runs
all sixteen of them as a required step, on every OS and Python version in the
matrix, alongside the test suite. A self-check that fails fails the build.

## 3. Mocked-subprocess unit tests

The suite is 152 tests across `tests/`, and it is designed to pass on a machine
with **no llama.cpp installed and no network access**. Every external effect is
monkeypatched at its boundary:

- `subprocess.run` itself, for the hardware probes (`nvidia-smi`, `rocm-smi`,
  `system_profiler`) — the tests drive the parser with recorded tool output,
  including the "executable not found" case
- `urllib.request.urlopen` for `fituna fetch-corpus`, plus `tempfile.mkstemp`
  to exercise the atomic-write path
- the wrapper functions themselves where the unit under test is the
  orchestration (`search` runs against fake `quantize`/`bench`/`quality`;
  `doctor` against fake `binaries.find_exe`, `get_llama_cpp_version`,
  `detect_hardware`, `shutil.disk_usage`, `os.access`)

Real tool output is preserved as a fixture
(`tests/fixtures/llama_bench_sample.json`), but its only consumer is
`fituna/bench.py`'s own `_self_check()` (`bench.py:147`) — that's Section 2's
per-module self-check mechanism, not this pytest suite. No `tests/` file
loads it. The substance still holds — the parser this fixture drives is
tested against text llama.cpp actually printed rather than text we
imagined — it just happens outside `pytest -q`.

This is a deliberate trade, and it has a known cost: **the suite cannot catch a
bug in how FiTuna talks to llama.cpp**, because in the suite llama.cpp is a
mock that behaves as we assumed. Every one of the flag-and-protocol bugs in the
0.1.0 changelog — `llama-bench` having no `-c` flag, `--version` being rejected,
a CPU-only bench never finishing — passed the full suite. Section 6 is the
answer to that, and it is why it is a separate step rather than more tests.

What the suite *does* cover well is everything above the subprocess boundary:
search order and early exits, cache keying and schema migration,
hardware-probe output parsing (`test_hardware.py`, against recorded
`nvidia-smi`/`rocm-smi`/`system_profiler` text), hardware-detection
fallbacks, error mapping and exit codes, and cross-platform path handling.
It does *not* cover parsing `llama-bench`, `llama-perplexity` or
`llama-quantize` output: `tests/` has six files
(`test_cache`, `test_config`, `test_corpus`, `test_doctor`, `test_hardware`,
`test_search`) and none of them exercise `bench.py`, `quality.py`,
`quantize.py`, `report.py` or `binaries.py` directly. `model_info.py` is the
one exception among the subprocess wrappers: `test_config.py` covers its
`is_already_quantized` guard, though not its GGUF header parsing. Those
modules' parsing logic is otherwise covered only by their own per-module
self-checks (Section 2) — `bench.py`'s is the one that reads the fixture
named above.

## 4. CI matrix: 3 OS × 2 Python

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on every pull
request and every push to `main`:

| | Python 3.11 | Python 3.13 |
|---|---|---|
| ubuntu-latest | ✅ | ✅ |
| macos-latest | ✅ | ✅ |
| windows-latest | ✅ | ✅ |

Six jobs, `fail-fast: false` so one platform's failure does not hide another's.
Each job installs the package with `pip install -e .` plus pytest — that install
is itself the zero-runtime-dependency check, since anything FiTuna imported and
did not declare would fail there — then runs `pytest -q` and all sixteen module
self-checks.

3.11 is the floor declared in `pyproject.toml`; 3.13 is the current release.
Windows is in the matrix because FiTuna manipulates paths and parses tool
output, and both differ there — the first real Windows CI run caught a test
that broke only because a Windows path contains `\U`, an invalid regex escape.

Not in CI, by choice: no linter, no formatter, no type checker, no coverage
gate. The package ships `py.typed` and is annotated, but nothing verifies the
annotations today **(plan)**.

## 5. Branch → pull request → review → merge

Work happens on a topic branch (`feat/…`, `fix/…`, `docs/…`, `chore/…`), never
directly on `main`. Each branch becomes a pull request, and `main` only moves
through a merge commit — the history shows PRs #1–#6 merged this way.

FiTuna is a solo project, so "review" means a written self-review recorded as a
review on the pull request before merge, and the resulting fixes pushed to the
same branch as their own commits. That record is the point: the review body
names what was checked rather than assumed, and the follow-up commits are
traceable to it. Examples in the history:

- PR #1 (`fituna doctor`) → `fix: address doctor review findings (Windows tests,
  dual binary path, naming)` and `fix: close doctor's never-raises gaps`
- PR #2 (`fetch-corpus`) → `fix: address fetch-corpus review findings
  (os.replace guard, rows<=0, docs)` and a final cleanup pass
- PR #6 (Run 5) → three review passes, each catching the previous pass
  overclaiming, ending in a **retraction** of a published measurement finding

That last one is the standard the review is held to. A review that only
confirms the change is a review that did not happen; the review on PR #6 killed
its own headline result after the per-chunk trace failed to support it, and PR
#4 corrected a false model-license claim in a document that had already been
published. A finding too large to fix inside its branch is written down where
it stays visible — named in the review body and carried onto the README
roadmap — rather than quietly dropped; the standing example is
`quality.py` discarding the `±` standard error that `llama-perplexity`
prints, deferred because capturing it invalidates the cache every published
number traces to.

The related repository practice: measured numbers in the documentation trace to
a log line or a cache row, and a claim that cannot be traced is removed rather
than softened.

## 6. Real-hardware end-to-end validation

Because the test suite deliberately cannot exercise llama.cpp (section 3), a
change that touches the subprocess boundary is validated separately, by running
the tool against real binaries and real models. This step is manual and is not
part of CI — GitHub's runners have no GPU and no llama.cpp build.

What a validation run covers:

1. `fituna doctor` against the real llama.cpp build, then `fituna list-binaries`
   to confirm the detected build version.
2. A full `fituna run` to a successful result (exit 0) with real
   quantize / bench / perplexity subprocesses.
3. The `--resume` cache-hit path on a second run.
4. The failure paths: missing binary (exit 2) and no feasible config with a
   best-effort report (exit 3).

Runs are written up with their logs, timings and hardware in
[RESULTS.md](RESULTS.md) — including run-to-run variance and a thermal-throttle
outlier that was kept rather than discarded — so a reader can check the numbers
instead of trusting them. Platform coverage so far: macOS (Apple Silicon /
Metal) and Linux (NVIDIA Tesla T4 / CUDA, reproducible by anyone through
[the Colab notebook](../notebooks/colab_nvidia_verification.ipynb)). Windows is
unit-tested and CI-run but has not been validated against real binaries; the
README lists this under Known limitations rather than claiming coverage.

[REVIEWERS.md](../REVIEWERS.md) is the Korean-language version of this
procedure, written so a third party can reproduce the published results.

## 7. Dependencies and licensing

Zero runtime dependencies is a hard constraint, not a preference: `pytest` is
the only development dependency, and stdlib-only extends even to the MCP server
(JSON-RPC over stdio is implemented directly rather than pulling in an SDK) and
to corpus downloading (`urllib`, not `datasets`). CI's `pip install -e .`
enforces the declaration side of it on every run.

Licensing is tracked rather than assumed: SPDX headers on every Python file,
`REUSE.toml`, and a compliance record covering the tools FiTuna invokes and the
corpora and models used in the measured runs — see
[LICENSE_COMPLIANCE.md](LICENSE_COMPLIANCE.md),
[SBOM.md](SBOM.md),
[OPEN_SOURCE_USAGE.md](OPEN_SOURCE_USAGE.md) and
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
AI-assisted development is disclosed in
[AI_MODEL_USAGE.md](AI_MODEL_USAGE.md).
