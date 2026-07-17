# Third-Party Notices

FiTuna does not vendor or redistribute any third-party source code. All
runtime dependencies of FiTuna itself are the Python 3.11 standard library
(see `docs/SBOM.md`).

FiTuna does, however, invoke the following external program as a
**subprocess** at runtime. It is not bundled with this repository; the user
installs it separately (their own build of the upstream project) and points
FiTuna at it via `--llama-bin-dir` or `PATH`.

## llama.cpp

- Project: https://github.com/ggml-org/llama.cpp
- License: MIT
- Usage: FiTuna shells out to `llama-quantize`, `llama-bench`,
  `llama-perplexity`, and optionally `llama-imatrix` / the HF-to-GGUF convert
  script. No llama.cpp source or binary is copied into this repository;
  FiTuna only starts it as a separate OS process and parses its stdout.

## Optional hardware-detection CLIs

FiTuna may shell out to vendor-provided system utilities to auto-detect GPU
hardware. These are OS/driver components, not project dependencies, and are
never bundled:

- `nvidia-smi` (NVIDIA driver package)
- `rocm-smi` (ROCm)
- `system_profiler` (Apple, ships with macOS)
