# FiTuna Architecture

## Summary

FiTuna is a Python 3.11 CLI that orchestrates llama.cpp binaries as
subprocesses to find the cheapest GGUF quantization + runtime config
(`quant`, `-ngl`, `-c`) that meets a user-specified throughput target
without exceeding a quality-loss budget. FiTuna performs no tensor math
itself — all inference/quantization/perplexity computation happens inside
the llama.cpp C++ binaries; FiTuna's job is orchestration, output parsing,
search, and caching.

## Module diagram

```
                        ┌───────────┐
                        │  cli.py   │  argparse entry point
                        └─────┬─────┘
                              │
        ┌─────────────┬──────┼───────┬──────────────┐
        ▼             ▼      ▼       ▼              ▼
  hardware.py   binaries.py  model_info.py     (config.py)
  detect GPU/   locate/       ensure base       shared types
  CPU/RAM       introspect    GGUF, read        used by every
                llama.cpp     model metadata    module below
                binaries
        │             │             │
        └──────┬──────┴──────┬──────┘
               ▼              ▼
          quantize.py     cache.py (sqlite3)
          llama-quantize  bench/quality memo
               │              ▲
               ▼              │
          bench.py ───────────┤
          llama-bench         │
               │              │
               ▼              │
          quality.py ─────────┘
          llama-perplexity
               │
               ▼
          search.py   (quality-first filter + grid search + ngl binary search)
               │
               ▼
          report.py   (run command + JSON/human report)
```

## Data flow (one `fituna run`)

1. `cli.py` parses argv into a `TargetSpec` (+ CLI overrides for hardware /
   binary dir / cache).
2. `hardware.detect_hardware()` / `parse_manual_hardware()` produce a
   `HardwareProfile`.
3. `binaries.locate_binaries()` resolves the required llama.cpp executables
   into a `BinaryPaths`, raising `BinaryNotFoundError` early if missing.
4. `model_info.ensure_base_gguf()` converts an HF directory to GGUF if
   needed, then `read_model_info()` returns a `ModelInfo` (layer count is
   the upper bound for `-ngl` search).
5. `search.search()` is the orchestrator: for each quant candidate
   (quality-descending order), it quantizes, checks quality loss against
   the base GGUF's perplexity (via `quality.py`), then binary-searches
   `-ngl` and grid-searches `ctx_candidates` via `bench.py`, short-circuiting
   on the first candidate that meets both constraints. All bench/quality
   calls are memoized through `cache.ResultCache` when `--resume` is passed.
6. `report.py` turns the winning (or best-effort) `SearchResult` into a
   ready-to-run `llama-cli` command and a JSON/human report.

## Why this shape

- **Single source of truth for types** (`fituna/config.py`): every
  cross-module value is a `frozen` dataclass or `Enum` defined once, so
  parallel implementation of modules can't drift on the interface.
- **Pure functions, explicit side effects**: only `quantize.py` (writes a
  `.gguf`), `model_info.py` (writes a converted base `.gguf`), and
  `cache.py` (writes to sqlite3) touch the filesystem; everything else
  returns values.
- **subprocess isolation**: every llama.cpp interaction goes through exactly
  one wrapper function per binary (`quantize()`, `run_bench()`,
  `compute_perplexity()`), so parsing logic for that binary's output lives
  in exactly one place.
