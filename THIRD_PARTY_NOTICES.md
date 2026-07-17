# Third-Party Notices

FiTuna's own source code is licensed under the MIT License (see `LICENSE`).
FiTuna does **not vendor, bundle, or redistribute any third-party source
code or binaries**. Its runtime Python dependencies are **zero** — the
package uses only the Python 3.11 standard library (see `docs/SBOM.md` for
the full module list).

At run time, however, FiTuna **invokes external programs as subprocesses**
and may ask the user to supply external data files. This document lists
those external components, their licenses, and exactly how FiTuna touches
them, in line with the conditions of their respective licenses.

---

## 1. llama.cpp (required, invoked as a subprocess)

- **Project**: https://github.com/ggml-org/llama.cpp
- **License**: MIT License, Copyright (c) 2023-2026 The ggml authors
- **How FiTuna uses it**: FiTuna does not implement quantization, inference,
  or benchmarking itself. It shells out (via Python's `subprocess` module)
  to pre-built llama.cpp executables that the **user has already installed**
  and points FiTuna at via `PATH` or `--llama-bin-dir`
  (`fituna/binaries.py:locate_binaries`):
  - `llama-quantize` — produce a quantized GGUF from a base F16/F32 GGUF
    (`fituna/quantize.py`)
  - `llama-bench` — measure prompt/generation throughput
    (`fituna/bench.py`)
  - `llama-perplexity` — measure quality loss vs. a baseline
    (`fituna/quality.py`)
  - `llama-imatrix` (optional) and the HF→GGUF `convert_hf_to_gguf.py`
    script (optional) — model conversion (`fituna/model_info.py`)

  FiTuna only starts these as separate OS processes and parses their
  stdout/stderr/exit code. **No llama.cpp source file or compiled binary is
  copied into, packaged with, or distributed by this repository.** If the
  required binaries are not found, `locate_binaries()` raises
  `BinaryNotFoundError` with a message pointing the user to the upstream
  build instructions rather than silently failing.

### MIT License text (llama.cpp)

```
MIT License

Copyright (c) 2023-2026 The ggml authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Reproduced here in full to satisfy the MIT License's notice-preservation
condition, even though no llama.cpp code is physically present in this
repository — FiTuna only invokes an independently-installed copy.

---

## 2. Optional hardware-detection CLIs (invoked as subprocesses, best-effort)

`fituna/hardware.py:detect_hardware()` shells out to vendor-provided system
utilities to auto-detect GPU vendor/VRAM. These are OS/driver components,
not project dependencies, are never bundled, and detection silently falls
back to CPU-only (via the stdlib `platform` module) if a given utility is
absent:

| Tool | Vendor / origin | License | FiTuna's use |
|---|---|---|---|
| `nvidia-smi` | Ships with the NVIDIA driver package | NVIDIA proprietary (not redistributed by FiTuna — invocation only) | Query NVIDIA GPU name / VRAM |
| `rocm-smi` | ROCm (https://github.com/ROCm/rocm_smi_lib) | MIT | Query AMD GPU name / VRAM |
| `system_profiler` | Ships with macOS | Apple proprietary (not redistributed by FiTuna — invocation only) | Query Apple Silicon unified memory |

---

## 3. Perplexity evaluation corpus (user-supplied input data, not bundled)

`fituna/quality.py` requires a text corpus (`--wikitext`) to feed
`llama-perplexity`. FiTuna ships **no corpus**; the documented, recommended
choice is:

- **Dataset**: WikiText-2 (raw) — https://huggingface.co/datasets/Salesforce/wikitext
- **License**: CC-BY-SA (see the dataset page for the exact version and
  attribution terms)
- **How FiTuna uses it**: read-only, as an input file path passed straight
  through to `llama-perplexity -f <wikitext_path>`. It is never copied,
  modified, or redistributed by FiTuna; the user downloads it separately
  (see `README.md` → Requirements).

---

## 4. LLM weights being tuned (user-supplied at run time, not bundled)

The `--model` argument the user passes to `fituna run` points at a model
(GGUF file or HF-format directory) the **user** has separately obtained
(e.g. from Hugging Face). FiTuna does not embed, fine-tune, retrain, or
redistribute any model weights — it only quantizes and benchmarks the copy
already on the user's disk via the llama.cpp subprocesses above. Each such
model carries its own license, which is the user's responsibility to
comply with; see `docs/AI_MODEL_USAGE.md` for the per-run disclosure
template.

---

## 5. Development-only dependency (not included in the installed package)

- **pytest** — https://github.com/pytest-dev/pytest — MIT License. Used
  only under `pip install fituna[dev]` to run the test suite in `tests/`;
  it is declared under `[project.optional-dependencies].dev` in
  `pyproject.toml` and is **not** a dependency of the installed `fituna`
  package.

---

## Summary

| # | Component | License | Bundled in this repo? | Invocation |
|---|---|---|---|---|
| 1 | llama.cpp (`llama-quantize`, `llama-bench`, `llama-perplexity`, `llama-imatrix`, convert script) | MIT | No | `subprocess` |
| 2 | `nvidia-smi` | NVIDIA proprietary | No | `subprocess` (optional) |
| 2 | `rocm-smi` | MIT | No | `subprocess` (optional) |
| 2 | `system_profiler` | Apple proprietary | No | `subprocess` (optional) |
| 3 | WikiText-2 corpus | CC-BY-SA | No | read as file input |
| 4 | User-selected LLM weights | Varies by model | No | read as file input |
| 5 | pytest (dev-only) | MIT | No (optional-deps, dev only) | not invoked at runtime |

See `docs/SBOM.md` for the FiTuna Python standard-library module list and
`LICENSE` for FiTuna's own license (MIT).
