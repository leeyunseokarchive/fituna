<!-- REUSE-IgnoreStart -->
<!--
  이 문서는 예시 출력으로 `SPDX-License-Identifier:` 줄을 인용한다.
  이 marker가 없으면 `reuse lint`(§3.5)가 주변 설명까지 이 파일의 license
  expression으로 해석해 invalid로 보고한다. 즉 문서가 자신이 공개한 scan 결과를
  오염시키게 된다. 이 marker는 인용한 tag에 대해 `reuse`가 문서화한 해결책이다.
-->

# 라이선스 준수 근거와 재현 방법

이 문서는 **라이선스 준수 근거**를 제시합니다. FiTuna가 사용하는 구성요소를
반복해서 나열하지 않습니다. 부문별 구성요소, 1차 출처로 확인한 라이선스,
결합 방식은 `docs/OPEN_SOURCE_USAGE.md`가 기준 문서입니다. 여기서는 라이선스
검증에서 실제로 묻는 네 가지 질문에 답합니다.

1. **배포물에는 무엇이 들어 있는가?** — 실제 빌드로 증명합니다.
2. **결합한 라이선스가 충돌하는가?** — 구성요소별 결합 방식으로 판단합니다.
3. **Scanner의 결과는 무엇인가?** — 실제 도구, 명령, 출력을 제시합니다.
4. **Scanner가 자체 파일을 분류할 수 있는가?** — SPDX 식별자를 추가했습니다.

아래 명령은 **2026-07-30**에 macOS 26.5.1(arm64, build 25F80), `Python
3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0]` 환경에서
`docs/license-compliance` branch의 당시 저장소 root를 기준으로 실행했습니다.
**문서의 출력을 손으로 작성하지 않았습니다.** `$` 뒤 block은 실제 실행에서
복사했습니다. 사실과 다른 인상을 주지 않도록 표현만 두 곳 통일했습니다. 실제로는
session 임시 디렉터리를 쓴 일회용 virtualenv 경로를 그대로 실행 가능한
`/tmp/buildenv`, `/tmp/runtimeenv`로 표시했고, 긴 빌드 log 한 곳은 `...`로
생략했다고 밝혔습니다. 도구를 사용할 수 없고 설치 비용이 지나치게 크면 그 사실과
대체 검사의 범위·한계를 §3.1과 §6에 명시합니다.

---

## 1. 실제 배포물의 구성

### 1.1 빌드

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

### 1.2 sdist 전체 목록

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
fituna-0.1.0/fituna/quickstart.py
fituna-0.1.0/fituna/report.py
fituna-0.1.0/fituna/search.py
fituna-0.1.0/pyproject.toml
fituna-0.1.0/setup.cfg
fituna-0.1.0/tests/
fituna-0.1.0/tests/test_cache.py
fituna-0.1.0/tests/test_cli.py
fituna-0.1.0/tests/test_config.py
fituna-0.1.0/tests/test_corpus.py
fituna-0.1.0/tests/test_doctor.py
fituna-0.1.0/tests/test_hardware.py
fituna-0.1.0/tests/test_quickstart.py
fituna-0.1.0/tests/test_report.py
fituna-0.1.0/tests/test_search.py
```

### 1.3 wheel 전체 목록

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
fituna/quickstart.py
fituna/report.py
fituna/search.py
```

**25 files. 18 of them are FiTuna `.py` source, one is the empty PEP 561
`py.typed` marker, and six are build-generated metadata (one of which is
FiTuna's own MIT `LICENSE`, which the wheel format places under
`.dist-info/licenses/`).** No vendored directory, no bundled binary, no
third-party `.py`, no copied license file belonging to anyone else.

### 1.4 두 산출물에 제3자 코드가 없다는 증명

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

### 1.5 빌드한 wheel에서 다시 읽은 의존성 선언

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

### 1.6 빈 환경에 설치

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

## 2. 라이선스가 충돌하지 않는 이유

`docs/OPEN_SOURCE_USAGE.md`의 결합 방식 표가 제시하는 원칙은 **라이선스 조건은
단순 사용이 아니라 link와 재배포를 통해 전달된다**는 것입니다. FiTuna는 Python
표준 라이브러리를 제외한 어떤 구성요소도 link하거나 재배포하지 않으며, 표준
라이브러리의 PSF-2.0도 permissive license입니다.

FiTuna 자체 라이선스는 MIT입니다(`LICENSE`, `pyproject.toml`의 PEP 639 SPDX
expression `license = "MIT"`). MIT는 고지 보존 하나만 요구하는 permissive
license이며 아래 모든 라이선스와 호환됩니다.

### 2.1 llama.cpp — MIT, subprocess만 사용

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

### 2.2 평가 corpus — CC BY-SA 3.0 / GFDL, 저장소 미포함

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
3. **The notice is given at fetch time.** `fituna/cli.py:320`
   (`_cmd_fetch_corpus`) prints the source URL and the license notice to
   stdout on every successful fetch, so a user who *does* go on to
   redistribute the text has been told the terms. When
   `--dataset/--config/--split` override a preset, the same code path prints
   a generic "check this dataset's own license" message instead — asserting
   CC BY-SA over a dataset we have not checked would be an unverified claim.

Share-alike attaches to the corpus text. It does not reach FiTuna's source
code, because FiTuna's source code is not a derivative or adaptation of the
corpus — it is a program that passes a file path to another program.

### 2.3 모델 weight — Apache-2.0 / MIT, 재배포하지 않음

`--model` is a path to a file the user already has. FiTuna does not bundle,
train, fine-tune, distil or merge weights; `llama-quantize` changes numeric
precision inside llama.cpp's own process. §1.4 confirms no `.gguf` is in
either artifact, and `.gitignore` excludes `*.gguf` and `*.gguf.tmp`.

The three models used for this project's own published measurements
(`docs/RESULTS.md`) are SmolLM2-135M-Instruct and Qwen3-4B-Instruct-2507
(both Apache-2.0) and Midm-2.0-Mini-Instruct (MIT), verified per
`docs/OPEN_SOURCE_USAGE.md` §3–4. Both Apache-2.0 and MIT are permissive and
compatible with MIT in the direction that matters here (that material
combined into an MIT-licensed project); no combination occurs in any case.
`docs/AI_MODEL_USAGE.md` carries the per-model disclosure template and the
same three models.

The model choice was itself made on license grounds: Qwen2.5-3B-Instruct was
dropped from the results because its license is `qwen-research`, a
research-use custom license rather than an OSI-approved one
(`docs/OPEN_SOURCE_USAGE.md` §3–4 records the verification). No gated or
bespoke-licensed model appears in the reproduction path.

### 2.4 GPL / AGPL / LGPL — 직간접적으로 사용하지 않음

**주장.** No GPL-family code is imported, linked, vendored or
distributed by FiTuna.

**확인 방법** — four independent checks, each reproducible:

| Method | What it covers | Result |
|---|---|---|
| Installed-environment scan (§3.2) | Every distribution resolvable in a clean install | Only `fituna`, MIT. With `[dev]`: MIT, BSD-2-Clause, Apache-2.0 OR BSD-2-Clause. No GPL-family license |
| Distribution provenance audit (§1.4) | Every file in the sdist and wheel | 0 files of non-repository origin |
| AST import scan (§3.4) | Every top-level import in `fituna/*.py` | 0 non-stdlib imports |
| Repository text scan (§3.3) | Every git-tracked file | 0 copyleft matches in any code, config, notebook or CI file; the only matches are the three license-documentation files that discuss the topic on purpose |

**프로젝트 주변의 유일한 GPL 구성요소.**
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

**이 방법의 한계**, stated plainly rather than glossed:

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

### 2.5 충돌 검토표

FiTuna와 관계된 모든 라이선스와 검토 결과입니다.

| 구성요소 | 라이선스 | 결합 방식 | MIT와 충돌 여부 |
|---|---|---|---|
| CPython standard library | PSF-2.0 | **imported** | No — permissive, no copyleft |
| llama.cpp, ggml/GGUF | MIT | subprocess / file format | No — same license; no linkage in any case |
| Model weights (SmolLM2, Qwen3) | Apache-2.0 | user-supplied file | No — permissive; never redistributed |
| Model weights (Midm-2.0-Mini) | MIT | user-supplied file | No — same license; never redistributed |
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

## 3. 실제 실행한 scan

### 3.1 이 컴퓨터에서 사용할 수 있었던 도구

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
this repository has files. For a codebase of 57 tracked files, 18 of which
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

### 3.2 설치 환경 라이선스 scan — `pip-licenses`

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

### 3.3 저장소 전체 copyleft·독점 문구 scan — `git grep`

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

### 3.4 Import graph scan — 표준 라이브러리 `ast`

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

`THIRD-PARTY : NONE`. The 29 stdlib modules (30 counting `__future__`,
which is a compiler directive rather than a runtime import) are exactly rows
2–30 of `docs/SBOM.md`, checked name by name — the SBOM and this scan agree.

### 3.5 SPDX 준수 scan — `reuse` 6.2.0

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
* Files with copyright information: 6 / 54
* Files with license information: 27 / 54

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
  require an `SPDX-FileCopyrightText` line in all 54 files including the
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
- **`Files with copyright information: 6 / 54`** — not a compliance signal.
  `reuse` counts any file in which it finds a copyright notice, and the six
  are the root `LICENSE`, `THIRD_PARTY_NOTICES.md` and the four documents
  that *quote* someone else's notice while recording where a license was
  read from (`README.md`, `docs/ARCHITECTURE.md`,
  `docs/OPEN_SOURCE_USAGE.md`, `docs/RESULTS.md`). FiTuna's `.py` files carry
  `SPDX-License-Identifier` but deliberately no `SPDX-FileCopyrightText`
  line — see the `Missing licenses` bullet above and §6.
- **`Files with license information: 27 / 54`** — all 27 `.py` files that
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
  `# SPDX-License-Identifier: MIT`, and §4's independent check confirms 27 of
  27 — but since `reuse` cannot see it directly, `REUSE.toml` supplies the
  same `MIT` identifier as a file-level annotation instead. This is REUSE's
  own documented mechanism for exactly this situation, and it does not
  depend on where in the file the annotation would otherwise sit: `reuse`
  reads `REUSE.toml` before it ever tries to sniff `config.py`'s encoding, so
  the 2048-byte heuristic never gets a chance to misfire. `reuse` also
  excludes two further files from its 54: `LICENSE` itself (it is the
  license) and the empty `fituna/py.typed` marker — plus `REUSE.toml` itself,
  which is its own configuration, not a file needing an annotation;
  54 + 3 = 57 = `git ls-files | wc -l`. The upstream mitigation for the
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

## 4. 소스의 SPDX 식별자

**Status before this change: no `.py` file carried an SPDX identifier.**
Verified by `grep -rn "SPDX" fituna/ tests/` returning nothing.

**Action taken: `# SPDX-License-Identifier: MIT` was added as line 1 of all
27 Python files** — 18 in the `fituna/` package and 9 in `tests/`. No file
in this repository has a shebang, so line 1 is correct everywhere; the tag
sits above the module docstring, which leaves `__doc__` untouched (a comment
is not a string literal). Verified:

```
$ ok=0; for f in fituna/*.py tests/*.py; do
    [ "$(head -1 "$f")" = "# SPDX-License-Identifier: MIT" ] && ok=$((ok+1)) || echo "MISSING: $f"
  done; echo "line-1 SPDX tag present: $ok/$(ls fituna/*.py tests/*.py | wc -l | tr -d ' ')"
line-1 SPDX tag present: 27/27
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
fituna/quickstart.py     # SPDX-License-Identifier: MIT
fituna/report.py         # SPDX-License-Identifier: MIT
fituna/search.py         # SPDX-License-Identifier: MIT
```

중요한 이유: without the tag, a scanner classifies each file as *unknown
license* and reports it as an unresolved item even though the repository has
a perfectly good root `LICENSE`. With it, every source file self-identifies —
26 directly via this header, and `fituna/config.py` via the `REUSE.toml`
annotation described in §3.5, because `reuse` cannot read its own header —
and this project's own SCA scan (§3.5) has nothing left to flag under "no
copyright and licensing information."

**Regression 검사.** Adding a line to every file shifts every line number
below it. Both consequences were checked and handled:

- `python3.13 -m pytest -q` → **246 passed**, and all 17 module self-checks
  listed in `.github/workflows/ci.yml` still exit 0.
- Four documents cite source locations as `file.py:NNN`, not one:
  `docs/OPEN_SOURCE_USAGE.md` (38 occurrences, 30 distinct `file:line`
  references), plus one each in `SECURITY.md`, `docs/DEVELOPMENT.md` and
  this file (§2.2). The original sweep covered only
  `docs/OPEN_SOURCE_USAGE.md` and wrongly asserted it was the only such
  file. All four have since been swept together and every citation
  re-verified by reading the cited line in the current source. Five stale
  occurrences were found and corrected: the three pointing at the CC BY-SA
  notice in `_cmd_fetch_corpus` (one here, two in
  `docs/OPEN_SOURCE_USAGE.md` — all three still named the last line of
  `_cmd_doctor`), and two mutually inconsistent anchors for one `bench.py` self-check,
  which now both name its `def _self_check()` line. The scope of a citation
  sweep is the whole repository, not one document:

  ```
  $ grep -rn --include="*.md" -E "[a-z_]+[.]py:[0-9]+" .
  ```

---

## 5. 문서의 모든 주장을 재현하는 방법

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
/tmp/runtimeenv/bin/python -m pytest -q            # expect: 0 failed (246 passed at the time of writing)
for m in __init__ errors config cache search model_info quantize quality \
         bench hardware binaries report; do /tmp/runtimeenv/bin/python -m fituna.$m || break; done
for m in corpus doctor quickstart cli mcp_server; do /tmp/runtimeenv/bin/python -m fituna.$m --selfcheck || break; done
```

---

## 6. 알려진 한계와 남은 항목

이 문서가 실제 검증 범위보다 넓게 읽히지 않도록 한계를 기록합니다.

| 항목 | 상태 |
|---|---|
| Code similarity / 라이선스 원문 matching(ScanCode, FOSSology) | **실행하지 않음** — 추적 파일 57개에 비해 비용이 큼. 대체 검사와 남는 사각지대는 §3.1 참조 |
| `reuse`가 `fituna/config.py` 자체 header를 읽지 못함 | **도구 한계를 진단하고 우회함**(§3.5). `reuse`의 2 KB encoding heuristic이 multi-byte 문자를 중간에서 잘라 파일 안 tag를 읽지 못함. 파일 byte 배치를 바꾸는 방식은 주석 길이와 2048번째 byte 위치에 의존해 취약하므로 쓰지 않고, byte 위치와 무관하며 REUSE가 공식 지원하는 `REUSE.toml` 파일 단위 annotation으로 해결 |
| REUSE 3.3 완전 준수(`LICENSES/` 디렉터리, 파일별 copyright tag) | **채택하지 않음** — 이번 검증 범위보다 엄격한 표준. root `LICENSE`와 파일별 SPDX tag를 사용하는 일반적인 방식을 유지 |
| `pyproject.toml` 라이선스 선언 | **변경함** — `license = { text = "MIT" }`를 PEP 639 SPDX expression `license = "MIT"`로 바꾸고 이를 지원하는 `setuptools>=77`로 build backend 최저 버전을 68에서 올림. Expression과 OSI classifier를 함께 두면 `setuptools>=77`이 `InvalidConfigError`를 내므로 `License :: OSI Approved :: MIT License` classifier는 제거. Wheel metadata는 기존 `License: MIT` 대신 Metadata-Version 2.4의 `License-Expression: MIT`를 포함하며 `pip-licenses`가 이를 읽음(§3.2). `importlib.metadata`의 `License` key나 OSI classifier 문자열만 보는 도구는 FiTuna를 찾지 못하므로 `License-Expression` 또는 SPDX 식별자를 읽어야 함 |
| HuggingFace dataset-viewer **service** 이용약관 | **미확인** — `docs/OPEN_SOURCE_USAGE.md` §7에 명시. Server 구현의 Apache-2.0은 확인했지만 hosted service 약관은 검토하지 않음 |
| `docs/RESULTS.md` Run 4의 llama.cpp 빌드 버전 | **주장하지 않음** — Colab notebook이 tag를 고정하지 않고 clone하므로 버전을 특정하지 않음(`docs/OPEN_SOURCE_USAGE.md` §13) |
| `docs/SBOM.md`의 pytest 버전이 "latest" | **유지** — version을 고정하지 않은 `dev` extra에 맞는 표현. Scan 당시 해석된 버전은 9.1.1(§3.2) |

---

## 관련 문서

- `docs/OPEN_SOURCE_USAGE.md` — FiTuna가 활용하는 구성요소, 결합 방식, 각
  라이선스 주장의 1차 출처
- `docs/SBOM.md` — 번호를 붙인 SBOM(표준 라이브러리 모듈 + 외부 실행 파일)
- `THIRD_PARTY_NOTICES.md` — llama.cpp MIT 전문을 포함한 필수 고지
- `docs/AI_MODEL_USAGE.md` — 모델별 AI 활용 공개
- `LICENSE` — FiTuna 자체 MIT license

<!-- REUSE-IgnoreEnd -->
