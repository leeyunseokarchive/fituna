# FiTuna Architecture

## Summary

FiTuna is a Python 3.11 CLI that orchestrates llama.cpp binaries as
subprocesses to find the cheapest GGUF quantization + runtime config
(`quant`, `-ngl`, `-c`) that meets a user-specified throughput target
without exceeding a quality-loss budget. FiTuna performs no tensor math
itself — all inference/quantization/perplexity computation happens inside
the llama.cpp C++ binaries; FiTuna's job is orchestration, output parsing,
search, and caching. It has zero runtime Python dependencies (stdlib only).

## Module diagram

```
                              ┌───────────┐
                              │  cli.py   │  argparse entry point (run /
                              └─────┬─────┘  quickstart / detect-hw /
                                    │ list-binaries / doctor /
                                    │ fetch-corpus / help);
                                    │ builds TargetSpec, dispatches
        ┌───────────────┬──────────┼───────────┬──────────────────┐
        ▼                ▼          ▼           ▼                  ▼
  hardware.py      binaries.py  model_info.py  quantize.py    report.py
  detect GPU/      locate/      ensure base    llama-quantize  SearchResult
  CPU/RAM, or       introspect  GGUF, read      wrapper,       -> run cmd,
  parse manual      llama.cpp   ModelInfo       memoized on    JSON/human
  override          binaries    (n_layers etc)  disk (idempot.) report
        │                │          │                │              ▲
        │                │          │                │              │
        └────────┬───────┴────┬─────┴──────┬─────────┘              │
                  ▼            ▼            ▼                        │
           ┌─────────────────────────────────────┐                  │
           │              search.py               │  orchestrator   │
           │  quality-first filter (quality.py)   │──────────────────┘
           │  + ngl binary search (bench.py)      │
           │  + ctx grid-check (bench.py)         │
           └───────────┬───────────────┬──────────┘
                        ▼               ▼
                  bench.py         quality.py
                  llama-bench      llama-perplexity
                  wrapper          wrapper
                        │               │
                        └───────┬───────┘
                                ▼
                          cache.py (sqlite3)
                          memoizes BenchResult / QualityResult
                          keyed on (model_fp, hw_fp, candidate)

           fituna/config.py — frozen dataclasses/Enum/exceptions used by
           every module above (HardwareProfile, TargetSpec, BinaryPaths,
           ModelInfo, CandidateConfig, BenchResult, QualityResult,
           SearchResult, DoctorCheck, CorpusPreset, FiTunaError hierarchy).
           No module defines its own cross-module type; everyone imports
           from here.
```

Arrows show call direction, not import direction: `search.py` *calls*
`quantize.py` / `bench.py` / `quality.py` / `cache.py`; those modules never
call back into `search.py`. `cli.py` is the module that imports and calls the
widest set of the others; below it, a module depends only on `config.py`
(and, where noted, on `binaries.py`'s `BinaryPaths`). The two entry points
*above* `cli.py` — `quickstart.py` and `mcp_server.py` — also reach across
several modules each, but they reach through `cli.py` for anything that runs
a search, so there is still exactly one implementation of the search path.

`fituna/quickstart.py` sits *above* `cli.py` rather than beside it: the
`fituna quickstart` wizard is an `input()`-based shell that collects answers,
assembles a `fituna run ...` argv, prints it, then parses that same argv back
through `cli._build_parser()` and calls `cli._cmd_run()` in-process. It
orchestrates existing modules only — `doctor.run_checks()` for step 1,
`hardware.detect_hardware()` for the memory-fit arithmetic,
`corpus.fetch_corpus()` for step 5, `report.human_size()` for every file size
— and duplicates none of their logic. Every *search parameter* it assembles
maps to a public `run` flag: the self-check
(`python -m fituna.quickstart --selfcheck`) asserts on the assembled argv, so
a wizard-only search knob would fail it. That check covers the run-argv
surface only — the wizard's own conveniences (curated-model download,
HuggingFace search, corpus fetch) have no `run` equivalent and are outside
what it asserts. It downloads models with stdlib
`urllib` using the same temp-file + `os.replace` atomic pattern as
`corpus.py`, and reads the HuggingFace `/api/models` search endpoint whose
response shape is documented (and was verified live) in that module's
docstring.

`fituna/mcp_server.py` is a second, thinner entry point alongside `cli.py`:
a stdlib-only MCP stdio server (newline-delimited JSON-RPC 2.0, no SDK
dependency — the same zero-runtime-dependency guarantee `cli.py` gets from
the stdlib) exposing two tools, `fituna_detect_hardware` and
`fituna_recommend`, so an AI agent can ask for a measured config
recommendation the same way `cli.py run` produces one. It calls
`binaries.py` / `hardware.py` / `model_info.py` / `search.py` / `report.py`
/ `cache.py` directly rather than shelling out to `cli.py`, and always runs
with an active `cache.ResultCache` so a repeat question about the same
model/hardware answers in about a second.

## Runtime data flow (one `fituna run`)

1. `cli.py` parses argv into CLI args, then assembles a `TargetSpec`
   (`--model`, `--target-tps`, `--max-quality-loss`, `--ctx` →
   `ctx_candidates` with the first value as `.ctx`, `--quant` →
   `quant_candidates` re-sorted to quality-descending order).
2. `hardware.detect_hardware()` runs `nvidia-smi` / `rocm-smi` /
   `system_profiler` / `platform` as available; `--gpu`/`--vram-mb` (if
   given) are merged in via `parse_manual_hardware()`, user values winning.
   Produces a `HardwareProfile`.
3. `binaries.locate_binaries(bin_dir=...)` resolves `llama-quantize`,
   `llama-bench`, `llama-perplexity` (and optionally `llama-imatrix`,
   `convert_hf_to_gguf.py`) on `PATH` or under `--llama-bin-dir`, raising
   `BinaryNotFoundError` with an install-guide message if any required one
   is missing. `list_supported_quant_types()` parses `llama-quantize --help`
   to filter `TargetSpec.quant_candidates` down to what the installed build
   actually supports.
4. `model_info.ensure_base_gguf()` converts an HF directory to
   `work_dir/base-f16.gguf` via `binaries.convert_script` if `model_path`
   isn't already a `.gguf` (raises `ModelConversionError` on failure), then
   `read_model_info()` reads architecture/layer count/param count into a
   `ModelInfo`. `n_layers` is the upper bound for the `-ngl` search.
5. `search.search()` is the orchestrator (see algorithm below). It calls
   `quantize.quantize()`, `bench.run_bench()`, and `quality.evaluate_quality()`
   through `binaries.BinaryPaths`, memoizing every bench/quality call
   through `cache.ResultCache` when `--resume` is passed. It returns a
   `SearchResult` — either a real solution (`meets_target=True`) or a
   best-effort one, or raises `NoFeasibleConfigError` if nothing came close.
6. `report.py` turns the `SearchResult` into the three ways to consume the
   GGUF the search already produced: `build_server_command()` (a
   `llama-server` invocation, the OpenAI-compatible local API),
   `export_ollama_modelfile()` (an Ollama `Modelfile` written atomically
   next to the `.gguf` when `--export-ollama` is passed) and
   `build_run_command()` (the `llama-cli` invocation, kept as the
   interactive check). `to_human()` leads with the artifact path and size,
   then lists those three in that order; `to_json()` adds
   `llama_server_command` / `modelfile_path` beside the existing fields.
   `cli.py` prints one or the other to stdout per `--json`. Both
   `llama-cli` and `llama-server` are *located, never executed*.

## Search algorithm flow (inside `search.search()`)

Two-stage grid search bounded to `O(quant × log(n_layers))` bench calls.
Key insight: perplexity depends only on `quant`, never on `ngl`/`ctx`, so
quality and speed are decoupled — quality is computed once per quant,
never re-measured while probing speed.

```
Stage 1 — quality prefilter (one llama-perplexity call per quant)
  baseline_ppl = compute_perplexity(base F16 GGUF)      [cached, computed once]
  for quant in quant_candidates ∩ list_supported_quant_types():
      gguf = quantize(base_gguf, quant)
      q = evaluate_quality(quant, gguf, baseline_ppl, wikitext_path)
      keep quant if q.quality_loss_pct <= max_quality_loss_pct
  quality_filtered = kept quants, in original quality-descending order
                      (Q8_0 → Q2_K), i.e. best quality first

Stage 2 — per quant, speed search (best quality first; first hit wins)
  for quant in quality_filtered:
      gguf = quantize(base_gguf, quant)                  # idempotent, reused from Stage 1
      top  = run_bench(gguf, ngl=n_layers, ctx=target.ctx)
      if top.gen_tok_per_sec < target_tps:
          continue                        # early-exit B: skip to next (lower-quality) quant
      if hw.gpu_vendor == NONE:
          return result(quant, ngl=0, top)                # CPU-only hardware, no ngl search
      low = run_bench(gguf, ngl=0, ctx=target.ctx)
      if low.gen_tok_per_sec >= target_tps:
          return result(quant, ngl=0, low)                 # early-exit C: GPU not even needed
      # binary search minimal ngl in [0, n_layers] satisfying target_tps
      # (assumes gen_tok_per_sec is non-decreasing in ngl; worst case falls
      # back to `top`, which is already known to satisfy the target)
      lo, hi, best, calls = 0, n_layers, top, 0
      while lo < hi and calls < target.ngl_max_calls:
          mid = (lo + hi) // 2
          r = run_bench(gguf, ngl=mid, ctx=target.ctx); calls += 1
          if r.gen_tok_per_sec >= target_tps: best, hi = r, mid
          else:                                lo = mid + 1
      # re-verify best.ngl against any remaining ctx_candidates
      return result(quant, ngl=best.candidate.ngl, best)    # first quant to reach here wins
  raise NoFeasibleConfigError(closest=fastest attempt seen)  # all quants failed early-exit B
```

Early-exit summary: **A** — quants failing the quality gate never reach a
speed benchmark. **B** — a quant that misses the target even at full GPU
offload is abandoned immediately (its lower-quality, usually-faster
neighbor is tried next). **C** — a quant that hits the target at `ngl=0`
skips the binary search entirely (minimal-resource config). Because quants
are tried in quality-descending order and the loop returns on the first
success, FiTuna always reports the *best-quality* feasible config, never a
lower-quality one that happened to be probed later. If `max_bench_seconds`
elapses mid-search, the best result found so far is returned with
`meets_target=False` instead of raising.

Upper bound on `llama-bench` calls: `N_quant_survived × (2 + ngl_max_calls +
len(ctx_candidates))` — worst case 54 with the `TargetSpec` defaults in
`fituna/config.py` (6 quants, `ngl_max_calls=6`, a single ctx candidate:
6 × (2 + 6 + 1)); early exits typically end the search in well under 10.

## Filesystem artifacts

Every side effect happens under `--out` (`work_dir`) or via the llama.cpp
binaries themselves; every other function is a pure transform over
`config.py` dataclasses.

```
<work_dir>/
├── base-f16.gguf            # model_info.ensure_base_gguf() — only if input was an HF dir
├── <model>-<fp12>-<quant>.gguf  # quantize.quantize() — one per quant tried, idempotent (reused if present)
├── Modelfile                # report.export_ollama_modelfile() — only with --export-ollama; atomic (Modelfile.tmp + os.replace)
└── .fituna_cache.sqlite3    # cache.ResultCache — bench_cache / quality_cache tables, only with --resume
```

`quantize()` and `ensure_base_gguf()` skip regenerating a file that already
exists at its target path, so re-running `fituna run` against the same
`--out` is cheap even without `--resume`. `model_info.model_fingerprint()`
(a cheap `sha256(name:size:mtime)`, not a full-file hash) is the cache key
component that identifies "this model," combined with a hardware
fingerprint, so cache entries never leak across a different model or a
different machine. The first 12 hex chars of that same fingerprint are also
folded into the quantized `.gguf` filename itself (`<model>-<fp12>-<quant>.gguf`)
— without it, two different models that both convert to the same
conventional base filename (every HF-directory input becomes
`base-f16.gguf`) would collide on the exact same output path in the same
`--out` dir, silently serving one model's quantized file as a "cache hit"
for a completely different model.

## Error handling & exit codes

`cli.py` maps the `FiTunaError` hierarchy (defined once in `config.py`,
re-exported from `errors.py`) to process exit codes:

| Exit code | Condition |
|---|---|
| 0 | success — `search()` returned a `SearchResult` with `meets_target=True` |
| 1 | generic error — any other `FiTunaError`, or `meets_target=False` (best-effort result, no config met the target) |
| 2 | `BinaryNotFoundError` — a required llama.cpp binary is missing; message includes an install pointer. **Also** argparse's own usage-error exit code — a missing required flag or an unrecognized flag exits 2 before `main()`'s `FiTunaError` mapping ever runs, since `parser.parse_args()` calls `sys.exit(2)` itself. Distinguish the two by stderr's first line: argparse's starts with `usage: ...`; `BinaryNotFoundError`'s is a `... ERROR fituna: ...` log line |
| 3 | `NoFeasibleConfigError` — every quant candidate failed the quality gate or the full-offload speed check; `.closest` carries the nearest attempt for diagnostics |

`ModelConversionError` (HF→GGUF conversion subprocess failure) and a
`FiTunaError` raised from a `llama-bench`/`llama-perplexity` timeout both
fall through to exit code 1.

`fituna doctor` does not go through this exception mapping at all —
`_cmd_doctor` computes its exit code directly from the check results via
`doctor.exit_code()`, bypassing `main()`'s `FiTunaError` handling entirely
(there is nothing for it to catch). It reuses the same 0/1/2 values for a
related but distinct condition: 0 if every check is PASS or WARN, 2 if any
of the three required llama.cpp binaries FAILed (deliberately mirroring the
`BinaryNotFoundError` → 2 convention above), 1 for any other FAIL. There is
no doctor equivalent of exit code 3 — `NoFeasibleConfigError` is a
`run`-only condition doctor never produces.

## Why this shape

- **Single source of truth for types** (`fituna/config.py`): every
  cross-module value is a `frozen` dataclass or `Enum` defined once, so
  parallel implementation of modules can't drift on the interface.
- **Pure functions, explicit side effects**: only `quantize.py` (writes a
  `.gguf`), `model_info.py` (writes a converted base `.gguf`),
  `cache.py` (writes to sqlite3), `corpus.py` (writes the downloaded
  corpus), `report.py` (writes the Ollama `Modelfile` for `--export-ollama`)
  and `quickstart.py` (writes downloaded `.gguf` files) touch the
  filesystem; everything else returns values. The three that download do it
  through the same temp-file + `os.replace` pattern, so an interrupted run
  leaves no partial file.
- **subprocess isolation**: every llama.cpp interaction goes through exactly
  one wrapper function per binary (`quantize()`, `run_bench()`,
  `compute_perplexity()`), so parsing logic for that binary's output lives
  in exactly one place.
- **Quality/speed decoupling**: because perplexity is independent of
  `ngl`/`ctx`, `search.py` computes it once per quant instead of once per
  candidate configuration, cutting benchmark calls from
  `O(quant × ngl × ctx)` down to `O(quant × log(n_layers))`.
- **Cache as an optimization, not a dependency**: every module that calls
  `cache.py` degrades gracefully to "just run the subprocess" when
  `cache is None` (`--resume` not passed) — the cache is never required for
  correctness, only for avoiding redundant subprocess calls across runs.
