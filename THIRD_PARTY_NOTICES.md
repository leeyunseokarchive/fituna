# 제3자 구성요소 고지

FiTuna 자체 소스 코드는 MIT License로 배포합니다(`LICENSE` 참조). FiTuna는
**제3자 소스 코드나 바이너리를 vendor 방식으로 포함하거나, 묶어서 배포하거나,
재배포하지 않습니다.** Python 런타임 의존성은 **0개**이며 Python 3.11 표준
라이브러리만 사용합니다. 전체 모듈 목록은 `docs/SBOM.md`에서 확인할 수 있습니다.

다만 실행 중에는 **외부 프로그램을 subprocess로 호출**하고 사용자에게 외부
데이터 파일을 요구할 수 있습니다. 이 문서는 각 라이선스 조건에 따라 해당 외부
구성요소와 라이선스, FiTuna가 사용하는 방식을 정확히 기록합니다.

---

## 1. llama.cpp(필수, subprocess로 실행)

- **프로젝트**: https://github.com/ggml-org/llama.cpp
- **라이선스**: MIT License, Copyright (c) 2023-2026 The ggml authors
- **FiTuna의 사용 방식**: FiTuna는 양자화, 추론, 벤치마크를 직접 구현하지
  않습니다. **사용자가 미리 설치**하고 `PATH` 또는 `--llama-bin-dir`로 지정한
  llama.cpp 실행 파일을 Python `subprocess` 모듈로 호출합니다
  (`fituna/binaries.py:locate_binaries`):
  - `llama-quantize` — F16/F32 기반 GGUF를 양자화된 GGUF로 변환
    (`fituna/quantize.py`)
  - `llama-bench` — prompt·생성 처리량 측정
    (`fituna/bench.py`)
  - `llama-perplexity` — 기준 모델 대비 품질 손실 측정
    (`fituna/quality.py`)
  - HF→GGUF `convert_hf_to_gguf.py` 스크립트(선택) — HF 형식 모델
    디렉터리를 F16 기반 GGUF로 변환
    (`fituna/model_info.py:ensure_base_gguf`)

  llama.cpp 산출물 세 개는 FiTuna가 **위치만 찾고 실행하지 않습니다.**
  `llama-cli`와 `llama-server`는 출력 결과의 명령에 실제 경로를 넣기 위해
  `fituna/report.py:_find_llama_cli`와 `_find_llama_server`에서만 찾습니다.
  `llama-cli`는 `fituna doctor`의 선택 점검 항목에도 표시됩니다.
  `llama-imatrix`는 `fituna/binaries.py:locate_binaries`가 찾아
  `fituna list-binaries`에서 출력하지만, 현재 이를 실행하는 코드 경로는 없습니다.

  FiTuna는 필요한 도구를 별도 OS process로 시작하고 stdout, stderr, 종료 코드를
  해석할 뿐입니다. **이 저장소에는 llama.cpp 소스 파일이나 컴파일된 바이너리를
  복사하거나 함께 packaging하거나 배포하지 않습니다.** 필수 바이너리를 찾지
  못하면 조용히 실패하지 않고 `locate_binaries()`가 upstream 빌드 안내를 담은
  `BinaryNotFoundError`를 발생시킵니다.

### MIT License 원문(llama.cpp)

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

이 저장소에 llama.cpp 코드가 실제로 들어 있지는 않지만, MIT License의 고지
보존 조건을 충족하도록 전문을 그대로 실었습니다. FiTuna는 별도로 설치된
llama.cpp만 호출합니다.

---

## 2. 하드웨어 감지 CLI(선택, subprocess로 실행)

`fituna/hardware.py:detect_hardware()`는 vendor가 제공한 시스템 utility를
실행해 GPU vendor와 VRAM을 자동 감지합니다. 이 도구들은 프로젝트 의존성이
아니라 OS·driver 구성요소이며 FiTuna에 포함되지 않습니다. 해당 도구가 없으면
표준 라이브러리 `platform` 모듈을 이용한 CPU 전용 정보로 자동 전환합니다.

| 도구 | Vendor / 출처 | 라이선스 | FiTuna의 사용 방식 |
|---|---|---|---|
| `nvidia-smi` | NVIDIA driver package에 포함 | NVIDIA 독점 라이선스(FiTuna가 재배포하지 않고 호출만 함) | NVIDIA GPU 이름과 VRAM 조회 |
| `rocm-smi` | ROCm (https://github.com/ROCm/rocm_smi_lib) | MIT | AMD GPU 이름과 VRAM 조회 |
| `system_profiler` | macOS에 포함 | Apple 독점 라이선스(FiTuna가 재배포하지 않고 호출만 함) | Apple Silicon 통합 메모리 조회 |
| `sysctl` | macOS / BSD 기본 시스템에 포함 | BSD-3-Clause (`apple-oss-distributions/system_cmds/sysctl/sysctl.c`; FiTuna가 재배포하지 않고 호출만 함) | macOS의 전체 RAM(`hw.memsize`) 조회 |

---

## 3. Perplexity 평가 corpus(사용자 제공 입력, 미포함)

`fituna/quality.py`가 `llama-perplexity`에 넣을 텍스트 corpus
(`--quality-corpus`)가 필요합니다. FiTuna는 **corpus를 포함하지 않습니다.**
사용자가 요청하면 `fituna fetch-corpus`(`fituna/corpus.py`, 표준 라이브러리
`urllib`만 사용)가 HuggingFace 공개 dataset-viewer API에서 두 프리셋 중 하나를
다운로드합니다.

- **영어 기본값 — WikiText-2(raw), test split**:
  https://huggingface.co/datasets/Salesforce/wikitext
  (`Salesforce/wikitext`, config `wikitext-2-raw-v1`)
- **한국어 — Wikipedia, train split**:
  https://huggingface.co/datasets/wikimedia/wikipedia
  (`wikimedia/wikipedia`, config `20231101.ko`)
- **라이선스(둘 다)**: CC BY-SA 3.0이며 GFDL로도 이중 라이선스됩니다. 저작자
  표시와 동일조건변경허락 의무가 적용됩니다. 추정하지 않고 각 데이터셋의
  HuggingFace metadata(`cardData.license`)에서 직접 확인했습니다.
- **FiTuna의 사용 방식**: `fetch-corpus`는 다운로드한 텍스트를 사용자가 선택한
  `--out` 경로에 한 번 저장합니다. 그다음부터 `fituna/quality.py`가 읽기 전용으로
  열어 `llama-perplexity -f <corpus_path>`에 그대로 전달합니다. FiTuna가 이
  파일을 함께 묶거나 수정하거나 재배포하지 않습니다. 모든 문서 예시가 따르는
  관례대로 `.gitignore`는 `.txt`로 끝나는 `--out` 경로를 저장소에서 제외하며,
  사용자가 corpus를 따로 받거나 제공합니다(`README.md`의 빠른 시작 참조).

---

## 4. 조정 대상 LLM weight(실행 시 사용자 제공, 미포함)

사용자가 `fituna run`에 전달하는 `--model`은 **사용자가** Hugging Face 등에서
별도로 구한 모델(GGUF 파일 또는 HF 형식 디렉터리)을 가리킵니다. FiTuna는 모델
weight를 내장하거나 fine-tuning·재학습·재배포하지 않습니다. 사용자 디스크에
있는 사본을 위 llama.cpp subprocess로 양자화하고 벤치마크할 뿐입니다. 모델마다
별도 라이선스가 있으며 이를 준수할 책임은 사용자에게 있습니다. 실행별 공개
양식은 `docs/AI_MODEL_USAGE.md`를 참고하세요.

---

## 5. 개발 전용 의존성(설치 package에는 미포함)

- **pytest** — https://github.com/pytest-dev/pytest — MIT License.
  `pip install fituna[dev]` 환경에서 `tests/`의 test suite를 실행할 때만
  사용합니다. `pyproject.toml`의 `[project.optional-dependencies].dev`에
  선언되어 있으며, 설치된 `fituna` package의 의존성이 **아닙니다.**

---

## 요약

| # | 구성요소 | 라이선스 | 저장소 포함 여부 | 호출 방식 |
|---|---|---|---|---|
| 1 | llama.cpp (`llama-quantize`, `llama-bench`, `llama-perplexity`, 변환 스크립트) | MIT | 아니요 | `subprocess` |
| 1 | llama.cpp (`llama-cli`, `llama-server`, `llama-imatrix`) | MIT | 아니요 | 위치 확인·보고만 하며 실행하지 않음 |
| 2 | `nvidia-smi` | NVIDIA 독점 라이선스 | 아니요 | `subprocess`(선택) |
| 2 | `rocm-smi` | MIT | 아니요 | `subprocess`(선택) |
| 2 | `system_profiler` | Apple 독점 라이선스 | 아니요 | `subprocess`(선택) |
| 2 | `sysctl` | BSD-3-Clause | 아니요 | `subprocess`(선택) |
| 3 | WikiText-2(영어)와 한국어 Wikipedia corpus | CC BY-SA 3.0 / GFDL | 아니요 | 파일 입력으로 읽음 |
| 4 | 사용자가 선택한 LLM weight | 모델마다 다름 | 아니요 | 파일 입력으로 읽음 |
| 5 | pytest(개발 전용) | MIT | 아니요(선택 개발 의존성) | 런타임에 호출하지 않음 |

FiTuna가 사용하는 Python 표준 라이브러리 모듈 목록은 `docs/SBOM.md`, 각
오픈소스 구성요소의 사용 영역과 라이선스 확인 방법은
`docs/OPEN_SOURCE_USAGE.md`, 위 구성요소를 재배포하지 않는다는 실행 검사와
빌드 산출물 근거는 `docs/LICENSE_COMPLIANCE.md`, FiTuna 자체 라이선스(MIT)는
`LICENSE`에서 확인할 수 있습니다.
