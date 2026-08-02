# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`fituna quickstart`** — an interactive six-step wizard (environment
  check → targets → license requirements → model → quality corpus → confirm
  and run). It is a shell over `fituna run`'s own flags and nothing more: it
  prints the fully assembled `fituna run ...` command, then parses that same
  argv back through the CLI parser and executes it in-process, so what is
  shown and what runs cannot diverge. Requires a TTY (exit 1 otherwise,
  pointing at `fituna run`).
  It refuses to predict throughput and says so on screen. Memory fit is
  arithmetic only — published file size vs detected VRAM/RAM, with the
  assumed 20 % margin stated as an assumption. The three project-verified
  models carry a "license text verified" badge; every HuggingFace search
  result is labelled uploader-supplied metadata with the uploader's link,
  and gated repositories are marked unusable. Past `docs/RESULTS.md`
  measurements appear only as records of what was measured on named
  hardware. The HuggingFace `/api/models` response shape was verified
  against the live API before the parser was written.

- **Artifact-centric result exits.** The quantized `.gguf` the search
  already produced is now the headline of the result (path + size), followed
  by the three ways to use it, in order: a `llama-server` command (the
  OpenAI-compatible local API), Ollama, and `llama-cli` — demoted to what it
  actually is, an interactive check. `report.build_server_command()` resolves
  `llama-server` exactly the way `llama-cli` is resolved: **located, never
  executed**, falling back to the bare name (and saying so) when it isn't
  installed.
- **`fituna run --export-ollama`** writes an Ollama `Modelfile`
  (`FROM ./<gguf>` + the measured `num_gpu`/`num_ctx`) next to the `.gguf`,
  atomically. The `FROM` path is relative so the `--out` directory stays
  relocatable. PARAMETER names verified against Ollama's documentation on
  2026-08-02, not written from memory.
- **`run --json` gains `llama_server_command` and `modelfile_path`**
  (the latter `null` unless `--export-ollama` was passed). Additive only —
  every existing field keeps its name and shape.

## [0.1.0] — 2026-07-30

Initial public release: everything below is the work recorded in this
repository's history up to this point. FiTuna is not published to PyPI yet —
install from source (`pip install -e .`).

Entries under **Fixed** that say "found on real hardware" were not caught by
the test suite. The suite mocks the subprocess layer by design (it must run
with no llama.cpp and no network), so those bugs surfaced only when the tool
was run against real llama.cpp binaries and real models. See
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for why that validation step is
separate from CI.

### Added

- **Two-stage measured search** (`fituna run`): quantize every candidate and
  measure its perplexity loss against the F16 baseline, drop the ones over
  the quality budget, then walk the survivors in *measured* quality order,
  benchmarking each at full offload and binary-searching the minimal `-ngl`
  for the first quant that meets the throughput target.
- **CLI** with `run`, `detect-hw`, `list-binaries` subcommands, human and
  `--json` output, and a distinct exit code per failure class (0 success,
  1 general error, 2 missing binary, 3 no feasible config). Exit code 2 is
  shared with argparse's own usage-error exit code — a required flag missing
  or an unrecognized flag also exits 2, distinguishable from a missing binary
  by whether stderr's first line starts with `usage:` (see
  `docs/ARCHITECTURE.md`'s exit-code table).
- **Hardware auto-detection** — NVIDIA (`nvidia-smi`), AMD (`rocm-smi`),
  Apple Silicon unified memory (`system_profiler`), plus `--gpu`/`--vram-mb`
  manual override.
- **llama.cpp binary discovery** (`--llama-bin-dir` or `PATH`) with
  capability and build-version introspection.
- **GGUF header parsing** via stdlib `struct` (layer count, file type), and
  HF-directory conversion through `convert_hf_to_gguf.py` when available.
- **`llama-quantize` wrapper** — idempotent, atomic (temp file + rename), with
  the model fingerprint folded into the output filename.
- **`llama-perplexity` wrapper** with a `--ppl-chunks` bound on how much of
  the corpus is evaluated (default 32).
- **`llama-bench` wrapper** with timeout handling and `-d/--n-depth`-based
  context emulation.
- **sqlite3 result cache** keyed by model fingerprint × hardware profile ×
  llama.cpp build version, driving `--resume`.
- **Report layer** — human-readable and JSON result rendering plus a
  ready-to-run `llama-cli` command line.
- **`fituna doctor`** — up-front environment self-diagnosis (Python version,
  required/advisory binaries, llama.cpp version, hardware detection, output
  directory writability, free disk space) as PASS/WARN/FAIL rows with a
  one-line remedy each, human and `--json`.
- **`fituna fetch-corpus`** — downloads a quality corpus from HuggingFace's
  public dataset-viewer REST API using stdlib `urllib` only (no `datasets`,
  no pyarrow/pandas). English (wikitext-2-raw) and Korean (Korean Wikipedia)
  presets, `--dataset/--config/--split` override, atomic writes, and a
  CC BY-SA attribution notice printed on success.
- **`--quality-corpus`** (with `--wikitext` kept as an alias) so the quality
  gate can be measured on text resembling the actual workload.
- **MCP server** (`fituna-mcp`) — newline-delimited JSON-RPC 2.0 over stdio,
  implemented against the protocol directly so the zero-dependency guarantee
  holds; exposes `fituna_detect_hardware` and `fituna_recommend`.
- **Per-module runnable self-checks** (`python -m fituna.<module>`), executed
  in CI alongside the test suite.
- **152 unit tests** over a mocked subprocess/network layer, and a
  3-OS × 2-Python (Ubuntu/macOS/Windows × 3.11/3.13) CI matrix.
- **Warning when `--model` is already a quantized GGUF** (double-quantization
  and a skewed baseline).
- **Documentation** — architecture, measured results (Runs 1–5 including
  run-to-run variance and a thermal-throttle outlier), use cases, a Korean
  reproduction guide for judges (`REVIEWERS.md`), AI-assisted-development
  disclosure, open-source usage spec, license-compliance record, SBOM,
  third-party notices, SPDX headers on every Python file, and `REUSE.toml`.
- **Colab notebook** for one-click NVIDIA/Linux reproduction on the free
  T4 tier.
- **Community files** — `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `REVIEWERS.md`, issue and pull-request templates.

### Fixed

- **A single `llama-bench` timeout aborted the whole search.** Found on real
  hardware: the minimal-`ngl` binary search benches `ngl=0`, which a 4B model
  cannot finish CPU-only inside the 300 s timeout, and the resulting error
  killed a search after 20+ minutes of completed work. A config too slow to
  finish one bench *is* the answer for that config, so the timeout is now
  caught, recorded as a 0 tok/s below-target result, and cached so `--resume`
  never pays it twice.
- **llama.cpp version detection silently failed on current builds.** Found on
  real hardware: `llama-bench` rejects `--version` and prints no build banner,
  so detection always returned `None` and the version-keyed cache hashed
  every result under `"unknown"` — defeating the guarantee that `--resume`
  never serves numbers measured under a different backend build.
  `llama-perplexity` is now probed as well, and the bare `llama.cpp <build>`
  banner form is accepted.
- **The quality cache was not keyed by corpus.** Found on real hardware while
  setting up the English-vs-Korean comparison: perplexity is a property of
  (model, quant, corpus), but the key was (model, quant, chunk count), so
  switching `--quality-corpus` under `--resume` served the previous corpus's
  measurements as the new corpus's results. The corpus fingerprint joined the
  key; pre-upgrade cache files have their quality table dropped and remeasured
  rather than migrated.
- **`llama-bench` has no `-c/--ctx-size` flag.** Found on real hardware: the
  assumed argument is a hard parse error on current builds. Context is now
  mapped to `-d/--n-depth` so the timed generation phase runs with the KV
  cache filled to approximately the requested context.
- **Perplexity evaluation ran over the entire test set.** `llama-perplexity`
  was invoked with no chunk limit, making a four-candidate search take 3 h 44 m
  on real hardware. `--ppl-chunks` (default 32) brings the same search to
  roughly 12 minutes.
- **`--resume` could serve a perplexity result computed at a different chunk
  count** — `ppl_chunks` joined the quality cache key.
- **Two FiTuna processes sharing an `--out` directory could write the same
  quantize temp file.** A PID suffix was added, and temp-file cleanup widened
  to a glob so stale files from earlier crashed runs are swept.
- **Two different models could collide on one quantize output path** (every
  HF-directory input converts to the same conventional base filename). The
  model fingerprint is now part of the output filename.
- **A crashed `llama-quantize` could leave a truncated file that looked
  cached.** Quantization writes to a temp path and renames atomically.
- **A present-but-unexecutable `llama-quantize`/`llama-perplexity` binary
  (e.g. wrong permissions) crashed with a raw `PermissionError` traceback**
  instead of the same `FiTunaError` reporting a missing binary gets.
  `quantize.py`/`quality.py` now catch `OSError` generally, not just
  `FileNotFoundError`, and distinguish "it's there but broken" from "go
  install it" in the message.
- **A corrupt or non-sqlite file at the cache path** raised a raw
  `sqlite3.DatabaseError` traceback; it now becomes a `FiTunaError` with
  concrete recovery guidance. A malformed `--ctx` value was fixed the same
  way.
- **A best-effort fallback could report `ngl=n_layers` for a CPU-only bench.**
  The result is relabelled `ngl=0` before it is recorded.
- **Both Windows CI jobs failed on the first real Windows run** — a Windows
  path in a `pytest.raises` match pattern contains `\U`, an invalid regex
  escape. The pattern is now `re.escape`d.
- **`fituna doctor` could raise out of its own diagnostic loop.** Every check
  is individually guarded so a failure in one produces a FAIL row for itself
  rather than crashing the tool.

### Changed

- **Retracted the Run 5 corpus-reorder finding.** A published measurement —
  that the Korean corpus reorders the mid-table quants — did not survive
  re-checking: the two runs were nested rather than independent, and the
  Korean margin changes sign nine times across the per-chunk trace. The
  finding was withdrawn and both margins are now stated with their error
  bars. The verdict flips in Runs 3 and 4 are *not* retracted, but are
  qualified inline. See
  [docs/RESULTS.md](docs/RESULTS.md#how-big-is-a-perplexity-gap-the-error-bar-we-had-been-discarding).
- **Corrected a false model-license claim** in the AI-usage documentation and
  reconciled the open-source-usage documents with the repository as it
  actually is; corrected stale figures in the license-compliance record.
- `--wikitext` was renamed to `--quality-corpus`; the old name remains an
  alias, so this is not a breaking change.

[0.1.0]: https://github.com/leeyunseokarchive/fituna/releases/tag/v0.1.0
