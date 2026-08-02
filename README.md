<div align="center">

**English** | [한국어](README.ko.md)

# 🎯 FiTuna

**Hardware-benchmark-driven auto-tuning for local LLMs.** Give it a model, a
target speed and a quality budget; get back the smallest llama.cpp config that
actually hits those numbers on **your** machine.

**API subscriptions add up. Going local means guessing which model your
machine can actually run.** Don't guess — measure it, and run your own.

[![CI](https://github.com/leeyunseokarchive/fituna/actions/workflows/ci.yml/badge.svg)](https://github.com/leeyunseokarchive/fituna/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Zero dependencies](https://img.shields.io/badge/runtime%20deps-0-brightgreen.svg)](docs/SBOM.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**심사위원 · 검증기관용 한국어 재현 가이드 → [REVIEWERS.md](REVIEWERS.md)** *(Korean reproduction guide for competition judges & verification agency)*

</div>

---

```bash
$ fituna run --model Qwen3-4B-Instruct-2507-F16.gguf \
    --target-tps 30 --max-quality-loss 5 --ctx 4096 --wikitext wiki.txt --out ./out

[Q6_K]   full-offload 28.48 tok/s < target 30.00, skipping (early-exit B)
[Q8_0]   full-offload 24.22 tok/s < target 30.00, skipping (early-exit B)
[Q5_K_M] full-offload 29.59 tok/s < target 30.00, skipping (early-exit B)
[Q4_K_M] found ngl=33 meeting target -- done

FiTuna result: MEETS TARGET
  quant : Q4_K_M   ngl : 33   ctx : 4096
  gen tok/s : 30.81      quality loss : 1.73%

  artifact: out/Qwen3-4B-Instruct-2507-...-Q4_K_M.gguf  (2.3 GB -- already produced during the search)

  1) local API server (OpenAI-compatible):
       llama-server -m out/Qwen3-...-Q4_K_M.gguf -ngl 33 -c 4096 --port 8080
  2) import into Ollama: re-run with --export-ollama to write a Modelfile beside the artifact
  3) terminal chat (interactive check):
       llama-cli -m out/Qwen3-...-Q4_K_M.gguf -ngl 33 -c 4096
```

*(Output formatting above is reconstructed against the current version; the
numbers are the Run 2 measurements.)*

A real run on an Apple M3 Pro. The "obviously best" Q8_0 **failed** the speed
target, Q5_K_M missed by **0.41 tok/s**, and the answer wasn't a quant alone —
it was a quant *plus* the minimal GPU offload (`-ngl 33`, not the full 36).
None of that is predictable from a spec sheet ([full logs](docs/RESULTS.md)).

## Install

Not on PyPI yet — install from git, into a virtualenv built with Python 3.11+
(macOS's system `python3` is 3.9):

```bash
git clone https://github.com/leeyunseokarchive/fituna
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e fituna
```

You also need llama.cpp, which provides the quantize/bench/perplexity engines
FiTuna orchestrates:

```bash
brew install llama.cpp        # macOS/Linux Homebrew — ships all needed binaries
# or build from source (any platform):
git clone https://github.com/ggml-org/llama.cpp
cmake -S llama.cpp -B llama.cpp/build && cmake --build llama.cpp/build --config Release
```

## Quickstart

Three ways in: a person runs the wizard; a script or CI job calls
`fituna run --json`; an AI agent talks to
[`fituna-mcp`](#mcp-server--measured-answers-for-ai-agents).

```bash
fituna quickstart
```

Six steps — environment check, targets, license requirements, model, quality
corpus, search — and it prints the assembled `fituna run ...` command
**before** executing it, so the next run is a one-liner you already have. It
needs a terminal; in CI or a pipe use `fituna run` directly, since every
search parameter maps to a public `run` flag (proven by an argv-equality
test). Model download (a curated shortlist) and HuggingFace search are
wizard-only conveniences; `run --model` expects a `.gguf` on disk.

It never predicts throughput: memory fit is arithmetic (published file size vs
detected VRAM/RAM, assumed margin stated), speed is measured, and curated or
HuggingFace-search candidates show their license — local-scan and manual-path
options cannot, since a `.gguf` carries no license metadata. Any
[`docs/RESULTS.md`](docs/RESULTS.md) figure it cites is a record of what was
measured on named hardware, never a prediction.

### The script path (what the wizard assembles for you)

Quality loss is perplexity increase over a plain-text corpus, so it is only
meaningful on text resembling your workload. Any UTF-8 file works
(`--quality-corpus`); both presets are one command away:

```bash
fituna fetch-corpus --lang en --out wikitext-2-raw-test.txt        # wikitext-2 test split
fituna fetch-corpus --lang ko --out kowiki-corpus.txt --rows 500   # Korean Wikipedia
```

Measure the language you'll run: the same quant can measure 2–3× different
loss on the two corpora, and in Run 3 that was enough to change the verdict
the tool returned ([measurement and
caveats](docs/RESULTS.md#run-3--english-vs-korean-quality-corpus-same-model-same-quants)).
Both presets are CC BY-SA 3.0 and `fetch-corpus` prints the attribution notice
when it finishes; `--dataset/--config/--split` override the preset
([provenance and licensing](docs/OPEN_SOURCE_USAGE.md)).

```bash
fituna doctor                             # confirm the environment is ready
fituna detect-hw                          # see what FiTuna detects
fituna run --model your-model-F16.gguf \
  --target-tps 30 --max-quality-loss 5 \
  --ctx 4096 --wikitext wikitext-2-raw-test.txt --out ./out --resume
```

Pass an F16/BF16 `.gguf` directly (many models publish one), or an HF-format
directory if `convert_hf_to_gguf.py` is available (source checkout +
`pip install torch transformers`; package-manager builds don't ship it).

> **Disk usage:** the search quantizes every candidate reaching the quality
> stage — ~12 GB for four candidates of a 4B model. Files are reused across
> runs; narrow `--quant` to bound this.

## Why

Running a local LLM means picking a quantization level (Q2–Q8), a GPU offload
layer count (`-ngl`) and a context length — a search space people navigate
today by trial and error:

- **Ollama / LM Studio** apply fixed per-model presets; a request for finer
  quantization control was [closed as not planned](https://github.com/ollama/ollama/issues/14674).
- **NVIDIA Model Optimizer**'s AutoQuantize is CUDA-only.
- **VRAM calculators & chatbot advice** estimate from specs — and specs don't
  know your thermals, memory bandwidth, or llama.cpp build flags.

FiTuna replaces the guesswork with a measured search over the llama.cpp
binaries you already have — verified on your hardware, reproducible from cache.

## Features

- 🔍 **Target-driven search** — in: model + target tok/s + max quality loss %.
  Out: quant × `-ngl` × ctx config + a ready-to-run command.
- 📏 **Measured, not assumed** — candidates walked in *measured* perplexity
  order (in our runs Q6_K beat Q8_0 — [data](docs/RESULTS.md)), with a binary
  search for the minimal GPU offload.
- ⚡ **Aggressive early exits** — quality-gate failures and hopeless quants are
  skipped without wasting benches; a bench that can't finish in time counts as
  "too slow", not a crash.
- 🗃️ **Reproducible cache** — sqlite3, keyed by model fingerprint × hardware ×
  llama.cpp build version; `--resume` re-answers in <1s and survives
  interruptions.
- 🖥️ **Hardware auto-detection** — NVIDIA (`nvidia-smi`), AMD (`rocm-smi`),
  Apple Silicon unified memory (`system_profiler`), with manual override.
- 🪶 **Zero runtime dependencies** — pure Python 3.11+ stdlib.

## Measured results

| Model | Target | What the "obvious" pick did | What FiTuna found |
|---|---|---|---|
| Qwen3-4B-Instruct (Apache 2.0) | 30 tok/s, ≤5% loss | Q8_0: 24.22 tok/s ❌ (and measured *worse* quality than Q6_K) | **Q4_K_M @ ngl=33 → 30.81 tok/s, 1.73% loss** ✅ |
| SmolLM2-135M (Apache 2.0) | 240 tok/s, ≤5% loss | Q8_0: 205.91 tok/s ❌ | **Q6_K → 249.50 tok/s, 0.53% loss** ✅ (and Q4_K_M measured *slower* than Q6_K) |
| Midm-2.0-Mini-Instruct, Korean (MIT) | 40 tok/s, ≤5% loss | Q8_0: 34.26 tok/s ❌ | **Q4_K_M @ ngl=48 → 44.62 tok/s, 2.58% loss** ✅ (the two corpora report different mid-table orders, but the per-chunk trace shows that reorder is [not something we could establish](docs/RESULTS.md#how-big-is-a-perplexity-gap-the-error-bar-we-had-been-discarding)) |

Apple M3 Pro, llama.cpp build 9960. Full logs, timings and run-to-run variance
analysis (including a thermal-throttle outlier we caught and documented):
**[docs/RESULTS.md](docs/RESULTS.md)** · Scenarios:
[docs/USE_CASES.md](docs/USE_CASES.md) · Reproduce on NVIDIA/Linux with the
one-click Colab notebook (free T4 tier):
[notebooks/colab_nvidia_verification.ipynb](notebooks/colab_nvidia_verification.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leeyunseokarchive/fituna/blob/main/notebooks/colab_nvidia_verification.ipynb)

## How it works

**Stage 1** measures perplexity loss for *every* candidate, because **Stage 2**
walks them in *measured* quality order and you can't sort by a number you
haven't measured. Stage 2 early-exits hard: a quant missing the target at full
offload is dropped without further benches, and the first quant that passes
wins. Results cache to sqlite3 keyed by model fingerprint, hardware profile
**and llama.cpp build version**, so `--resume` never serves numbers from a
different backend build. Diagrams, module map and full algorithm:
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · Contract:
[`fituna/config.py`](fituna/config.py)

## Use as a library

Zero runtime dependencies means the modules import directly:

```python
from fituna.hardware import detect_hardware

hw = detect_hardware()
print(f"{hw.gpu_vendor.value}: {hw.gpu_name}, {hw.vram_mb} MB VRAM, {hw.ram_mb} MB RAM")
# apple: Apple M3 Pro, 18432 MB VRAM, 18432 MB RAM
```

(Real output from a `python3.13 -c` run on the same M3 Pro as above.) Driving
the search programmatically means calling `fituna.search.search()`, which also
needs a `ModelInfo`, resolved `BinaryPaths`, a work directory and a corpus
path — exactly what `fituna run`/`quickstart` assemble for you
([`search.py`](fituna/search.py), [`config.py`](fituna/config.py)).

## MCP server — measured answers for AI agents

Ask a chatbot "which local model config fits my machine?" and it guesses from
specs. Point it at FiTuna's MCP server and it *measures*:

```bash
claude mcp add fituna -- fituna-mcp      # or any MCP client, stdio transport
```

| Tool | What it does |
|---|---|
| `fituna_detect_hardware` | GPU vendor/name, VRAM, CPU cores, RAM as FiTuna sees them |
| `fituna_recommend` | Runs the measured search for a target spec; returns the winning config, measured tok/s, measured quality loss, and a ready-to-run command. Slow once, ~1 s on repeat (cache). |

Stdlib-only like the rest of FiTuna — MCP stdio is newline-delimited JSON-RPC
2.0, no SDK required ([`fituna/mcp_server.py`](fituna/mcp_server.py)).

## Scope

FiTuna recommends; it doesn't execute or serve. The output is the quantized
`.gguf` plus `llama-server` / `llama-cli` commands you copy and run (and, with
`--export-ollama`, an Ollama `Modelfile` beside it) — FiTuna launches none of
them. That's a deliberate boundary: serving inference is llama.cpp's job, and
duplicating it would add no differentiated value
([rationale](docs/ARCHITECTURE.md#why-this-shape)). The two extensions that
stay inside it — `--launch` and an LM Studio preset export — are tracked in
[#19](https://github.com/leeyunseokarchive/fituna/issues/19).

## Known limitations

- **Single GPU only** — first GPU reported by `nvidia-smi`/`rocm-smi`; no
  `--tensor-split` ([#11](https://github.com/leeyunseokarchive/fituna/issues/11),
  help wanted: we have no multi-GPU machine to measure on).
- **Windows AMD auto-detection** — `rocm-smi` has no mainstream Windows
  distribution; use `--gpu amd --vram-mb <N>`.
- **Quality = perplexity on a corpus you choose** — a proxy, not a guarantee
  of domain quality. Gate on text resembling your workload
  (`--quality-corpus`; [measured EN-vs-KO
  comparison](docs/RESULTS.md#run-3--english-vs-korean-quality-corpus-same-model-same-quants)).
- **The quality verdict depends on `--ppl-chunks`** — loss is an estimate over
  `chunks × 512` tokens whose absolute value grows with the chunk count, so
  re-measure a candidate close to your budget before trusting the PASS
  ([measured effect](docs/RESULTS.md#how-big-is-a-perplexity-gap-the-error-bar-we-had-been-discarding)).
  `quality.py` still parses the PPL and discards llama-perplexity's error bar
  ([#8](https://github.com/leeyunseokarchive/fituna/issues/8)) — which is how
  Run 5 came to publish a claim it later had to withdraw.
- **Benchmarks are thermally sensitive** — verdicts within a few tok/s of the
  target are marginal ([variance
  analysis](docs/RESULTS.md#run-to-run-variance-measured-not-hidden)).
- **Real-hardware E2E covers macOS and Linux only** — Apple Silicon/Metal and
  NVIDIA T4/CUDA. Windows paths are unit-tested and CI-run, but not yet
  integration-run against real binaries
  ([#12](https://github.com/leeyunseokarchive/fituna/issues/12)).

## Contributing

Contributions welcome — the codebase is small, dependency-free and
contract-first (start at [`fituna/config.py`](fituna/config.py)); 246 unit
tests, per-module self-checks and a 3-OS × 2-Python CI matrix guard it.
Planned work sits in the
[v0.2.0 milestone](https://github.com/leeyunseokarchive/fituna/milestone/1),
including [#10](https://github.com/leeyunseokarchive/fituna/issues/10) (parser
test coverage, good first issue). See [CONTRIBUTING.md](CONTRIBUTING.md) ·
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) · [CHANGELOG.md](CHANGELOG.md) ·
[SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © FiTuna contributors. Third-party notices (llama.cpp and
subprocess-invoked tools): [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) ·
SBOM: [docs/SBOM.md](docs/SBOM.md) · Open-source usage:
[docs/OPEN_SOURCE_USAGE.md](docs/OPEN_SOURCE_USAGE.md) · AI-assisted
development disclosure: [docs/AI_MODEL_USAGE.md](docs/AI_MODEL_USAGE.md)
