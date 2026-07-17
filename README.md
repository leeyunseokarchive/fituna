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

Early scaffold. The public interfaces (`fituna/config.py` and the function
signatures across `fituna/*.py`) are fixed; implementations are being filled
in. See inline `TODO`s.

## Requirements

- Python 3.11+
- A working [llama.cpp](https://github.com/ggml-org/llama.cpp) build on your
  `PATH` (or point FiTuna at it with `--llama-bin-dir`), providing at least
  `llama-quantize`, `llama-bench`, and `llama-perplexity`.
- A perplexity evaluation corpus, e.g.
  [wikitext-2-raw](https://huggingface.co/datasets/Salesforce/wikitext)
  (CC-BY-SA), downloaded locally.

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

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see `LICENSE`. Third-party notices for subprocess-invoked tools
(llama.cpp, etc.) are in `THIRD_PARTY_NOTICES.md`.
