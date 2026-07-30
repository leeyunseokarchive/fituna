<!-- REUSE-IgnoreStart -->
<!--
  This document quotes `SPDX-License-Identifier:` lines as example output.
  Without these markers, `reuse lint` (§3.5) would parse the surrounding
  prose as license expressions of this file and report them as invalid --
  i.e. the document would corrupt the very scan result it publishes. The
  markers are `reuse`'s own documented remedy for quoted tags.
-->

# License compliance — the evidence, and how to reproduce it

This document is the **compliance argument**. It does not restate what
FiTuna uses; `docs/OPEN_SOURCE_USAGE.md` is the authoritative area-by-area
account of that, with every license claim checked against a primary source
and a coupling-mode column. This document answers the four questions a
license verification actually asks:

1. **What is in the distribution?** — proven from a real build.
2. **Do the combined licenses conflict?** — argued per counterparty, from
   the coupling mode.
3. **What does a scanner say?** — real tools, real commands, real output.
4. **Can a scanner classify our own files?** — SPDX identifiers, added.

Every command below was executed on **2026-07-30** on macOS 26.5.1
(arm64, build 25F80) with `Python 3.13.7 (main, Aug 14 2025, 11:12:11)
[Clang 17.0.0]`, from the repository root at commit-time state of branch
`docs/license-compliance`. **No output in this document was written by
hand**; every block below `$` is copied from a real run. Two cosmetic
normalisations, so that nothing is claimed that is not true: the throwaway
virtualenvs are shown as `/tmp/buildenv` and `/tmp/runtimeenv` where the
actual runs used a session scratch directory (the commands work verbatim at
those paths), and one long build log is elided at a marked `...`. Where a
tool was unavailable and installing it was disproportionate, that is said
plainly, together with what the substitute does and does not cover
(§3.1, §6).

---

## 1. What is actually in the distribution

### 1.1 The build

Build tooling is installed into a throwaway virtualenv **outside the
repository**, so it never becomes a dependency of anything:

```
$ python3.13 -m venv /tmp/buildenv
$ /tmp/buildenv/bin/pip install build
$ /tmp/buildenv/bin/python -m build
...
Successfully built fituna-0.1.0.tar.gz and fituna-0.1.0-py3-none-any.whl
```

`build` 1.5.0 provisions `setuptools>=77` in its own isolated environment,
exactly as `pyproject.toml` `[build-system]` declares. Neither `build` nor
`setuptools` appears in the installed package — §1.6 proves that by
installing the wheel into an empty environment and listing what arrived.

The elided `...` is setuptools' own build log. There is no
`SetuptoolsDeprecationWarning` about a license declaration to elide any more:
`pyproject.toml` now declares the PEP 639 `license = "MIT"` expression
directly (raised from `setuptools>=68` for this), so the deprecated
`license = { text = "MIT" }` form the warning used to fire on is gone. §6
records the trade this made, not a pending warning.

### 1.2 Everything in the sdist

```
$ tar -tzf dist/fituna-0.1.0.tar.gz | sort
fituna-0.1.0/
fituna-0.1.0/LICENSE
fituna-0.1.0/PKG-INFO
fituna-0.1.0/README.md
fituna-0.1.0/fituna.egg-info/
fituna-0.1.0/fituna.egg-info/PKG-INFO
fituna-0.1.0/fituna.egg-info/SOURCES.txt
fituna-0.1.0/fituna.egg-info/dependency_links.txt
fituna-0.1.0/fituna.egg-info/entry_points.txt
fituna-0.1.0/fituna.egg-info/requires.txt
fituna-0.1.0/fituna.egg-info/top_level.txt
fituna-0.1.0/fituna/
fituna-0.1.0/fituna/__init__.py
fituna-0.1.0/fituna/__main__.py
fituna-0.1.0/fituna/bench.py
fituna-0.1.0/fituna/binaries.py
fituna-0.1.0/fituna/cache.py
fituna-0.1.0/fituna/cli.py
fituna-0.1.0/fituna/config.py
fituna-0.1.0/fituna/corpus.py
fituna-0.1.0/fituna/doctor.py
fituna-0.1.0/fituna/errors.py
fituna-0.1.0/fituna/hardware.py
fituna-0.1.0/fituna/mcp_server.py
fituna-0.1.0/fituna/model_info.py
fituna-0.1.0/fituna/py.typed
fituna-0.1.0/fituna/quality.py
fituna-0.1.0/fituna/quantize.py
fituna-0.1.0/fituna/report.py
fituna-0.1.0/fituna/search.py
fituna-0.1.0/pyproject.toml
fituna-0.1.0/setup.cfg
fituna-0.1.0/tests/
fituna-0.1.0/tests/test_cache.py
fituna-0.1.0/tests/test_config.py
fituna-0.1.0/tests/test_corpus.py
fituna-0.1.0/tests/test_doctor.py
fituna-0.1.0/tests/test_hardware.py
fituna-0.1.0/tests/test_search.py
```

### 1.3 Everything in the wheel

```
$ unzip -Z1 dist/fituna-0.1.0-py3-none-any.whl | sort
fituna-0.1.0.dist-info/METADATA
fituna-0.1.0.dist-info/RECORD
fituna-0.1.0.dist-info/WHEEL
fituna-0.1.0.dist-info/entry_points.txt
fituna-0.1.0.dist-info/licenses/LICENSE
fituna-0.1.0.dist-info/top_level.txt
fituna/__init__.py
fituna/__main__.py
fituna/bench.py
fituna/binaries.py
fituna/cache.py
fituna/cli.py
fituna/config.py
fituna/corpus.py
fituna/doctor.py
fituna/errors.py
fituna/hardware.py
fituna/mcp_server.py
fituna/model_info.py
fituna/py.typed
fituna/quality.py
fituna/quantize.py
fituna/report.py
fituna/search.py
```

**24 files. 17 of them are FiTuna `.py` source, one is the empty PEP 561
`py.typed` marker, and six are build-generated metadata (one of which is
FiTuna's own MIT `LICENSE`, which the wheel format places under
`.dist-info/licenses/`).** No vendored directory, no bundled binary, no
third-party `.py`, no copied license file belonging to anyone else.

### 1.4 Proof that no file in either artifact is third-party code

A listing shows names. This shows *provenance*: every non-generated file in
both artifacts is **byte-for-byte identical to a file tracked in this
repository's git index**, so nothing was injected during the build.

```
$ python3.13 - <<'PY'
import subprocess, tarfile, zipfile, hashlib, pathlib
tracked = {p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
           for p in subprocess.run(["git","ls-files"],capture_output=True,text=True).stdout.split()}
GEN = ("PKG-INFO","SOURCES.txt","dependency_links.txt","entry_points.txt","requires.txt",
       "top_level.txt","setup.cfg",".dist-info/")
def audit(label, items):
    same=gen=unknown=0
    for name, data in items:
        rel = name.split("/",1)[1] if label=="sdist" else name
        if any(g in name for g in GEN): gen+=1; continue
        if rel in tracked and hashlib.sha256(data).hexdigest()==tracked[rel]: same+=1
        else: unknown+=1; print(f"  !! {label}: {name} is NOT a byte-identical tracked repo file")
    print(f"{label}: {same} byte-identical to tracked repo files, "
          f"{gen} build-generated metadata, {unknown} unaccounted for")
with tarfile.open("dist/fituna-0.1.0.tar.gz") as t:
    audit("sdist", [(m.name, t.extractfile(m).read()) for m in t.getmembers() if m.isfile()])
with zipfile.ZipFile("dist/fituna-0.1.0-py3-none-any.whl") as z:
    audit("wheel", [(n, z.read(n)) for n in z.namelist()])
PY
sdist: 27 byte-identical to tracked repo files, 8 build-generated metadata, 0 unaccounted for
wheel: 18 byte-identical to tracked repo files, 6 build-generated metadata, 0 unaccounted for
```

**0 unaccounted for, in both artifacts.**

### 1.5 Declared dependencies, read back out of the built wheel

```
$ unzip -p dist/fituna-0.1.0-py3-none-any.whl fituna-0.1.0.dist-info/METADATA \
    | grep -E '^(Name|Version|Requires-Python|License-Expression|License-File|Provides-Extra|Requires-Dist):'
Name: fituna
Version: 0.1.0
License-Expression: MIT
Requires-Python: >=3.11
License-File: LICENSE
Provides-Extra: dev
Requires-Dist: pytest; extra == "dev"
```

The original `grep` pattern here matched `^License:`; under `setuptools>=77`
and the PEP 639 `license = "MIT"` expression the wheel emits
`License-Expression: MIT` (Metadata-Version 2.4) instead of a bare `License:`
line, so the pattern above adds `License-Expression` to keep the block
reproducible. §6 records what this change costs.

The only `Requires-Dist` line is gated on the `dev` extra. There is no
unconditional runtime requirement.

### 1.6 Installing it into an empty environment

The decisive test — `pip` resolves the real dependency graph, and nothing
comes with it:

```
$ python3.13 -m venv /tmp/runtimeenv
$ /tmp/runtimeenv/bin/python -m pip list --format=json
[{"name": "pip", "version": "25.2"}]

$ /tmp/runtimeenv/bin/python -m pip install dist/fituna-0.1.0-py3-none-any.whl
Processing ./dist/fituna-0.1.0-py3-none-any.whl
Installing collected packages: fituna
Successfully installed fituna-0.1.0

$ /tmp/runtimeenv/bin/python -m pip list --format=json
[{"name": "fituna", "version": "0.1.0"}, {"name": "pip", "version": "25.2"}]
```

`Installing collected packages: fituna` — one package, no transitive
closure. The environment after the install is the environment before it plus
`fituna`. `pip` itself is the venv's own bootstrap, not something FiTuna
pulled in.

---

## 2. Why no license conflict exists

The general principle, taken from `docs/OPEN_SOURCE_USAGE.md`'s coupling
table: **license terms propagate through linkage and redistribution, not
through use.** FiTuna does neither, for every counterparty except the Python
standard library — and that one is PSF-2.0, which is permissive.

FiTuna's own license is MIT (`LICENSE`, `pyproject.toml`
`license = "MIT"`, a PEP 639 SPDX expression). MIT is permissive with a single operative
condition — preserve the notice — and is compatible with every license named
below.

### 2.1 llama.cpp — MIT, subprocess only

`fituna/quantize.py`, `bench.py`, `quality.py`, `model_info.py` invoke
`llama-quantize`, `llama-bench`, `llama-perplexity` and
`convert_hf_to_gguf.py` through `subprocess.run()` with an argv list, and
read back stdout/stderr and the exit code. Nothing else crosses the
boundary.

- **No linking.** No llama.cpp header is `#include`d, no `libllama` is
  loaded via `ctypes` or a compiled extension, no static or dynamic link
  step exists — FiTuna has no compiled component at all (the wheel in §1.3
  is `py3-none-any`, i.e. pure Python, no ABI tag).
- **No import.** The AST scan in §3.4 finds zero non-stdlib imports.
- **No vendoring, no redistribution.** §1.4 proves it: no file in either
  artifact came from anywhere but this repository's git index. The user
  installs llama.cpp themselves; `fituna/binaries.py:locate_binaries()`
  discovers it on `PATH` or under `--llama-bin-dir`, and raises
  `BinaryNotFoundError` pointing at upstream's build instructions when it
  is absent.

**And the question is moot anyway: llama.cpp is MIT.** Even under the
closest possible coupling — statically linking it into a single binary — MIT
and MIT do not conflict; the combined work would simply carry both notices.
The subprocess boundary is an architectural choice
(`docs/OPEN_SOURCE_USAGE.md` §1 records why), not a license workaround. The
one obligation that does apply — MIT's notice-preservation condition — is
discharged by `THIRD_PARTY_NOTICES.md` §1, which reproduces llama.cpp's full
MIT text even though no llama.cpp byte is present here.

The same reasoning covers **GGUF/ggml** (MIT): `fituna/model_info.py` is an
independent reader written against the published specification using the
stdlib `struct` module. Conformance to a documented file format is not
derivation, and the format's own repository is MIT regardless.

### 2.2 Evaluation corpora — CC BY-SA 3.0 / GFDL, never in the repository

`fituna/corpus.py` defines two presets (`Salesforce/wikitext` for English,
`wikimedia/wikipedia` `20231101.ko` for Korean). Both are CC BY-SA 3.0,
dual-licensed GFDL — copyleft-style share-alike licenses, so this is the
counterparty that deserves the most care.

Three facts remove the conflict:

1. **No corpus text is in the repository.** `.gitignore` excludes `*.txt`
   (with explicit negations for ordinary repo text files, so the rule cannot
   silently swallow a legitimate one) and the corpus temp file pattern
   `.*.tmp`. The §1.4 audit independently confirms no corpus file is in
   either artifact.
2. **FiTuna does not distribute it.** `fituna fetch-corpus` downloads to a
   path *the user chooses* (`--out`). The bytes travel from HuggingFace to
   the user; FiTuna is the transport, not the redistributor.
3. **The notice is given at fetch time.** `fituna/cli.py:256`
   (`_cmd_fetch_corpus`) prints the source URL and the license notice to
   stdout on every successful fetch, so a user who *does* go on to
   redistribute the text has been told the terms. When
   `--dataset/--config/--split` override a preset, the same code path prints
   a generic "check this dataset's own license" message instead — asserting
   CC BY-SA over a dataset we have not checked would be an unverified claim.

Share-alike attaches to the corpus text. It does not reach FiTuna's source
code, because FiTuna's source code is not a derivative or adaptation of the
corpus — it is a program that passes a file path to another program.

### 2.3 Model weights — Apache-2.0, never redistributed

`--model` is a path to a file the user already has. FiTuna does not bundle,
train, fine-tune, distil or merge weights; `llama-quantize` changes numeric
precision inside llama.cpp's own process. §1.4 confirms no `.gguf` is in
either artifact, and `.gitignore` excludes `*.gguf` and `*.gguf.tmp`.

The two models used for this project's own published measurements
(`docs/RESULTS.md`) are SmolLM2-135M-Instruct and Qwen3-4B-Instruct-2507,
both Apache-2.0, verified per `docs/OPEN_SOURCE_USAGE.md` §3–4. Apache-2.0
is permissive and compatible with MIT in the direction that matters here
(Apache-2.0 material combined into an MIT-licensed project); no combination
occurs in any case. `docs/AI_MODEL_USAGE.md` carries the per-model
disclosure template.

The model choice was itself made on license grounds: Qwen2.5-3B-Instruct was
dropped from the results because its license is `qwen-research`, a
research-use custom license rather than an OSI-approved one
(`docs/OPEN_SOURCE_USAGE.md` §3–4 records the verification). No gated or
bespoke-licensed model appears in the reproduction path.

### 2.4 GPL / AGPL / LGPL — not used, directly or indirectly

**The claim.** No GPL-family code is imported, linked, vendored or
distributed by FiTuna.

**How it was established** — four independent checks, each reproducible:

| Method | What it covers | Result |
|---|---|---|
| Installed-environment scan (§3.2) | Every distribution resolvable in a clean install | Only `fituna`, MIT. With `[dev]`: MIT, BSD-2-Clause, Apache-2.0 OR BSD-2-Clause. No GPL-family license |
| Distribution provenance audit (§1.4) | Every file in the sdist and wheel | 0 files of non-repository origin |
| AST import scan (§3.4) | Every top-level import in `fituna/*.py` | 0 non-stdlib imports |
| Repository text scan (§3.3) | Every git-tracked file | 0 copyleft matches in any code, config, notebook or CI file; the only matches are the three license-documentation files that discuss the topic on purpose |

**The one GPL component anywhere near this project, named explicitly.**
`git` is GPL-2.0 and is invoked by `notebooks/colab_nvidia_verification.ipynb`
(cell 2, `git clone --depth 1` of llama.cpp; cell 3's
`pip install git+https://...`). This is a **development/verification-time
tool executed as a separate process inside a Colab runtime**. It is not
imported, not linked, not distributed, and not present in either artifact in
§1.

Invoking a GPL program as a separate process does not make the caller a
derivative work of it. The FSF's own GPL FAQ states the criterion
(`https://www.gnu.org/licenses/gpl-faq.html`, HTTP 200, fetched
2026-07-30):

> By contrast, pipes, sockets and command-line arguments are communication
> mechanisms normally used between two separate programs. So when they are
> used for communication, the modules normally are separate programs. But if
> the semantics of the communication are intimate enough, exchanging complex
> internal data structures, that too could be a basis to consider the two
> parts as combined into a larger program.

The FAQ's own qualifier is exactly the question worth answering here, not
one to quote around: what crosses the `git` boundary is an argv list in, and
stdout/stderr/exit-code out — no complex internal data structure, no shared
memory, no callback. Command-line arguments and stdout are exactly and only
what crosses this
boundary — the same boundary described for llama.cpp in §2.1 — and FiTuna's
relationship with `git` is more distant still: the notebook, not the
package, runs it. This is stated rather than omitted because the
alternative — a scanner finding "GPL-2.0" in `docs/OPEN_SOURCE_USAGE.md` §13
while our own compliance document stays silent about it — is worse.

**The limits of this method**, stated plainly rather than glossed:

- These checks prove that no third-party *file* or *package* enters FiTuna.
  They do **not** prove that no third-party *snippet* was ever pasted into a
  FiTuna source file without a header. Detecting that requires license-text
  and code-similarity matching (ScanCode, FOSSology, Black Duck); see §3.1
  for why that class of tool was not run here and what stands in its place.
- The text scan is keyword-based. A copyleft file carrying no recognisable
  license string would not be found by it. The provenance audit in §1.4 is
  the check that does not depend on strings: it is a hash comparison.
- `pip-licenses` reports what each package's own metadata declares. A
  package that misdeclares its license would be reported wrongly. For this
  project the entire runtime list is one package — FiTuna's own — so there
  is nothing to misdeclare.

### 2.5 The conflict matrix

Every license FiTuna combines with, and the outcome:

| Counterparty | License | Coupling | Conflict with MIT? |
|---|---|---|---|
| CPython standard library | PSF-2.0 | **imported** | No — permissive, no copyleft |
| llama.cpp, ggml/GGUF | MIT | subprocess / file format | No — same license; no linkage in any case |
| Model weights (SmolLM2, Qwen3) | Apache-2.0 | user-supplied file | No — permissive; never redistributed |
| WikiText-2, Korean Wikipedia | CC BY-SA 3.0 / GFDL | fetched file | No — share-alike attaches to the text, which is neither in the repo nor in the distribution; notice printed at fetch |
| HF dataset-viewer (server) | Apache-2.0 | HTTP client | No — no code of it is used |
| Model Context Protocol | Apache-2.0 / MIT, in transition | protocol, own implementation | No — no SDK, no schema library, no spec-repo code |
| setuptools | MIT | build time only | No — isolated build env, not installed |
| pytest | MIT | dev extra only | No — not installed by `pip install fituna` |
| `rocm-smi`, `sysctl` | MIT, BSD-3-Clause | optional subprocess | No — permissive; invoked, never redistributed |
| `git` (notebook only) | GPL-2.0 | subprocess, dev/notebook | No — see §2.4 |
| CMake (notebook only) | BSD-3-Clause | subprocess, dev/notebook | No — permissive; builds llama.cpp inside Colab, never installed |
| `pip` (notebook only) | MIT | subprocess, dev/notebook | No — permissive; installs FiTuna and `huggingface_hub` inside Colab |
| `huggingface_hub` (notebook only) | Apache-2.0 | `pip install`-ed, dev/notebook | No — permissive; downloads the demo GGUF, not a FiTuna dependency |
| Jupyter notebook format (`nbformat`) | BSD-3-Clause | file format, dev/notebook | No — permissive; the `.ipynb` file itself conforms to the format |
| `actions/checkout`, `actions/setup-python` | MIT | CI action, dev only | No — permissive; runs in GitHub Actions, never shipped |

Non-open-source components FiTuna invokes but never redistributes
(`nvidia-smi`, `system_profiler`, the CUDA toolkit, and the hosted GitHub
Actions and Google Colab services) are enumerated in
`docs/OPEN_SOURCE_USAGE.md` and are not claimed as open source anywhere.

**Result: no license pair in this project is in conflict, so no resolution
measure is required.** The design decisions that produce that result — the
subprocess boundary, the zero-dependency rule, fetching rather than shipping
data — were made for engineering reasons and are recorded as such in
`docs/ARCHITECTURE.md` and `docs/OPEN_SOURCE_USAGE.md`; the clean license
position is their consequence.

---

## 3. The scans, actually run

### 3.1 What was available on this machine

Checked with `command -v` before anything was installed:

| Tool | Present? | Used |
|---|---|---|
| `pip-licenses` | no → installed into `/tmp/buildenv` | **yes** (§3.2) |
| `reuse` | no → installed into `/tmp/buildenv` | **yes** (§3.5) |
| `python3.13 -m pip list` | yes | **yes** (§1.6) |
| `git grep` | yes | **yes** (§3.3) |
| Python `ast` (stdlib) | yes | **yes** (§3.4) |
| `pipdeptree` | no | not needed — the dependency graph is a single node (§1.6) |
| `scancode` | no | **not run** — see below |
| `syft`, `trivy`, `osv-scanner`, `cyclonedx-py`, `licensecheck`, `askalono` | no | not run |

**Why ScanCode was not run.** `scancode-toolkit` ships a license-text index
of several hundred megabytes and would take longer to install and index than
this repository has files. For a codebase of 51 tracked files, 17 of which
are the shipped source, that is disproportionate. What was run instead —
`reuse` (SPDX tag extraction), `pip-licenses` (package metadata), `git grep`
(license-string presence), an AST import scan, and the hash-based
provenance audit of §1.4 — covers *declared* licensing completely and
*distribution provenance* completely.

**What it does not cover, stated so the gap is not overstated away:** none
of the tools run here performs license-text similarity matching or code
clone detection. If a reviewer needs assurance against an undeclared pasted
snippet, ScanCode or an equivalent is the right instrument, and the
reproduction commands in §5 are structured so that adding it is a single
extra step. The evidence this document *does* provide against that risk is
structural rather than statistical: FiTuna imports nothing, links nothing,
and ships nothing it did not author (§1.4).

### 3.2 Installed-environment license scan — `pip-licenses`

`pip-licenses` is run **from the build venv against the clean runtime venv**
via `--python`, so the scanner's own dependencies never enter the
environment being measured.

```
$ /tmp/buildenv/bin/pip-licenses --python /tmp/runtimeenv/bin/python \
      --from=mixed --with-authors --with-urls --format=markdown
```

| Name   | Version | License | Author              | URL                                         |
|--------|---------|---------|---------------------|---------------------------------------------|
| fituna | 0.1.0   | MIT     | FiTuna contributors | https://github.com/leeyunseokarchive/fituna |

**One row.** That is the complete license inventory of an installed FiTuna.
It reads `MIT`, not `MIT License` — `pip-licenses` derives the name from the
`License :: OSI Approved :: ...` classifier when one is present, and FiTuna's
wheel carries none (§6 explains why); with only `License-Expression: MIT` to
go on, `pip-licenses` reports the bare SPDX identifier instead.

With the development extra installed (`fituna[dev]`), for completeness —
none of this ships:

```
$ /tmp/runtimeenv/bin/python -m pip install 'dist/fituna-0.1.0-py3-none-any.whl[dev]'
$ /tmp/buildenv/bin/pip-licenses --python /tmp/runtimeenv/bin/python --from=mixed --format=markdown
```

| Name      | Version | License                    |
|-----------|---------|----------------------------|
| Pygments  | 2.20.0  | BSD-2-Clause               |
| fituna    | 0.1.0   | MIT                        |
| iniconfig | 2.3.0   | MIT                        |
| packaging | 26.2    | Apache-2.0 OR BSD-2-Clause |
| pluggy    | 1.6.0   | MIT License                |
| pytest    | 9.1.1   | MIT                        |

All permissive; no copyleft license appears even in the development
environment. (`Pygments`, `iniconfig`, `packaging` and `pluggy` are pytest's
own transitive dependencies, resolved by pip — FiTuna declares only
`pytest`.)

### 3.3 Repository-wide copyleft / proprietary text scan — `git grep`

```
$ git grep -c -i -E 'GPL|AGPL|LGPL|copyleft|CDDL|EPL-|MPL-|SSPL|Commons Clause|proprietary|All Rights Reserved' -- .
THIRD_PARTY_NOTICES.md:4
docs/LICENSE_COMPLIANCE.md:25
docs/OPEN_SOURCE_USAGE.md:13
```

Three files match, and all three match **because they are the documents
that discuss third-party licensing on purpose** — `THIRD_PARTY_NOTICES.md`'s
proprietary-utility table, `docs/OPEN_SOURCE_USAGE.md`'s §13 `git` GPL-2.0
entry and §14 proprietary-tool table, and this file, which names the
copyleft licenses in order to rule them out (§2.4). Restricting the same
scan to everything that is code, configuration or executable content:

```
$ git grep -n -i -E 'GPL|AGPL|LGPL|copyleft|CDDL|EPL-|MPL-|SSPL|Commons Clause|proprietary|All Rights Reserved' \
      -- fituna tests pyproject.toml notebooks examples .github
(no matches)
```

**Zero matches across the package, the test suite, the build configuration,
the notebook, the examples and the CI workflow.**

Method and limits: this is a case-insensitive fixed-keyword scan over
git-tracked content. It establishes the *absence of license strings*, not
the absence of unlabelled copied code — see §3.1.

### 3.4 Import-graph scan — stdlib `ast`

The zero-dependency claim, re-derived from the syntax tree rather than
trusted from `pyproject.toml`:

```
$ python3.13 - <<'PY'
import ast, pathlib, sys
mods = set()
for p in sorted(pathlib.Path("fituna").glob("*.py")):
    for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            mods |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            mods.add(n.module.split(".")[0])
std, first = sys.stdlib_module_names, {"fituna"}
print("total distinct top-level imports:", len(mods))
print("stdlib      :", sorted(mods & std))
print("first-party :", sorted(mods & first))
print("THIRD-PARTY :", sorted(mods - std - first) or "NONE")
PY
total distinct top-level imports: 28
stdlib      : ['__future__', 'argparse', 'ctypes', 'dataclasses', 'datetime', 'enum', 'hashlib', 'io', 'json', 'logging', 'os', 'pathlib', 'platform', 're', 'shutil', 'sqlite3', 'stat', 'struct', 'subprocess', 'sys', 'tempfile', 'textwrap', 'time', 'tomllib', 'typing', 'unittest', 'urllib']
first-party : ['fituna']
THIRD-PARTY : NONE
```

`THIRD-PARTY : NONE`. The 26 stdlib modules (27 counting `__future__`,
which is a compiler directive rather than a runtime import) are exactly rows
2–27 of `docs/SBOM.md`, checked name by name — the SBOM and this scan agree.

### 3.5 SPDX conformance scan — `reuse` 6.2.0

`reuse` is the FSFE's SPDX/REUSE tool; it reads `SPDX-License-Identifier`
tags out of every git-tracked file and reports what it finds.

```
$ /tmp/buildenv/bin/reuse lint
# SUMMARY

* Bad licenses: 0
* Deprecated licenses: 0
* Licenses without file extension: 0
* Missing licenses: MIT
* Unused licenses: 0
* Used licenses: MIT
* Read errors: 0
* Invalid SPDX License Expressions: 2
* Files with copyright information: 5 / 48
* Files with license information: 23 / 48

Unfortunately, your project is not compliant with version 3.3 of the REUSE Specification :-(
```

Read that output precisely, because three of its lines need explaining and
one of them is a real finding:

- **`Bad licenses: 0`, `Deprecated licenses: 0`, `Used licenses: MIT`** —
  the substantive result. Every license identifier `reuse` found in this
  repository is `MIT`, none is deprecated, and none is on its bad list.
- **`Missing licenses: MIT`** — this is *not* "MIT is missing from the
  files". It means the REUSE 3.3 specification wants a `LICENSES/MIT.txt`
  directory alongside the tags, and FiTuna keeps its license in the
  conventional root `LICENSE` file instead. Full REUSE compliance would also
  require an `SPDX-FileCopyrightText` line in all 48 files including the
  documentation. That is a stricter standard than the one being verified
  here, and the project deliberately does not adopt it; the `:-(` line is a
  statement about REUSE 3.3, not about license validity.
- **`Invalid SPDX License Expressions: 2`** — both are false positives from
  *this documentation set*: `docs/OPEN_SOURCE_USAGE.md` and `docs/SBOM.md`
  quote the string `SPDX-License-Identifier: BSD-3-Clause` inside prose
  (when explaining how macOS `sysctl`'s license was determined), and
  `reuse`'s line parser reads the trailing Korean prose as part of the
  expression. No source file is affected. This document would have added
  four more such false positives — it quotes the tag repeatedly — which is
  why an HTML-comment ignore-block marker pair (the remedy `reuse`'s own
  recommendation names) brackets this file, first line and last. Without
  them, publishing the scan would change the scan. Those two markers are the
  only place their exact spelling appears in this file, deliberately: naming
  the closing token anywhere in the prose would end the ignore block right
  there and re-expose everything below it.
- **`Files with license information: 23 / 48`** — all 23 `.py` files that
  carry the tag (§4) are counted. That includes `fituna/config.py`, which
  needs an explanation because `reuse` cannot read its own header: `reuse`
  sniffs the encoding of only the first 2048 bytes of a file
  (`HEURISTICS_CHUNK_SIZE`), and in `config.py` byte 2048 falls in the middle
  of a multi-byte UTF-8 Korean comment. `charset-normalizer` cannot decode
  the truncated chunk, `reuse` concludes the file is binary, and skips
  reading it without an error. Verified directly:

  ```
  $ /tmp/buildenv/bin/python -c "
  from reuse import extract
  raw = open('fituna/config.py','rb').read()
  print(raw[2040:2056])
  print('2 KB chunk  ->', extract.detect_encoding(raw[:2048]))
  print('2050 bytes  ->', extract.detect_encoding(raw[:2050]))
  print('whole file  ->', extract.detect_encoding(raw))"
  b'\xec\xa0\x9c\xed\x95\x9c \xec\x97\x86\xec\x9d\x8c)\xeb\xa1'
  2 KB chunk  -> None
  2050 bytes  -> utf_8
  whole file  -> utf_8
  ```

  The tag *is* present in the file — `head -1 fituna/config.py` prints
  `# SPDX-License-Identifier: MIT`, and §4's independent check confirms 23 of
  23 — but since `reuse` cannot see it directly, `REUSE.toml` supplies the
  same `MIT` identifier as a file-level annotation instead. This is REUSE's
  own documented mechanism for exactly this situation, and it does not
  depend on where in the file the annotation would otherwise sit: `reuse`
  reads `REUSE.toml` before it ever tries to sniff `config.py`'s encoding, so
  the 2048-byte heuristic never gets a chance to misfire. `reuse` also
  excludes two further files from its 48: `LICENSE` itself (it is the
  license) and the empty `fituna/py.typed` marker — plus `REUSE.toml` itself,
  which is its own configuration, not a file needing an annotation;
  48 + 3 = 51 = `git ls-files | wc -l`. The upstream mitigation for the
  underlying heuristic — installing `libmagic` so `reuse` uses `python-magic`
  instead of `charset-normalizer` for encoding detection — is a system
  package and was not installed here; `REUSE.toml` fixes the same symptom
  without it. A reviewer's own SCA tool may or may not share this quirk — it
  is recorded so that a single "unknown license" file in someone else's
  report has a documented cause, even where that reviewer's tool has no
  `REUSE.toml`-equivalent remedy.

`reuse` itself is GPL-3.0-licensed. It was installed into a throwaway venv
outside the repository, invoked as a separate process, and is not a
dependency of anything in this project — the same arm's-length relationship
described in §2.4.

---

## 4. SPDX identifiers in the source

**Status before this change: no `.py` file carried an SPDX identifier.**
Verified by `grep -rn "SPDX" fituna/ tests/` returning nothing.

**Action taken: `# SPDX-License-Identifier: MIT` was added as line 1 of all
23 Python files** — 17 in the `fituna/` package and 6 in `tests/`. No file
in this repository has a shebang, so line 1 is correct everywhere; the tag
sits above the module docstring, which leaves `__doc__` untouched (a comment
is not a string literal). Verified:

```
$ ok=0; for f in fituna/*.py tests/*.py; do
    [ "$(head -1 "$f")" = "# SPDX-License-Identifier: MIT" ] && ok=$((ok+1)) || echo "MISSING: $f"
  done; echo "line-1 SPDX tag present: $ok/$(ls fituna/*.py tests/*.py | wc -l | tr -d ' ')"
line-1 SPDX tag present: 23/23
```

And in the built wheel, so the tag reaches whoever installs the package:

```
$ for f in $(unzip -Z1 dist/fituna-0.1.0-py3-none-any.whl | grep '\.py$'); do
    printf "%-24s %s\n" "$f" "$(unzip -p dist/fituna-0.1.0-py3-none-any.whl $f | head -1)"; done
fituna/__init__.py       # SPDX-License-Identifier: MIT
fituna/__main__.py       # SPDX-License-Identifier: MIT
fituna/bench.py          # SPDX-License-Identifier: MIT
fituna/binaries.py       # SPDX-License-Identifier: MIT
fituna/cache.py          # SPDX-License-Identifier: MIT
fituna/cli.py            # SPDX-License-Identifier: MIT
fituna/config.py         # SPDX-License-Identifier: MIT
fituna/corpus.py         # SPDX-License-Identifier: MIT
fituna/doctor.py         # SPDX-License-Identifier: MIT
fituna/errors.py         # SPDX-License-Identifier: MIT
fituna/hardware.py       # SPDX-License-Identifier: MIT
fituna/mcp_server.py     # SPDX-License-Identifier: MIT
fituna/model_info.py     # SPDX-License-Identifier: MIT
fituna/quality.py        # SPDX-License-Identifier: MIT
fituna/quantize.py       # SPDX-License-Identifier: MIT
fituna/report.py         # SPDX-License-Identifier: MIT
fituna/search.py         # SPDX-License-Identifier: MIT
```

Why it matters: without the tag, a scanner classifies each file as *unknown
license* and reports it as an unresolved item even though the repository has
a perfectly good root `LICENSE`. With it, every source file self-identifies —
22 directly via this header, and `fituna/config.py` via the `REUSE.toml`
annotation described in §3.5, because `reuse` cannot read its own header —
and this project's own SCA scan (§3.5) has nothing left to flag under "no
copyright and licensing information."

**Regression check.** Adding a line to every file shifts every line number
below it. Both consequences were checked and handled:

- `python3.13 -m pytest -q` → **151 passed**, and all 16 module self-checks
  listed in `.github/workflows/ci.yml` still exit 0.
- `docs/OPEN_SOURCE_USAGE.md` cites source locations as `file.py:NNN` in 38
  places. Each was verified — by comparing the cited line in the pre-change
  file (`git show HEAD:<path>`) against line *N*+1 in the post-change file —
  to be a clean one-line shift, 30 distinct `file:line` references, 0 mismatches, and
  then bumped by one. No other file in the repository uses `file.py:NNN`
  citations.

---

## 5. How to reproduce every claim in this document

From a clean checkout, on any platform with Python 3.11+ and git. Nothing
here installs anything into the project.

```bash
# --- 0. tooling, in throwaway venvs outside the repo -------------------
python3 -m venv /tmp/buildenv
/tmp/buildenv/bin/pip install build pip-licenses 'reuse[charset-normalizer]'

# --- 1. what ships (§1) ------------------------------------------------
rm -rf build dist fituna.egg-info
/tmp/buildenv/bin/python -m build
tar -tzf dist/fituna-0.1.0.tar.gz | sort
unzip -Z1 dist/fituna-0.1.0-py3-none-any.whl | sort
unzip -p dist/fituna-0.1.0-py3-none-any.whl fituna-0.1.0.dist-info/METADATA \
  | grep -E '^(Name|Version|Requires-Python|License-Expression|License-File|Provides-Extra|Requires-Dist):'

# --- 2. zero runtime dependencies, resolved by pip (§1.6) --------------
python3 -m venv /tmp/runtimeenv
/tmp/runtimeenv/bin/python -m pip list --format=json          # baseline
/tmp/runtimeenv/bin/python -m pip install dist/fituna-0.1.0-py3-none-any.whl
/tmp/runtimeenv/bin/python -m pip list --format=json          # + fituna, nothing else

# --- 3. license inventory of the installed package (§3.2) --------------
/tmp/buildenv/bin/pip-licenses --python /tmp/runtimeenv/bin/python \
  --from=mixed --with-authors --with-urls --format=markdown

# --- 4. no copyleft / proprietary strings in code (§3.3) ---------------
git grep -c -i -E 'GPL|AGPL|LGPL|copyleft|CDDL|EPL-|MPL-|SSPL|Commons Clause|proprietary|All Rights Reserved' -- .
git grep -n -i -E 'GPL|AGPL|LGPL|copyleft|CDDL|EPL-|MPL-|SSPL|Commons Clause|proprietary|All Rights Reserved' \
  -- fituna tests pyproject.toml notebooks examples .github

# --- 5. SPDX tags (§3.5, §4) -------------------------------------------
/tmp/buildenv/bin/reuse lint
for f in fituna/*.py tests/*.py; do head -1 "$f"; done | sort | uniq -c

# --- 6. no third-party imports (§3.4) ----------------------------------
#      (the AST snippet in §3.4, pasted verbatim)

# --- 7. nothing in the artifacts came from outside the repo (§1.4) -----
#      (the provenance snippet in §1.4, pasted verbatim)

# --- 8. nothing broke (same two steps CI runs) --------------------------
/tmp/runtimeenv/bin/python -m pip install pytest
/tmp/runtimeenv/bin/python -m pytest -q            # expect: 151 passed
for m in __init__ errors config cache search model_info quantize quality \
         bench hardware binaries report; do /tmp/runtimeenv/bin/python -m fituna.$m || break; done
for m in corpus doctor cli mcp_server; do /tmp/runtimeenv/bin/python -m fituna.$m --selfcheck || break; done
```

---

## 6. Known limitations and open items

Recorded so that nothing in this document is read as covering more than it
does.

| Item | Status |
|---|---|
| Code-similarity / license-text matching (ScanCode, FOSSology) | **Not run** — disproportionate for 51 tracked files; see §3.1 for what stands in its place and what that leaves uncovered |
| `reuse` can't read `fituna/config.py`'s own header | **Tool limitation, diagnosed and worked around** (§3.5). `reuse`'s 2 KB encoding heuristic truncates a multi-byte character, so it never reads the in-file tag. Not fixed by reshaping the file's byte layout — that would be fragile in both directions and dependent on comment length staying clear of byte 2048. Fixed instead with a `REUSE.toml` file-level annotation, REUSE's own documented mechanism for this case, which does not depend on byte position |
| REUSE 3.3 full compliance (`LICENSES/` directory, per-file copyright tags) | **Not adopted** — a stricter standard than this verification asks for; the root `LICENSE` plus per-file SPDX tags is the conventional position |
| `pyproject.toml` license declaration | **Changed**: `license = { text = "MIT" }` was replaced with the PEP 639 SPDX expression `license = "MIT"`, which required raising the build-backend floor from `setuptools>=68` to `>=77` (the version that supports the expression form). One cost came with it: the `License :: OSI Approved :: MIT License` classifier had to be removed, because `setuptools>=77` raises `InvalidConfigError` — "License classifiers have been superseded by license expressions" — if a license expression and an OSI classifier are both present (verified directly: re-adding the classifier alongside `license = "MIT"` fails the build with exactly that error). The wheel's metadata now carries `License-Expression: MIT` under Metadata-Version 2.4 instead of the old `License: MIT` field — still machine-readable, and it is what `pip-licenses` reads (§3.2). The narrow residual cost: any tool that reads `importlib.metadata`'s `License` key directly, or filters packages by the OSI classifier string, sees nothing for FiTuna now — it has to read `License-Expression` or parse the SPDX identifier instead |
| HuggingFace dataset-viewer **service** terms of use | **Unverified**, as `docs/OPEN_SOURCE_USAGE.md` §7 already states. The server implementation's Apache-2.0 license was verified; the hosted service's terms were not reviewed |
| llama.cpp build version used for `docs/RESULTS.md` Run 4 | **Not claimed** — the Colab notebook clones without a pinned tag, so no version is asserted (`docs/OPEN_SOURCE_USAGE.md` §13) |
| `docs/SBOM.md` lists pytest's version as "latest" | **Left as is** — accurate for an unpinned `dev` extra. The version resolved at scan time was 9.1.1 (§3.2) |

---

## Related documents

- `docs/OPEN_SOURCE_USAGE.md` — what FiTuna uses, area by area, with the
  coupling mode and the primary source for every license claim
- `docs/SBOM.md` — the numbered SBOM (stdlib modules + external executables)
- `THIRD_PARTY_NOTICES.md` — required notices, including llama.cpp's full
  MIT text
- `docs/AI_MODEL_USAGE.md` — per-model AI usage disclosure
- `LICENSE` — FiTuna's own MIT license

<!-- REUSE-IgnoreEnd -->
