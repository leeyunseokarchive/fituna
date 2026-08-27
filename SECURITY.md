# Security Policy

## Supported versions

FiTuna is pre-1.0. Only the latest release (`0.2.0`) and `main` are supported;
fixes land on `main` and ship in the next release.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting:
[**Security → Report a vulnerability**](https://github.com/leeyunseokarchive/fituna/security/advisories/new).
If that is unavailable to you, email the maintainer at `dbstjr3576@gmail.com`
with `[fituna security]` in the subject.

Please include the FiTuna command you ran, your OS and llama.cpp build
(`fituna doctor --json` covers both), and what an attacker gains. Expect an
acknowledgement within a week — this is a solo, volunteer-maintained project.
Please do not open a public issue for a vulnerability until it has a fix.

## Trust boundary

FiTuna performs no inference or quantization itself: it executes llama.cpp
binaries as subprocesses and parses their output. Those binaries are found at
paths **you** supply — `--llama-bin-dir`, or whatever `llama-quantize` and
`llama-bench`/`llama-perplexity` your `PATH` resolves to — and FiTuna runs
them with your privileges. It also reads model files you point it at and, in
`fituna fetch-corpus`, fetches text from a fixed host
(`https://datasets-server.huggingface.co`); `--dataset`/`--config`/`--split`
only choose *which* dataset on that host, not the host itself. So: pointing
FiTuna at an untrusted binary or directory is executing that untrusted thing,
and fetching a dataset you did not vet is ingesting untrusted *text* from
that fixed host — FiTuna neither sandboxes nor verifies either. Treat
`--llama-bin-dir`, `PATH`, the `--out` directory, and the dataset you name
via `--dataset`/preset as inputs you control.

The largest exposure is not `--llama-bin-dir` itself but where it can point:
converting an HF-format model directory (`fituna/model_info.py:166-177`) runs
`[sys.executable, convert_hf_to_gguf.py, ...]` — an arbitrary Python script
executed by the same interpreter running FiTuna. That script is resolved by
`fituna/binaries.py`'s `_find_script`, which looks not only in `bin_dir`
(your `--llama-bin-dir`) but also in `bin_dir.parent.parent` — two directory
levels *above* the path you pointed at. A `--llama-bin-dir` two levels below
an attacker-writable `convert_hf_to_gguf.py` is enough to get it executed.
Treat that fallback as part of the boundary: `--llama-bin-dir` and everything
up to two parents above it are inputs you control.

FiTuna never executes `llama-cli` or `llama-server`: `fituna doctor`/
`report.py` only locate them on `PATH`/`--llama-bin-dir` to report whether
they are available, and `fituna run`'s `--json`/human output emits
`llama-cli ...` / `llama-server ...` command strings (`report.py`'s
`build_run_command` / `build_server_command`) for *you* to run afterwards —
they are not run by FiTuna itself. `--export-ollama` likewise only *writes*
a `Modelfile` next to the produced `.gguf` (`report.py`'s
`export_ollama_modelfile`); FiTuna never invokes `ollama`.

Bugs *inside* this boundary — FiTuna mishandling an untrusted path, model
file, script, or downloaded corpus in a way that grants more than the above —
are in scope and worth reporting.
