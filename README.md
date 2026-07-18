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
binaries (Homebrew build) and a real model (Qwen3-4B-Instruct-2507, Apache
2.0), covering the success path, `--resume` cache hits, `BinaryNotFoundError`
(exit 2), and `NoFeasibleConfigError` best-effort reporting (exit 3), on top
of module self-checks + `pytest` (77 tests) against stand-in binaries — see
`docs/RESULTS.md` for the measured numbers. **All real-hardware validation so
far is on macOS (Apple Silicon)** — Linux/Windows code paths (see "Known
limitations" below) run unit tests + self-checks in CI
(`.github/workflows/ci.yml`, ubuntu/macos/windows matrix) but have not had a
real-binary integration run on those platforms. The public interfaces in
`fituna/config.py` and the function signatures across `fituna/*.py` are the
fixed cross-module contract.

## Requirements

- Python 3.11+
- A working [llama.cpp](https://github.com/ggml-org/llama.cpp) build on your
  `PATH` (or point FiTuna at it with `--llama-bin-dir`), providing at least
  `llama-quantize`, `llama-bench`, and `llama-perplexity`. Easiest routes:

  ```bash
  brew install llama.cpp        # macOS/Linux Homebrew — ships all three
  # or build from source (any platform):
  git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
  cmake -B build && cmake --build build --config Release
  # then: fituna ... --llama-bin-dir ./llama.cpp/build/bin
  ```

  Note: package-manager builds (Homebrew etc.) do **not** ship
  `convert_hf_to_gguf.py`, which FiTuna needs only when `--model` points at a
  HuggingFace-format *directory*. If you pass an F16/BF16 `.gguf` file
  directly (many models publish one), no convert script is needed; for HF-dir
  input, use a source checkout as `--llama-bin-dir` (the script sits at the
  repo root) and `pip install torch transformers` for the script itself.
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

Search for a config meeting a throughput + quality target (pass an F16/BF16
GGUF directly — or an HF-format directory if a convert script is available,
see Requirements):

```bash
fituna run --model ./models/Qwen3-4B-Instruct-2507-F16.gguf \
  --target-tps 20 --max-quality-loss 3 \
  --ctx 4096 --wikitext ./wikitext-2-raw-test.txt --out ./out
```

> **Disk usage:** the search quantizes *every* quant candidate that passes
> the quality gate stage before benchmarking (quality is measured for all
> candidates first, so the speed search can walk them in *measured* quality
> order). With the default 6 candidates and an 8B model, expect roughly
> 25–35 GB in `--out` on top of the base GGUF. Files are reused across runs
> (quantization is idempotent), and you can narrow `--quant` to bound this.

Pin GPU hardware manually, restrict quant candidates, try multiple context
lengths, and emit machine-readable JSON:

```bash
fituna run --model ./models/qwen3-8b-f16.gguf --gpu nvidia --vram-mb 12000 \
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

Two stages, with different cost profiles:

1. **Quality stage (paid for every candidate).** Each quant candidate is
   quantized (idempotent — skipped if the file exists) and its perplexity
   loss vs. the unquantized baseline is measured. Candidates over
   `--max-quality-loss` are dropped. This stage deliberately measures *all*
   candidates up front: the speed stage walks them in **measured** quality
   order, and you can't sort by a number you haven't measured. (Ordering by
   the conventional Q8_0 → Q2_K ranking instead would be a guess — and
   guesses are exactly what this tool exists to replace.)
2. **Speed stage (early-exits aggressively).** Walking survivors from
   highest measured quality down: bench at full offload (if even that misses
   the target, skip the quant entirely), then binary-search the minimal
   `-ngl` (bounded by `ngl_max_calls` bench calls) and re-verify extra
   `ctx_candidates`. The first quant that meets `--target-tps` wins —
   lower-quality quants are never benchmarked.
3. If nothing satisfies both constraints, FiTuna reports the closest
   best-effort config and exits 3.
4. Bench/quality results are cached in `<out>/.fituna_cache.sqlite3`, keyed
   by model fingerprint, hardware profile **and llama.cpp build version**;
   `--resume` reuses them instead of re-running llama.cpp.

## Why not just ask a chatbot / use presets?

| | FiTuna | Ollama / LM Studio presets | Chatbot advice / VRAM calculators |
|---|---|---|---|
| Picks quant for *your* hardware | measured on-device | coarse VRAM heuristic | guessed from specs |
| Target throughput (tok/s) input | yes — search constraint | no | no |
| Quality-loss budget input | yes — measured perplexity gate | no | no |
| Output verifiable | re-run = same numbers (cached) | n/a | not reproducible |

The gap is real: hardware variance (thermals, memory bandwidth, backend
build flags) makes spec-based guesses miss — in our own E2E run the
"obviously best" Q8_0 config missed the throughput target while a Q5_K_M
config beat it with 1% measured quality loss (`docs/RESULTS.md`).

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
