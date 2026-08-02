# SBOM (Software Bill of Materials) — 붙임1

FiTuna의 런타임 파이썬 의존성은 **0개**입니다 (표준 라이브러리만 사용).
아래 표는 사용된 표준 라이브러리 모듈과, 프로세스 형태로 연동하는 외부 실행
도구(파이썬 패키지 아님)를 함께 정리한 것입니다. 표준 라이브러리 모듈 목록은
`fituna/*.py` 전체에 대한 AST(추상 구문 트리) 스캔으로 재도출했습니다 — 문자열
grep이 아니라 실제 import 문만 집계한 결과입니다.

| 번호 | 라이브러리/도구명 | 버전 | 라이선스 | 공식 저장소 URL | 사용 목적 |
|----|------------------|------|----------|------------------|-----------|
| 1 | Python | 3.11+ | PSF License | https://github.com/python/cpython | 실행 런타임 |
| 2 | subprocess (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | llama.cpp 바이너리 호출 |
| 3 | dataclasses (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 모듈 간 타입 계약 |
| 4 | enum (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 열거형 상수 정의 |
| 5 | argparse (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | CLI 파싱 |
| 6 | pathlib (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 파일 경로 처리 |
| 7 | sqlite3 (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 벤치/품질 결과 캐시 |
| 8 | json (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | llama-bench JSON 출력 파싱 |
| 9 | re (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 바이너리 stdout 파싱 |
| 10 | struct (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | GGUF 헤더 파싱 |
| 11 | hashlib (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 모델 지문(fingerprint) 계산 |
| 12 | logging (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 실행 로그 |
| 13 | shutil (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 바이너리 탐색(`shutil.which`) |
| 14 | platform (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | CPU-only 폴백 HW 감지, OS 이름 판별 |
| 15 | typing (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | Optional/Callable 등 타입 힌트 |
| 16 | urllib (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | `fituna fetch-corpus`의 HuggingFace dataset-viewer API 호출, `fituna quickstart`의 HuggingFace 모델 검색(`/api/models`) 및 GGUF 다운로드 (`urllib.request`/`urllib.error`/`urllib.parse`) |
| 17 | ctypes (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | Windows `GlobalMemoryStatusEx` 호출로 RAM 조회 (`hardware.py`) |
| 18 | datetime (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 캐시 결과 타임스탬프 기록 (`cache.py`) |
| 19 | io (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 인메모리 버퍼 처리 (`corpus.py` 원자적 쓰기, `mcp_server.py` stdio) |
| 20 | os (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | CPU 코어 수(`os.cpu_count`), 경로 처리, `os.replace` 원자적 쓰기 |
| 21 | stat (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 실행 권한 비트 확인(`binaries.py`), 원자적 쓰기 파일 모드 설정(`quantize.py`) |
| 22 | sys (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | `sys.executable`로 `convert_hf_to_gguf.py` 실행, `mcp_server.py` stdin/stdout, `argv` 처리 |
| 23 | tempfile (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 임시 파일 작성 후 교체(rename)하는 원자적 쓰기 패턴 (여러 모듈) |
| 24 | textwrap (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | `fituna doctor` 출력 포맷팅 (`doctor.py`) |
| 25 | time (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | 탐색 소요 시간 측정 (`search.py`) |
| 26 | shlex (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | `fituna quickstart`가 조립한 `fituna run` 명령을 셸에 그대로 붙여넣을 수 있는 형태로 출력 (`shlex.join`, `quickstart.py`) |
| 27 | http.client (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | `fituna quickstart`의 GGUF 다운로드가 중간에 끊겼을 때 `http.client.IncompleteRead`를 잡아 부분 파일을 남기지 않고 실패시킴 (`quickstart.py`) |
| 28 | tomllib (stdlib, self-check 전용) | 3.11 내장 | PSF License | https://github.com/python/cpython | `__init__.py` 버전-드리프트 self-check(`python -m fituna.__init__`에서만 실행)가 `pyproject.toml` 파싱 — 3.11+ 전용 모듈이지만 설치된 패키지의 런타임 경로에는 없어 하한선을 강제하는 근거는 아님 |
| 29 | unittest.mock (stdlib, self-check 전용) | 3.11 내장 | PSF License | https://github.com/python/cpython | `bench.py`의 assert 기반 self-check(`_self_check()`)가 `subprocess.run`을 모킹 — unittest.mock을 쓰는 유일한 모듈 |
| 30 | contextlib (stdlib, self-check 전용) | 3.11 내장 | PSF License | https://github.com/python/cpython | `cli.py`의 self-check가 `fituna help <없는 명령>`의 종료 코드 2를 검증할 때 그 진단 메시지를 `contextlib.redirect_stderr`로 삼켜 self-check 출력이 OK 한 줄만 남도록 함 |
| 31 | pytest (dev-only) | latest | MIT | https://github.com/pytest-dev/pytest | 테스트(설치 산출물에는 미포함) |
| 32 | llama.cpp (외부 실행 도구, 서브프로세스) | 사용자 빌드 버전 | MIT | https://github.com/ggml-org/llama.cpp | `llama-quantize`/`llama-bench`/`llama-perplexity`/(선택)`convert_hf_to_gguf.py` 실행 — 실제 양자화·벤치마크·perplexity 연산 수행. `llama-cli`·`llama-server`·`llama-imatrix`는 경로 탐색·보고만 하고 실행하지 않음(아래 비고) |
| 33 | nvidia-smi (선택, OS 드라이버 유틸) | 드라이버 종속 | NVIDIA 독점 (연동만, 재배포 없음) | https://developer.nvidia.com | NVIDIA GPU/VRAM 감지 |
| 34 | rocm-smi (선택, OS 드라이버 유틸) | ROCm 종속 | MIT | https://github.com/ROCm/rocm_smi_lib | AMD GPU/VRAM 감지 |
| 35 | system_profiler (선택, macOS 내장) | macOS 종속 | Apple 독점 (연동만, 재배포 없음) | https://www.apple.com | Apple Silicon 통합메모리(VRAM) 감지 |
| 36 | sysctl (선택, macOS/BSD 내장) | macOS 종속 | BSD-3-Clause (연동만, 재배포 없음) | https://github.com/apple-oss-distributions/system_cmds | macOS 전체 RAM(`hw.memsize`) 감지 |

## 비고

- 1~30번은 Python 3.11 표준 라이브러리이며 별도 설치가 필요 없습니다. FiTuna의
  런타임 의존성은 **0개**입니다(`pyproject.toml`의 `dependencies = []`). 이
  중 28번(`tomllib`), 29번(`unittest.mock`), 30번(`contextlib`)은 각각
  `__init__.py`·`bench.py`·`cli.py`의 self-check 전용이며, 설치된 패키지가
  실제로 벤치마크를 수행하는 런타임 경로에서는 쓰이지 않습니다.
- 31번(pytest)은 개발/테스트 전용이며 `pip install fituna`로 설치되는 패키지에는
  포함되지 않습니다 (`pyproject.toml`의 `[project.optional-dependencies].dev`).
- 32~36번은 파이썬 패키지가 아니라 OS PATH 상(또는 `--llama-bin-dir`로 지정한
  경로)에서 subprocess로 호출하는 외부 실행 파일입니다. 소스 코드를 포함하거나
  재배포하지 않으며, 사용자가 자신의 환경에 별도로 설치했다고 가정합니다.
  FiTuna는 이들을 항상 별도 OS 프로세스로 실행하고 표준출력만 파싱합니다.
  자세한 고지는 `THIRD_PARTY_NOTICES.md` 참고.
- 32번 llama.cpp는 단일 저장소이며 빌드 산출물인 여러 바이너리
  (`llama-quantize`, `llama-bench`, `llama-perplexity`, 선택적으로 HF→GGUF
  변환 스크립트)를 하나의 SBOM 항목으로 묶어 표기했습니다 — 모두 동일
  저장소·동일 라이선스(MIT)에서 비롯됩니다. **세 가지**(`llama-cli`,
  `llama-server`, `llama-imatrix`)는 같은 저장소 산출물이지만 **FiTuna가
  실행하지는 않습니다**: `llama-cli`와 `llama-server`는 최종 결과 블록의
  산출물(artifact) 사용법 — `3) terminal chat`(`llama-cli`)과 `1) local API
  server`(`llama-server`) — 에 실제 경로를 넣기 위해 `fituna/report.py`가
  경로만 찾고(`llama-cli`는 `fituna doctor`가 선택 점검 항목으로도 보고),
  `llama-imatrix`는 `fituna/binaries.py`가 경로를 찾아 `fituna list-binaries`가
  출력할 뿐 호출하는 코드 경로가 현재 없습니다. (`THIRD_PARTY_NOTICES.md`,
  `docs/OPEN_SOURCE_USAGE.md`와 동일한 세 항목.)
- 33번(nvidia-smi)과 35번(system_profiler)은 각각 NVIDIA 드라이버 패키지,
  macOS 운영체제에 기본 포함된 독점 유틸리티입니다. 36번(sysctl)은 macOS/BSD
  기본 유틸리티이지만, 상류 소스(`apple-oss-distributions/system_cmds`
  저장소의 `sysctl/sysctl.c`)의 `SPDX-License-Identifier: BSD-3-Clause`
  헤더로 확인된 오픈소스입니다. 셋 다 FiTuna는 호출만 할 뿐 코드를 포함하지
  않으므로 재배포 의무가 발생하지 않습니다. 모두 없을 경우
  `fituna/hardware.py`는 `platform` 모듈 기반 CPU-only `HardwareProfile`로
  자동 폴백합니다.
- `fituna fetch-corpus`(16번, urllib)가 내려받는 코퍼스 자체(WikiText-2,
  Korean Wikipedia)는 사용자 산출물이며 FiTuna 저장소에는 포함되지 않습니다 —
  라이선스 고지는 `THIRD_PARTY_NOTICES.md` §3 참고.
- 위 표의 2~30번(표준 라이브러리 29개)은 `docs/LICENSE_COMPLIANCE.md` §3.4의 AST
  임포트 스캔 결과와 이름 단위로 일치하며(`THIRD-PARTY : NONE`), 배포물
  (sdist·wheel)에 제3자 코드가 없다는 점은 같은 문서 §1에서 실제 빌드 산출물
  파일 목록과 해시 대조로 증명했습니다. 결합 방식별 라이선스 충돌 분석은
  `docs/OPEN_SOURCE_USAGE.md`와 `docs/LICENSE_COMPLIANCE.md` §2를 참고하십시오.
