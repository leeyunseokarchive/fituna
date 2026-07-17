# FiTuna

FiTuna finds the smallest llama.cpp GGUF quantization + runtime config
(`quant`, `-ngl`, `-c`) that meets a target generation throughput without
exceeding a quality-loss budget — automatically, for your actual hardware.

FiTuna does not do any inference or quantization math itself. All heavy
lifting happens inside [llama.cpp](https://github.com/ggml-org/llama.cpp)
binaries (`llama-quantize`, `llama-bench`, `llama-perplexity`), which FiTuna
runs as subprocesses and whose output it parses. FiTuna itself is a thin,
dependency-free Python orchestrator: hardware detection + a quality-first
search over quant/ngl/ctx candidates + result caching.

See `docs/ARCHITECTURE.md` for the module diagram and data flow.

## Status

Implemented and integration-tested end-to-end against **real** llama.cpp
binaries (Homebrew build) and a real model (Qwen2.5-3B-Instruct GGUF),
covering the success path, `--resume` cache hits, `BinaryNotFoundError`
(exit 2), and `NoFeasibleConfigError` best-effort reporting (exit 3), on top
of module self-checks + `pytest` (74 tests) against stand-in binaries. **All
real-hardware validation so far is on macOS (Apple Silicon)** — Linux/Windows
code paths (see "Known limitations" below) are code-reviewed but not
integration-tested on those platforms. The public interfaces in
`fituna/config.py` and the function signatures across `fituna/*.py` are the
fixed cross-module contract.

## Requirements

- Python 3.11+
- A working [llama.cpp](https://github.com/ggml-org/llama.cpp) build on your
  `PATH` (or point FiTuna at it with `--llama-bin-dir`), providing at least
  `llama-quantize`, `llama-bench`, and `llama-perplexity`.
- A perplexity evaluation corpus as plain text. The
  [wikitext-2-raw-v1](https://huggingface.co/datasets/Salesforce/wikitext)
  dataset (CC-BY-SA) on HuggingFace is distributed as Parquet, not a `.txt`
  file `llama-perplexity -f` can read directly — export the test split with:

  ```bash
  pip install datasets  # one-time, only needed to fetch this corpus
  python -c "
  from datasets import load_dataset
  ds = load_dataset('Salesforce/wikitext', 'wikitext-2-raw-v1', split='test')
  open('wikitext-2-raw-test.txt', 'w').write('\n'.join(ds['text']))
  "
  ```

  then pass `--wikitext wikitext-2-raw-test.txt`.

FiTuna itself has **zero runtime Python dependencies** — everything it needs
is in the standard library. See `docs/SBOM.md`.

## Install

```bash
pip install -e .
# or, for development:
pip install -e ".[dev]"
```

## Usage

Auto-detect hardware:

```bash
fituna detect-hw
```

Search for a config meeting a throughput + quality target:

```bash
fituna run --model ./models/Llama-3-8B-Instruct --target-tps 20 --max-quality-loss 3 \
  --ctx 4096 --wikitext ./data/wikitext-2-raw --out ./out
```

Pin GPU hardware manually, restrict quant candidates, try multiple context
lengths, and emit machine-readable JSON:

```bash
fituna run --model ./models/qwen2.5-7b.gguf --gpu nvidia --vram-mb 12000 \
  --target-tps 35 --max-quality-loss 5 \
  --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M,Q3_K_M --ctx 8192,4096 \
  --wikitext ./data/wikitext-2-raw --json > result.json
```

CPU-only run against a non-default llama.cpp build dir, resuming from cache:

```bash
fituna run --model ./models/phi-3-mini --gpu none --target-tps 8 --max-quality-loss 2 \
  --llama-bin-dir /opt/llama.cpp/build/bin --wikitext ./data/wikitext-2-raw --resume
```

Inspect which llama.cpp binaries FiTuna resolved:

```bash
fituna list-binaries --llama-bin-dir /usr/local/bin
```

## How the search works

1. Try `quant_candidates` in quality-descending order (default `Q8_0` →
   `Q2_K`). For each: quantize (idempotent, skipped if the file already
   exists), then check perplexity loss vs. the unquantized baseline against
   `--max-quality-loss`.
2. Within a quant tier that passes the quality gate, grid-search
   `ctx_candidates` and binary-search `-ngl` (bounded by `ngl_max_calls`
   bench calls) for the smallest `-ngl` meeting `--target-tps`.
3. Stop at the first candidate that satisfies both constraints (best
   quality wins ties). If nothing satisfies both, return the closest
   best-effort result.
4. Bench/quality results are cached in `<out>/.fituna_cache.sqlite3`;
   `--resume` reuses them instead of re-running llama.cpp.

## Known limitations

- **Single GPU only.** Hardware detection reads only the first GPU reported
  by `nvidia-smi`/`rocm-smi`, and bench invocations don't set
  `--tensor-split`/`--main-gpu`. Multi-GPU tensor-split support is on the
  roadmap, not implemented.
- **Windows AMD GPU auto-detection is a known gap.** `rocm-smi` has no
  mainstream Windows distribution, so an AMD GPU on Windows is likely to be
  mis-detected as CPU-only. Use `--gpu amd --vram-mb <N>` to override.
- **Windows RAM auto-detection is code-reviewed, not integration-tested** —
  no Windows CI job exists yet to exercise the `ctypes`/`GlobalMemoryStatusEx`
  path against a real Windows process.
- **`ngl_max_calls` (default 6)** bounds the `-ngl` binary search; for models
  much deeper than the range it was tuned against, the search can fall back
  to the safe-but-suboptimal full-offload candidate before converging on the
  true minimal `-ngl`. Not an accuracy bug (the reported config still meets
  the target), just a possibly-conservative one.
- `llama-bench`/`llama-perplexity` failures (e.g. out-of-memory) surface
  llama.cpp's own stderr as-is; FiTuna doesn't yet pattern-match common
  failure causes into an actionable suggestion.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see `LICENSE`. Third-party notices for subprocess-invoked tools
(llama.cpp, etc.) are in `THIRD_PARTY_NOTICES.md`.
