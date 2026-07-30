# Open-source software FiTuna adopts

## Read this before the dependency list

FiTuna's headline is **zero runtime dependencies** (`pyproject.toml`:
`dependencies = []`). Read alone, that line invites exactly the wrong
conclusion — that this project uses no open-source software.

It uses a great deal of it. FiTuna performs no tensor math, no
quantization, no inference and no perplexity computation of its own: every
number it reports is produced by **llama.cpp**, running as a separate
process, on a **GGUF** file, using **open-weight models**, evaluated
against **openly-licensed corpora**, reachable by agents over an **open
protocol**, tested on **open CI**. What FiTuna contributes is the search,
the parsing, the caching and the honesty about what was measured.

The precise claim is therefore: **FiTuna vendors nothing and links nothing;
it depends on a lot.** "Zero dependencies" is a statement about the Python
import graph and the installed wheel, not about the software stack. This
document is the stack.

Every license below was checked against a primary source on **2026-07-30**
(the project's own `LICENSE`/`License.txt` file, or the HuggingFace API's
`cardData.license` for models and datasets). The exact source and what it
returned is stated per item. Nothing here is quoted from memory; anything
that could not be verified is marked **unverified** and named as such.

## The coupling column is the important one

License consequences follow from *how* code is combined, not from whether
it was used. FiTuna uses five distinct coupling modes, and only one of them
is the mode that propagates license terms into this repository:

| Mode | Meaning | Consequence for FiTuna |
|---|---|---|
| **imported** | Runs inside the FiTuna Python process | The only mode that could impose terms on FiTuna's own distribution |
| **subprocess** | Separate OS process; FiTuna passes argv and parses stdout | No linkage. Nothing distributed. User installs it themselves |
| **file format** | Data read/written per a public specification | No linkage. Format conformance is not derivation |
| **network / IPC protocol** | Spoken to over HTTP or stdio | No linkage. FiTuna implements the client/server itself |
| **dev / CI only** | Never present in the installed package | No effect on downstream users |

Only one entry in this document is **imported**: the CPython standard
library. That is what "zero runtime dependencies" actually means.

## Master table

| # | Area | Open-source software | License (verified) | Coupling | Where in this repo |
|---|---|---|---|---|---|
| 1 | Inference / quantization engine | llama.cpp (`llama-quantize`, `llama-bench`, `llama-perplexity`, `convert_hf_to_gguf.py`) | MIT | subprocess (`llama-cli`: emitted in the result command, never run) | `quantize.py`, `bench.py`, `quality.py`, `model_info.py`, `binaries.py`, `report.py` |
| 2 | Model file format | GGUF (ggml) | MIT (spec repo) | file format | `model_info.py:200` `read_model_info()` |
| 3 | Model weights | SmolLM2-135M-Instruct | Apache-2.0 | file format (user-supplied) | `docs/RESULTS.md` Run 1/4, `notebooks/` |
| 4 | Model weights | Qwen3-4B-Instruct-2507 | Apache-2.0 | file format (user-supplied) | `docs/RESULTS.md` Run 2/3 |
| 5 | Evaluation corpus (EN) | `Salesforce/wikitext`, `wikitext-2-raw-v1` | CC BY-SA 3.0 / GFDL | file format (fetched) | `corpus.py` `PRESETS["en"]` |
| 6 | Evaluation corpus (KO) | `wikimedia/wikipedia`, `20231101.ko` | CC BY-SA 3.0 / GFDL | file format (fetched) | `corpus.py` `PRESETS["ko"]` |
| 7 | Data-access API | HuggingFace dataset-viewer | Apache-2.0 (server impl.) | network protocol (HTTP GET) | `corpus.py:51` `API_BASE` |
| 8 | Agent protocol | Model Context Protocol, rev. `2024-11-05`, over JSON-RPC 2.0 | Apache-2.0 / MIT (in transition) | IPC protocol (stdio) | `mcp_server.py` |
| 9 | Language runtime | CPython 3.11+ standard library | PSF License Agreement v2 | **imported** | whole package; `pyproject.toml` |
| 10 | Build backend | setuptools ≥ 68 | MIT | build time only | `pyproject.toml` `[build-system]` |
| 11 | CI | `actions/checkout@v4`, `actions/setup-python@v5` | MIT | dev / CI only | `.github/workflows/ci.yml` |
| 12 | Test framework | pytest | MIT | dev only (`[dev]` extra) | `tests/`, `pyproject.toml` |
| 13 | Verification environment | Jupyter notebook format, git, CMake, pip, `huggingface_hub` | BSD-3-Clause, GPL-2.0, BSD-3-Clause, MIT, Apache-2.0 | dev / notebook only | `notebooks/colab_nvidia_verification.ipynb` |
| 14 | GPU/RAM detection | `rocm-smi` (ROCm) | MIT | subprocess (optional) | `hardware.py:110` |

Non-open-source components FiTuna also invokes but never redistributes —
`nvidia-smi`, `system_profiler`, the CUDA toolkit, and the hosted
GitHub Actions and Google Colab services — are listed in §14 for
completeness, because an honest stack description includes the parts that
are not open source. `sysctl` is deliberately not in that list: §14 verifies
it as BSD-3-Clause open-source, invoked but never redistributed like the
others.

---

## 1. Inference and quantization engine — llama.cpp

**What it is.** The C/C++ LLM inference stack this entire project exists to
tune. FiTuna implements none of it.

**Where it is used.** Four llama.cpp artifacts are executed, one wrapper
each (the first three are compiled binaries; the fourth is a Python script
run through `sys.executable`):

| Binary | Called from | Purpose |
|---|---|---|
| `llama-quantize` | `fituna/quantize.py:70` (`quantize()`) | Produce a quantized GGUF from the F16/F32 base |
| `llama-bench` | `fituna/bench.py:113` (`run_bench()`) | Measure prompt/generation throughput, `-o json` |
| `llama-perplexity` | `fituna/quality.py:55` (`compute_perplexity()`) | Measure perplexity for the quality-loss gate |
| `convert_hf_to_gguf.py` | `fituna/model_info.py:165` (`ensure_base_gguf()`) | Convert an HF-format directory to a base F16 GGUF |

Two more are *located but never executed*: `llama-cli` is resolved by
`fituna/report.py:24` (`_find_llama_cli()`) purely so the printed
`run command:` line names a real path, and is checked by `fituna doctor`
(`doctor.py:299`) as an optional check; `llama-imatrix` is resolved by
`fituna/binaries.py:98` and printed by `fituna list-binaries`
(`cli.py:219`), and no code path invokes it today. Stating this precisely
matters — claiming FiTuna "uses llama-imatrix" would overstate the
relationship.

Discovery and version handling live in `fituna/binaries.py`:
`locate_binaries()` resolves the three required binaries via
`shutil.which()` on `PATH` or under `--llama-bin-dir`, and raises
`BinaryNotFoundError` pointing at upstream's build instructions rather than
failing obscurely.

**License and how it was determined.** MIT. Fetched
`https://raw.githubusercontent.com/ggml-org/llama.cpp/master/LICENSE` on
2026-07-30; its first lines read `MIT License` /
`Copyright (c) 2023-2026 The ggml authors`. The full text is reproduced in
`THIRD_PARTY_NOTICES.md` §1 to satisfy MIT's notice-preservation condition,
even though no llama.cpp byte is present in this repository.

**Coupling.** Subprocess, in every case. `subprocess.run()` with an argv
list; FiTuna reads stdout/stderr and the exit code and nothing else. No
llama.cpp header, source file, shared library or binary is compiled
against, linked, vendored, packaged or redistributed. The user installs
llama.cpp themselves and FiTuna finds it — both ways this project's own
measurements were taken (Homebrew on macOS, a CUDA source build in the
Colab notebook) work unchanged. Because there is no linkage, MIT's only operative
condition on FiTuna is notice preservation, which `THIRD_PARTY_NOTICES.md`
discharges.

**Why this is the right choice.** llama.cpp is the de-facto portable local
inference runtime (Metal, CUDA, ROCm, CPU from one codebase), so tuning
*it* is what makes FiTuna's answer usable on the machine the user has.
Deliberate design consequences of the subprocess boundary:

- FiTuna **never hardcodes a quant list**. `list_supported_quant_types()`
  (`binaries.py:123`) parses `llama-quantize --help` at run time, so a build
  with a different set of quant types is handled instead of being assumed
  away.
- FiTuna **tolerates upstream drift**. `get_llama_cpp_version()`
  (`binaries.py:138`) tries three different banner formats because the
  wording changed across llama.cpp releases; `bench.py:42` distinguishes
  llama-bench's prompt/generation records by `n_prompt`/`n_gen` rather than
  by the `"pp512"`-style label, because that label format has changed.
  `report.py:21` accepts `main` as well as `llama-cli`, upstream's older
  binary name.

**Alternative considered.** Binding to `libllama` (ctypes or a compiled
extension) instead of shelling out. Rejected: it would make FiTuna's
install depend on the user's llama.cpp ABI version, turn every upstream API
change into a build break, and require shipping or matching a compiled
artifact — while the subprocess boundary already gives everything the
search needs, since `llama-bench` is precisely the tool whose numbers we
want to report.

## 2. Model file format — GGUF

**What it is.** The single-file model container format used by llama.cpp,
specified in the ggml repository.

**Where it is used.** `fituna/model_info.py:200` `read_model_info()` opens
the file and parses the GGUF header directly with the stdlib `struct`
module: magic, version, tensor/KV counts, the metadata KV table
(`general.architecture`, `<arch>.block_count`, `general.file_type`) and the
tensor-info section, summing tensor element counts to get the true
parameter count. `n_layers` from that parse is the upper bound of the
`-ngl` binary search, and `general.file_type` drives
`is_already_quantized()` (`model_info.py:268`), which warns when the user
hands FiTuna an already-quantized file as a "baseline."

**License and how it was determined.** The specification document lives at
`https://github.com/ggml-org/ggml/blob/master/docs/gguf.md` (HTTP 200 on
2026-07-30). Its repository's `LICENSE`, fetched from
`https://raw.githubusercontent.com/ggml-org/ggml/master/LICENSE`, reads
`MIT License` / `Copyright (c) 2023-2026 The ggml authors` — the same text
as llama.cpp.

**Coupling.** File format only. No ggml code is imported, linked or copied;
`model_info.py` is an independent reader written against the published
spec. Reading a documented file format creates no derivative work.

**Why this is the right choice.** GGUF is what `llama-quantize` emits and
`llama-bench` consumes, so there is no alternative container in this
pipeline.

**Alternative considered.** Asking a llama.cpp binary to dump metadata, or
depending on the `gguf` PyPI package. The first is rejected for the reason
recorded in `model_info.py`'s own module docstring: no llama.cpp binary
exposes a "dump metadata as JSON" contract stable across versions. The
second is this document's own judgment call rather than a claim sourced
from that docstring: a PyPI dependency for what is ~100 lines of `struct`
parsing would cost the zero-dependency guarantee for a parser this small.
The parser treats the file as untrusted input — length and count
fields are bounded against the real file size before allocation
(`_read_exact()`, `_read_value()`), because a GGUF is whatever the user
downloaded.

## 3–4. Open-weight models

FiTuna bundles no weights and pins no model. `--model` is whatever the user
already has on disk. The two models below are the ones the project's own
published measurements were taken with, so they are named here as *used
open-source artifacts*, not as dependencies.

| Model | Used in | License | How determined |
|---|---|---|---|
| SmolLM2-135M-Instruct | `docs/RESULTS.md` Runs 1 and 4; `notebooks/colab_nvidia_verification.ipynb` cell 5; `docs/DEMO_SCRIPT.md` live demo | Apache-2.0 | `https://huggingface.co/api/models/HuggingFaceTB/SmolLM2-135M-Instruct` → `cardData.license: apache-2.0` (2026-07-30). The GGUF actually downloaded is `bartowski/SmolLM2-135M-Instruct-GGUF`, whose own card reports `apache-2.0` by the same query |
| Qwen3-4B-Instruct-2507 | `docs/RESULTS.md` Runs 2 and 3 | Apache-2.0 | `https://huggingface.co/api/models/Qwen/Qwen3-4B-Instruct-2507` → `cardData.license: apache-2.0`; the GGUF used, `unsloth/Qwen3-4B-Instruct-2507-GGUF`, likewise reports `apache-2.0` |

**Coupling.** File format, user-supplied. The weights are read by the
llama.cpp subprocesses, never by FiTuna, and are never committed, packaged
or redistributed. FiTuna does not train, fine-tune, distil or merge
anything; `llama-quantize` changes numeric precision inside llama.cpp's own
process. `docs/AI_MODEL_USAGE.md` carries the per-model disclosure template.

**Why these two.** They bracket the interesting range with the same
command: 135M makes a full cold search finish in ~76 s (small enough to
record live, per `docs/DEMO_SCRIPT.md`), and 4B is large enough that the
answer stops being obvious — in Run 2 the measured quality order put Q6_K
ahead of Q8_0, inverting the conventional ranking.

**Alternative rejected — and this one is a license decision.**
Qwen2.5-3B-Instruct was the earlier candidate for the mid-size run and was
dropped for its license: `https://huggingface.co/api/models/Qwen/Qwen2.5-3B-Instruct`
returns `license: other`, `license_name: qwen-research` (verified
2026-07-30), i.e. a research-use custom license, not an OSI-approved one.
It was replaced by Qwen3-4B-Instruct-2507 (Apache-2.0) so that every model
in the published results is under a permissive open license and a reviewer
can reproduce the runs without accepting a bespoke agreement. For the same
reason no gated model is used in the reproduction path — for contrast,
`meta-llama/Meta-Llama-3-8B-Instruct` reports `license: llama3`, a
community license with its own conditions.

## 5–6. Evaluation corpora

**What they are.** The plain-text corpora `llama-perplexity` runs over to
produce the quality number the search gates on.

**Where they are used.** `fituna/corpus.py` `PRESETS` defines exactly two:

- `en` → `Salesforce/wikitext`, config `wikitext-2-raw-v1`, split `test`,
  1000 rows by default
- `ko` → `wikimedia/wikipedia`, config `20231101.ko`, split `train`,
  500 rows by default

`fituna fetch-corpus` writes the text to the user's `--out` path; from then
on `fituna/quality.py:55` passes that path to `llama-perplexity -f`.

**License and how it was determined.** Both are **CC BY-SA 3.0, also
dual-licensed GFDL** — attribution and share-alike apply. Determined by
querying each dataset's own metadata on 2026-07-30:
`https://huggingface.co/api/datasets/Salesforce/wikitext` and
`https://huggingface.co/api/datasets/wikimedia/wikipedia` both return
`cardData.license: ["cc-by-sa-3.0", "gfdl"]`. `corpus.py:55` records the
same provenance in a comment, and each preset's `license_note` carries the
attribution text.

**Coupling.** File format, fetched on demand. No corpus text is committed
to this repository; `.gitignore` keeps `*.txt` outputs out. Because the
corpus is downloaded to a path of the user's choosing and never
redistributed by FiTuna, CC BY-SA's share-alike condition is not triggered
by FiTuna itself — but the user can trigger it, so `cli.py:255`
(`_cmd_fetch_corpus`) **prints the license notice and source URL to stdout
on every successful fetch**. When `--dataset/--config/--split` override a
preset, that same code path deliberately prints a *generic* "check this
dataset's own license" message instead, because asserting CC BY-SA over
someone else's dataset would be an unverified claim.

**Why this matters here more than usual.** `docs/RESULTS.md` Run 3 measured
the identical quantized files against both corpora: quality loss differed
by more than 2× (Q4_K_M, 1.73 % EN vs 0.77 % KO), and at a 1 % budget the
corpus *alone* flipped feasibility. A quality gate is only as meaningful as
its corpus, so the corpus is a first-class, documented, openly-licensed
input — not a hidden constant.

**Alternative considered.** The conventional `pip install datasets` +
snippet, which was in fact what the README documented before `corpus.py`
existed. Rejected as recorded in `corpus.py`'s module docstring: `datasets`
pulls in pyarrow/pandas — hundreds of megabytes — to download a text file,
which contradicts the zero-dependency guarantee. Replaced by ~40 lines of
stdlib `urllib` against the public REST API.

## 7. Data-access API — HuggingFace dataset-viewer

**What it is.** HuggingFace's public REST service that serves dataset rows
as JSON without authentication.

**Where it is used.** `fituna/corpus.py:51`
`API_BASE = "https://datasets-server.huggingface.co/rows"`, called from
`_fetch_page()` via `urllib.request.urlopen`. `fetch_corpus()` paginates
with `offset`/`length` (the server caps `length` at 100), validates that
the response actually contains the expected text field before writing, and
writes atomically via a temp file plus `os.replace` so a dropped connection
never leaves a partial corpus behind. The request/response shape was
verified by hand against the live API on 2026-07-30 and documented in the
module docstring, including the observed 422 cap and the "offset past the
end returns 200 with an empty `rows` list" behaviour.

**License and how it was determined.** The service's server implementation
is open source: `https://api.github.com/repos/huggingface/dataset-viewer/license`
returns SPDX `Apache-2.0` (2026-07-30). **That license does not govern
FiTuna's use of it** — FiTuna imports none of that code; it makes anonymous
HTTP GET requests to a hosted service. The obligation that actually applies
to the bytes returned is the *dataset's* CC BY-SA, handled in §5–6. The
service's own terms of use were not reviewed and are **unverified**; FiTuna
uses only the documented public endpoint with default headers and no
authentication.

**Coupling.** Network protocol. HTTP client, stdlib only.

**Why this is appropriate.** It removes the last "go and manually download
this" step from the quickstart while keeping the dependency count at zero,
and it fails loudly with actionable guidance (`_MANUAL_FALLBACK`) rather
than retrying, so a judge on a restricted network gets a clear "download it
manually or point `--quality-corpus` at any UTF-8 text file" message
instead of a hang. This is the project's only network dependency, and it is
optional: `fituna run` never touches the network.

## 8. Agent protocol — Model Context Protocol over JSON-RPC 2.0

**What it is.** MCP is the open protocol for exposing tools to AI agents.
Its stdio transport is newline-delimited JSON-RPC 2.0.

**Where it is used.** `fituna/mcp_server.py` is a complete server in 304
lines of stdlib: `serve()` runs the newline-delimited JSON-RPC loop over
stdin/stdout; `_handle()` implements `initialize`, `tools/list`,
`tools/call` and `ping`, returns `-32601` for unknown methods and `-32700`
for malformed JSON, and correctly returns *nothing* for notifications (no
`id`), per JSON-RPC 2.0. It advertises `PROTOCOL_VERSION = "2024-11-05"`
and exposes two tools, `fituna_detect_hardware` and `fituna_recommend`.
Entry point `fituna-mcp` in `pyproject.toml`.

**License and how it was determined.** The specification repository's
`LICENSE`
(`https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/LICENSE`,
fetched 2026-07-30) states that the project is **mid-transition from MIT to
Apache-2.0**: new code and specification contributions are Apache-2.0,
documentation (excluding specifications) is CC-BY-4.0, and contributions
whose authors have not consented to relicensing remain MIT. It is therefore
accurate to describe MCP as Apache-2.0/MIT in transition, and inaccurate to
call it flatly "MIT". The `2024-11-05` revision FiTuna implements exists
upstream: `https://modelcontextprotocol.io/specification/2024-11-05`
returned HTTP 200 on 2026-07-30. Its JSON Schema is *not* at a
`modelcontextprotocol.io` URL of that shape, though — both
`.../specification/2024-11-05/schema.json` and
`.../schema/2024-11-05/schema.json` 404 under that host (checked
2026-07-30). The schema does resolve, at
`https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/schema/2024-11-05/schema.json`
(HTTP 200, same date) — that is the URL to cite, not the two above.
JSON-RPC 2.0 itself is a published open specification at
`https://www.jsonrpc.org/specification`, "Copyright (C) 2007-2010 by the
JSON-RPC Working Group"; it is a specification document rather than
licensed software, and no software license is claimed for it here.

**Coupling.** IPC protocol. FiTuna speaks MCP; it does not use any MCP
implementation. No SDK, no schema library, no code from the spec repo.

**Alternative considered — and this is the clearest case in the document.**
The official MCP Python SDK. Rejected to preserve the zero-runtime-
dependency guarantee, as recorded in `mcp_server.py`'s module docstring and
`docs/ARCHITECTURE.md`: the stdio transport is newline-delimited JSON-RPC
2.0, which `json` + `sys.stdin` cover completely. The cost of that choice is
that new protocol revisions must be implemented by hand; the benefit is
that `pip install fituna` still installs exactly one package. The
implementation is protocol-tested, not assumed — `python -m
fituna.mcp_server --selfcheck` drives a real `initialize` → `tools/list` →
bad `tools/call` → notification → malformed-JSON sequence through `serve()`
and asserts the responses, and CI runs it on every push.

## 9. Language runtime — CPython standard library

**What it is.** The one thing FiTuna actually imports.

**Where it is used.** Everywhere; `pyproject.toml` declares
`requires-python = ">=3.11"` and `dependencies = []`. The load-bearing
modules, per area: `subprocess` (every llama.cpp call), `struct` (GGUF
header parsing), `sqlite3` (`cache.py`, the `--resume` result cache),
`urllib` (`corpus.py`), `json` (llama-bench output, JSON-RPC, reports), `re`
(stdout parsing), `argparse` (`cli.py`), `hashlib` (model fingerprints),
`shutil.which` (binary discovery), `dataclasses`/`enum`/`typing`
(`config.py`'s frozen-dataclass interface contract), `ctypes` (Windows RAM
query), `platform`/`os`/`pathlib`/`logging`, `tempfile`/`stat`/`io` (atomic
write-then-rename, spread across `corpus.py`, `quantize.py`, `binaries.py`,
`cache.py`, `model_info.py`, `report.py`), `sys` (`sys.executable` to invoke
`convert_hf_to_gguf.py`; stdin/stdout in `mcp_server.py`), `time`
(`search.py` elapsed-time tracking), `datetime` (`cache.py` result
timestamps), `textwrap` (`doctor.py` output formatting), `unittest.mock`
(every module's `_self_check()`/`demo()` mocks `subprocess.run` rather than
shelling out for real), and `tomllib` (`fituna/__init__.py:10`'s
version-drift self-check, parsing `pyproject.toml`) — `tomllib` is the one
genuinely 3.11-only module in this list and the actual reason
`requires-python` floors at 3.11 (see the Python-floor note two paragraphs
down). An AST scan of every top-level import across `fituna/*.py` finds
exactly 26 such modules (27 if `__future__` is counted, but that is a
compiler directive processed at parse time, not a runtime import).
**`csv` is not one of them, despite an earlier version of this document
claiming it was**: the string `"csv"` appears only as the literal
`nvidia-smi --format=csv,noheader,nounits` argument (`hardware.py:78`) and
in the function name `_parse_nvidia_csv`; no module under `fituna/` imports
the `csv` package, and both `bench.py` and `quality.py` parse JSON, not CSV.
The complete, AST-verified list is `docs/SBOM.md` rows 2–27 (row 1 being the
interpreter itself).

**License and how it was determined.** PSF License Agreement Version 2
(SPDX `PSF-2.0`). Fetched
`https://raw.githubusercontent.com/python/cpython/main/LICENSE` on
2026-07-30; the license section is headed
`Python Software Foundation License Version 2`. It is permissive and
imposes no copyleft on FiTuna.

**Coupling.** Imported — the only such entry. The declared floor is
`requires-python = ">=3.11"`, which carries **no declared upper bound**; CI
proves the floor (3.11) and the newest release tested today (3.13) across
three operating systems on every push — 3.13 is the newest version
exercised, not a ceiling the project has declared.

**Why this is appropriate.** The zero-dependency property is not asceticism
for its own sake: FiTuna's users are people already fighting a large,
fragile local-LLM toolchain, and a tuner that adds its own dependency tree
to that is a tuner they will not install. Everything a subprocess
orchestrator needs — process control, sqlite, HTTP, binary struct parsing,
JSON — is already in the stdlib.

**Alternatives considered.** `psutil` for hardware detection, rejected in
favour of a ~20-line `ctypes` call to `GlobalMemoryStatusEx` on Windows and
`/proc/meminfo`/`sysctl` elsewhere (`hardware.py:175`, with an in-code note
that `psutil` is the upgrade path if per-NUMA precision is ever needed);
`requests` for the corpus fetch, rejected in favour of `urllib.request`.

## 10. Build backend — setuptools

`pyproject.toml` `[build-system]` declares `requires = ["setuptools>=68"]`
and `build-backend = "setuptools.build_meta"`. License: MIT, per
`https://api.github.com/repos/pypa/setuptools/license` → SPDX `MIT`
(2026-07-30). **Coupling: build time only** — pip provisions it in an
isolated build environment; it is not a runtime dependency of the installed
package. Chosen because the project is a plain pure-Python package with two
console scripts and needs nothing a modern setuptools does not already do.

## 11. CI — GitHub Actions

**Where it is used.** `.github/workflows/ci.yml` runs on every push to
`main` and every pull request, over a 3 OS × 2 Python matrix
(ubuntu/macos/windows-latest × 3.11/3.13) with `fail-fast: false`. Two
steps: `pytest -q`, then every module that ships a standalone self-check.
All 17 files under `fituna/` have an `if __name__ == "__main__":` block, but
only 16 of them run an assert-based check there; CI invokes exactly those
16 (`python -m fituna.config`, `.cache`, `.search`, `.model_info`,
`.quantize`, `.quality`, `.bench`, `.hardware`, `.binaries`, `.report`,
`.corpus`, `.doctor`, `.cli`, `.mcp_server`, `.__init__`, `.errors`) — so the
assert-based checks embedded in each module are real CI gates, not
decoration. The 17th file, `fituna/__main__.py`, is the `python -m fituna`
entry point (it just calls `cli.main()`); it has no self-check of its own,
so excluding it from this list is correct, not an oversight.

**License and how it was determined.** The two reusable actions consumed
are open source and MIT: `https://api.github.com/repos/actions/checkout/license`
and `.../actions/setup-python/license` both return SPDX `MIT`
(2026-07-30). The runner itself (`actions/runner`) and the runner images
(`actions/runner-images`) are likewise MIT by the same query. **The hosted
GitHub Actions service is a proprietary GitHub product** — FiTuna consumes
it, does not redistribute it, and nothing about it is claimed as open
source here.

**Coupling.** Development/CI only; nothing from CI reaches the installed
package.

**Why this is appropriate.** FiTuna's cross-platform claims are the ones
most likely to be wrong (`shutil.which` semantics, `Path.replace` vs
`rename` on Windows, subprocess text decoding under non-UTF-8 locales), and
each of those has a matching defensive line in the source. A three-OS
matrix is what keeps those honest. Note the limit — verifiable directly
from `.github/workflows/ci.yml` itself, which has no GPU runner and no
llama.cpp build step: CI exercises FiTuna's logic, not real benchmark
runs — those are `docs/RESULTS.md` and the Colab notebook.

## 12. Test framework — pytest

**Where it is used.** `tests/test_cache.py`, `test_config.py`,
`test_corpus.py`, `test_doctor.py`, `test_hardware.py`, `test_search.py` —
fixtures, `parametrize`, `raises`. Declared as
`[project.optional-dependencies].dev = ["pytest"]` with
`[tool.pytest.ini_options] testpaths = ["tests"]`.

**License and how it was determined.** MIT, per
`https://api.github.com/repos/pytest-dev/pytest/license` → SPDX `MIT`
(2026-07-30).

**Coupling.** Dev only. `pip install fituna` does not install it; only
`pip install fituna[dev]` does. It is therefore not a dependency of the
shipped software, which is why `docs/SBOM.md` marks it dev-only.

**Why both pytest and stdlib asserts.** The two layers are deliberate, not
redundant: each module carries an assert-based `_self_check()`/`demo()`
runnable as `python -m fituna.<module>` with no framework at all (the
rationale is written into `model_info.py`: "no test framework needed for a
single module's worth of parsing logic"), while pytest carries the
cross-cutting suites where fixtures and parametrization genuinely pay —
cache key matrices, search-algorithm scenarios, hardware-parsing variants.
CI runs both. The stdlib layer is what lets a reviewer verify any single
module without installing anything.

## 13. Verification environment — Colab notebook

`notebooks/colab_nvidia_verification.ipynb` reproduces the measured search
on an NVIDIA T4 (Linux/CUDA), hardware the maintainer does not own; its
recorded outputs are `docs/RESULTS.md` Run 4. Open-source components in
that path:

| Component | Role in the notebook | License | How determined |
|---|---|---|---|
| Jupyter notebook format (`nbformat`) | The `.ipynb` file itself | BSD-3-Clause | `https://api.github.com/repos/jupyter/nbformat/license` → SPDX `BSD-3-Clause` (2026-07-30) |
| `git` | Cell 2 clones llama.cpp (`git clone --depth 1`); cell 3's `pip install git+https://...` also invokes it to clone this repository | GPL-2.0 | `https://raw.githubusercontent.com/git/git/master/COPYING` — the text itself, "GNU GENERAL PUBLIC LICENSE Version 2, June 1991" (2026-07-30). GitHub's license-detection API returns `NOASSERTION` for `git/git`, so the raw file was read directly instead of trusting that endpoint |
| CMake | Cell 2 builds llama.cpp with `-DGGML_CUDA=ON` | BSD-3-Clause | `https://api.github.com/repos/Kitware/CMake/license` → SPDX `BSD-3-Clause` (2026-07-30) |
| `pip` | Cells 3 and 5 install FiTuna and `huggingface_hub` into the Colab runtime | MIT | `https://api.github.com/repos/pypa/pip/license` → SPDX `MIT` (2026-07-30) |
| `huggingface_hub` | Cell 5 downloads the demo GGUF | Apache-2.0 | `https://api.github.com/repos/huggingface/huggingface_hub/license` → SPDX `Apache-2.0` (2026-07-30) |
| llama.cpp | Cell 2 clones and builds it from source | MIT | §1 |

**Coupling.** Notebook/dev only. `huggingface_hub` is `pip install`-ed
*inside the notebook* to fetch a file; it is not a FiTuna dependency and
appears nowhere in `pyproject.toml`. Google Colab is a proprietary hosted
Google service used as an execution environment. The CUDA toolkit used to
build llama.cpp's CUDA backend is NVIDIA proprietary, provided by the Colab
image, and not redistributed. The notebook clones llama.cpp with
`git clone --depth 1` and **no pinned tag**, so no llama.cpp version is
claimed for Run 4; the macOS runs in `docs/RESULTS.md` state their build
(Homebrew 9960) because that one was recorded.

## 14. Hardware detection utilities

`fituna/hardware.py:detect_hardware()` shells out to whatever is present
and falls back to a CPU-only profile via `platform` when nothing is. Two
of these are open source (`rocm-smi` and `sysctl`), and this document says
so rather than blurring it:

| Tool | Called from | Origin | License | Coupling |
|---|---|---|---|---|
| `rocm-smi` | `hardware.py:110` | ROCm (`ROCm/rocm_smi_lib`, `python_smi_tools/rocm_smi.py`) | **MIT** | subprocess, optional |
| `nvidia-smi` | `hardware.py:77` | NVIDIA driver package | NVIDIA proprietary | subprocess, optional |
| `system_profiler` | `hardware.py:154` | macOS | Apple proprietary | subprocess, optional |
| `sysctl` | `hardware.py:186` | macOS/BSD base system (`apple-oss-distributions/system_cmds`) | **BSD-3-Clause** — see below | subprocess, optional |
| `/proc/meminfo` | `hardware.py:179` | Linux kernel interface | n/a (kernel-provided virtual file) | file read |
| `GlobalMemoryStatusEx` | `hardware.py:213` | Windows kernel32, via `ctypes` | Microsoft proprietary | OS API call |

**`rocm-smi` license determination.** `https://raw.githubusercontent.com/ROCm/rocm_smi_lib/amd-staging_deprecated/License.txt`
— the repository's current default branch — reads `MIT License` /
`Copyright (c) 2023-2025, Advanced Micro Devices, Inc.` (2026-07-30). Worth
recording precisely: the repository's older `master` branch still carries
the **University of Illinois/NCSA Open Source License**, so a reader
checking a different branch will see a different answer. The MIT text on
the current branch is the one that applies to a present-day ROCm install.

**`sysctl` license determination.** The `sysctl` binary invoked on macOS
comes from Apple's base system, built from the open-source
`apple-oss-distributions/system_cmds` package. Its primary source,
`https://raw.githubusercontent.com/apple-oss-distributions/system_cmds/main/sysctl/sysctl.c`
(HTTP 200, 2026-07-30), carries the header
`SPDX-License-Identifier: BSD-3-Clause` and `Copyright (c) 1993 The Regents
of the University of California. All rights reserved.` — the classic
3-clause BSD text. It is a stock OS utility, invoked and never
redistributed, exactly like `system_profiler` — the difference is that this
one particular binary's upstream is itself open source, which
`system_profiler`'s is not.

None of these are bundled, and every one is optional: if all detection
fails, `detect_hardware()` returns a CPU-only `HardwareProfile` and the
search proceeds (skipping the `-ngl` binary search, per
`docs/ARCHITECTURE.md`).

---

## License obligations FiTuna actually carries

Because nothing is vendored and only the PSF-licensed stdlib is imported,
the obligation set is small and fully discharged in-repo:

| Obligation | Source | Discharged by |
|---|---|---|
| Preserve the MIT notice | llama.cpp, ggml | `THIRD_PARTY_NOTICES.md` §1 reproduces the full MIT text |
| Attribution + share-alike | CC BY-SA 3.0 corpora | `fituna fetch-corpus` prints the notice and source URL on every fetch (`cli.py:255`); no corpus text is committed |
| Model license compliance | User's chosen weights | Weights are never redistributed; `docs/AI_MODEL_USAGE.md` carries the disclosure template, and every model in the published results is Apache-2.0 |
| FiTuna's own terms | MIT (`LICENSE`) | Permissive; imposes nothing on users |

No copyleft software is linked into FiTuna. The CC BY-SA share-alike
condition attaches to corpus *text*, which FiTuna transports to a
user-chosen path and never republishes.

## What this project gives back upstream

Stated as of 2026-07-30, without inflation:

**What exists.**

- **Published cross-platform measurements of the llama.cpp toolchain** that
  are not otherwise available in one place: `docs/RESULTS.md` records four
  runs, including a case where the *same* quantized file and the *same*
  corpus produced 4.74 % quality loss under Metal and 5.22 % under CUDA —
  enough to flip a 5 % gate — and cases where a smaller quant benchmarks
  *slower* than a larger one on the same machine. Each number states the
  command, the hardware and the llama.cpp build where one was recorded.
- **A one-click reproduction path on hardware anyone can rent for free**:
  `notebooks/colab_nvidia_verification.ipynb`, with real recorded cell
  outputs, builds llama.cpp with CUDA and reruns the published experiment
  on a Colab T4.
- **A measured demonstration that quality gates are language-dependent**:
  `docs/RESULTS.md` Run 3 shows English and Korean perplexity corpora
  disagreeing by more than 2× on the same files, with the corpus alone
  flipping feasibility at a 1 % budget.
- **The tool itself**, MIT-licensed and public, usable by anyone
  benchmarking llama.cpp quantizations.
- **Run-to-run variance published rather than hidden** — including a
  thermal-throttle outlier and the direct `llama-bench` repeats that
  identified it as an outlier.

**What does not exist yet, and is not claimed.** No patch, pull request or
issue of this project's has been merged into llama.cpp, ggml, the Model
Context Protocol, or any dataset or model repository. FiTuna is a consumer
of those projects that publishes measurements about them; it is not, today,
a contributor to their code. The honest summary is: **published measured
data and a reproducible notebook, and nothing merged upstream yet.**

## Related documents

- `docs/SBOM.md` — the numbered SBOM (stdlib modules + external executables)
- `THIRD_PARTY_NOTICES.md` — required license notices, incl. llama.cpp's
  full MIT text
- `docs/AI_MODEL_USAGE.md` — per-model AI usage disclosure
- `docs/ARCHITECTURE.md` — where the subprocess boundaries sit and why
- `LICENSE` — FiTuna's own MIT license

---

## 국문 요약 — 부문별 오픈소스SW 활용

FiTuna는 **런타임 의존성이 0개**이지만, 이는 "타 오픈소스SW를 쓰지 않는다"는
뜻이 아니다. **어떤 코드도 저장소에 포함(vendoring)하거나 프로세스에 링크하지
않을 뿐**, 양자화·추론·품질측정 연산 전부를 llama.cpp에 위임하고, GGUF 포맷과
공개 가중치·공개 데이터셋·공개 프로토콜 위에서 동작한다. 아래 표의 **결합
방식**이 라이선스 의무를 결정하는 핵심 항목이다.

| 부문 | 활용 오픈소스SW | 라이선스(확인함) | 결합 방식 | 저장소 내 사용 위치 |
|---|---|---|---|---|
| 추론·양자화 엔진 | llama.cpp (`llama-quantize`/`llama-bench`/`llama-perplexity`/`convert_hf_to_gguf.py`) | MIT | **서브프로세스** (링크·포함 없음) | `quantize.py`, `bench.py`, `quality.py`, `model_info.py`, `binaries.py` |
| 모델 파일 포맷 | GGUF (ggml 사양) | MIT | **파일 포맷 준수** (`struct`로 직접 파싱) | `model_info.py:200` |
| 모델 가중치 | SmolLM2-135M-Instruct, Qwen3-4B-Instruct-2507 | 둘 다 Apache-2.0 | **사용자 제공 파일** (재배포 없음) | `docs/RESULTS.md`, `notebooks/` |
| 평가 데이터셋 | `Salesforce/wikitext`(영), `wikimedia/wikipedia` `20231101.ko`(한) | CC BY-SA 3.0 / GFDL | **내려받아 파일로 사용** (저장소 미포함) | `corpus.py` `PRESETS` |
| 데이터 조회 API | HuggingFace dataset-viewer | 서버 구현체 Apache-2.0 (FiTuna는 HTTP 호출만) | **네트워크 프로토콜** | `corpus.py:51` |
| 에이전트 연동 프로토콜 | Model Context Protocol(`2024-11-05`) / JSON-RPC 2.0 | Apache-2.0·MIT 전환 중 | **프로토콜 자체 구현** (SDK 미사용) | `mcp_server.py` |
| 언어·런타임 | CPython 3.11+ 표준 라이브러리 | PSF License Agreement v2 | **임포트** (유일한 링크 항목) | 패키지 전체, `pyproject.toml` |
| 빌드 백엔드 | setuptools ≥ 68 | MIT | 빌드 시점 한정 | `pyproject.toml` |
| CI | `actions/checkout@v4`, `actions/setup-python@v5` | 둘 다 MIT | 개발·CI 한정 | `.github/workflows/ci.yml` |
| 테스트 | pytest | MIT | 개발 한정(`[dev]` 옵션) | `tests/`, `pyproject.toml` |
| 검증 환경 | Jupyter 노트북 포맷, git, CMake, pip, `huggingface_hub` | BSD-3-Clause, GPL-2.0, BSD-3-Clause, MIT, Apache-2.0 | 노트북 한정 | `notebooks/colab_nvidia_verification.ipynb` |
| GPU 감지 | `rocm-smi` (ROCm) | MIT (현행 기본 브랜치 `License.txt`) | 서브프로세스(선택) | `hardware.py:110` |

**라이선스 확인 방법.** 위 라이선스는 모두 2026-07-30에 1차 출처에서 직접
확인했다 — 각 프로젝트의 `LICENSE`/`License.txt` 원문, 또는 모델·데이터셋의
경우 HuggingFace API의 `cardData.license` 값이다. macOS `sysctl`도
`apple-oss-distributions/system_cmds`의 `sysctl/sysctl.c` 헤더
(`SPDX-License-Identifier: BSD-3-Clause`)로 직접 확인해 §14에 반영했다 —
더 이상 미확인이 아니다. 끝내 확인하지 못했거나 의도적으로 특정하지 않은
항목은 두 가지다: HuggingFace dataset-viewer **서비스 자체**의 이용약관
(§7 — 서버 코드의 Apache-2.0 라이선스와는 별개이며, 검토하지 않았다)과
Colab Run 4의 llama.cpp 정확한 빌드 버전(§13 — 태그를 고정하지 않고 클론해
특정 버전을 주장하지 않는다).

**오픈소스가 아닌 연동 대상.** `nvidia-smi`(NVIDIA 독점),
`system_profiler`(Apple 독점), CUDA 툴킷(NVIDIA 독점), GitHub Actions·Google
Colab(각 사 호스팅 서비스)도 호출·이용하지만, 모두 재배포하지 않으며 오픈소스로
표기하지 않는다.

**FiTuna가 지는 라이선스 의무.** 벤더링·링크가 없으므로 의무는 네 가지로
정리된다: (1) llama.cpp MIT 고지 보존 — `THIRD_PARTY_NOTICES.md`에 전문
수록, (2) 코퍼스 CC BY-SA 저작자표시·동일조건 — `fituna fetch-corpus` 실행
시마다 출처·라이선스 고지를 표준출력에 인쇄하고 코퍼스 원문은 저장소에 넣지
않음, (3) 사용자가 선택한 모델의 라이선스 준수 — 가중치를 재배포하지 않고
`docs/AI_MODEL_USAGE.md`에 고지 템플릿을 제공하며 시연에 사용한 모델은 모두
Apache-2.0, (4) FiTuna 자체 라이선스(MIT) 준수 — 사용자에게 아무 의무도
부과하지 않는 permissive 라이선스. 링크된 카피레프트 소프트웨어는 없다 —
§13의 `git`(GPL-2.0)은 검증 노트북 안에서만 호출되는 개발/노트북 한정
도구이며 FiTuna 배포물에는 링크되지 않는다.

**상류 기여 현황(과장 없이).** 현재까지 llama.cpp·ggml·MCP·데이터셋 저장소에
**병합된 기여는 없다**. 대신 공개한 것은 실측 데이터
(`docs/RESULTS.md` — 동일 파일·동일 코퍼스인데 Metal 4.74 % vs CUDA 5.22 %로
품질 게이트 판정이 뒤집힌 사례 포함)와 무료 Colab T4에서 그대로 재현되는
노트북, 그리고 MIT로 공개한 도구 자체다.
