# SBOM (Software Bill of Materials) — 붙임1

FiTuna의 런타임 파이썬 의존성은 **0개**입니다 (표준 라이브러리만 사용).
아래 표는 사용된 표준 라이브러리 모듈과, 프로세스 형태로 연동하는 외부 실행
도구(파이썬 패키지 아님)를 함께 정리한 것입니다.

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
| 15 | csv (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | llama-bench CSV 출력 파싱(포맷 폴백 대비) |
| 16 | typing (stdlib) | 3.11 내장 | PSF License | https://github.com/python/cpython | Optional/Callable 등 타입 힌트 |
| 17 | pytest (dev-only) | latest | MIT | https://github.com/pytest-dev/pytest | 테스트(설치 산출물에는 미포함) |
| 18 | llama.cpp (외부 실행 도구, 서브프로세스) | 사용자 빌드 버전 | MIT | https://github.com/ggml-org/llama.cpp | `llama-quantize`/`llama-bench`/`llama-perplexity`/(선택)`llama-imatrix`/(선택)`convert_hf_to_gguf.py` 실행 — 실제 양자화·벤치마크·perplexity 연산 수행 |
| 19 | nvidia-smi (선택, OS 드라이버 유틸) | 드라이버 종속 | NVIDIA 독점 (연동만, 재배포 없음) | https://developer.nvidia.com | NVIDIA GPU/VRAM 감지 |
| 20 | rocm-smi (선택, OS 드라이버 유틸) | ROCm 종속 | MIT | https://github.com/ROCm/rocm_smi_lib | AMD GPU/VRAM 감지 |
| 21 | system_profiler (선택, macOS 내장) | macOS 종속 | Apple 독점 (연동만, 재배포 없음) | https://www.apple.com | Apple Silicon 통합메모리(VRAM) 감지 |

## 비고

- 1~16번은 Python 3.11 표준 라이브러리이며 별도 설치가 필요 없습니다. FiTuna의
  런타임 의존성은 **0개**입니다(`pyproject.toml`의 `dependencies = []`).
- 17번(pytest)은 개발/테스트 전용이며 `pip install fituna`로 설치되는 패키지에는
  포함되지 않습니다 (`pyproject.toml`의 `[project.optional-dependencies].dev`).
- 18~21번은 파이썬 패키지가 아니라 OS PATH 상(또는 `--llama-bin-dir`로 지정한
  경로)에서 subprocess로 호출하는 외부 실행 파일입니다. 소스 코드를 포함하거나
  재배포하지 않으며, 사용자가 자신의 환경에 별도로 설치했다고 가정합니다.
  FiTuna는 이들을 항상 별도 OS 프로세스로 실행하고 표준출력만 파싱합니다.
  자세한 고지는 `THIRD_PARTY_NOTICES.md` 참고.
- 18번 llama.cpp는 단일 저장소이며 빌드 산출물인 여러 바이너리
  (`llama-quantize`, `llama-bench`, `llama-perplexity`, 선택적으로
  `llama-imatrix`와 HF→GGUF 변환 스크립트)를 하나의 SBOM 항목으로 묶어
  표기했습니다 — 모두 동일 저장소·동일 라이선스(MIT)에서 비롯됩니다.
- 19번(nvidia-smi)과 21번(system_profiler)은 각각 NVIDIA 드라이버 패키지,
  macOS 운영체제에 기본 포함된 독점 유틸리티입니다. FiTuna는 이를 호출만 할
  뿐 코드를 포함하지 않으므로 재배포 의무가 발생하지 않습니다. 두 도구 모두
  없을 경우 `fituna/hardware.py`는 `platform` 모듈 기반 CPU-only
  `HardwareProfile`로 자동 폴백합니다.
