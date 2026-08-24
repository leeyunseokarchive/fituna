<div align="center">

**한국어** | [English](README.en.md)

<img src="assets/logo.png" width="160" alt="FiTuna 로고 — 아기 참치 캐릭터">

# FiTuna

**llama.cpp 설정, 추측하지 말고 측정하세요.**

모델 파일과 목표 속도(tok/s), 허용 품질손실(%)을 입력하면, 내 기기에서
실제로 그 수치를 달성하는 가장 가벼운 llama.cpp 설정 — 양자화 레벨,
GPU 오프로드, 컨텍스트 길이의 조합 — 을 실측 벤치마크로 찾아 줍니다.

**`pip install fituna`**

[![CI](https://github.com/leeyunseokarchive/fituna/actions/workflows/ci.yml/badge.svg)](https://github.com/leeyunseokarchive/fituna/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/fituna.svg)](https://pypi.org/project/fituna/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Zero dependencies](https://img.shields.io/badge/runtime%20deps-0-brightgreen.svg)](docs/SBOM.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**심사위원 · 검증기관용 한국어 재현 가이드 → [REVIEWERS.md](REVIEWERS.md)**

![실제 fituna 실행: Apple M3 Pro에서 다운로드부터 llama-server 명령 출력까지 58초](assets/demo.svg)

</div>

## 왜 필요한가

llama.cpp로 로컬 LLM을 돌리려면 세 가지를 골라야 합니다. 모델을 얼마나
압축할지(양자화 레벨, Q2–Q8 — 낮을수록 빠르지만 품질이 떨어집니다),
모델의 레이어 몇 개를 GPU에 올릴지(`-ngl`), 대화 맥락을 얼마나 길게
잡을지(컨텍스트 길이). 조합은 수십 가지인데, 지금은 대부분 하나씩 돌려
보며 감으로 찾습니다. 기존 도구들도 이 문제를 절반만 풉니다:

| 기존 방법 | 한계 |
|---|---|
| Ollama · LM Studio | 모델별 고정 프리셋을 적용할 뿐, 내 목표에 맞춰 주지 않음. 세밀한 양자화 제어 요청은 ["Closed as not planned"](https://github.com/ollama/ollama/issues/14674)로 닫힘 |
| NVIDIA AutoQuantize | CUDA 전용 — Apple Silicon에서는 쓸 수 없음 |
| VRAM 계산기 · 챗봇 조언 | 사양표 기반 추정 — 내 기기의 발열, 메모리 대역폭, llama.cpp 빌드 옵션까지는 모름 |

그리고 실제로 재 보면 직관은 자주 뒤집힙니다. Apple M3 Pro 실측에서
"당연히 가장 좋을" Q8_0이 속도 목표에서 탈락했고, 정답은 양자화 하나가
아니라 **Q4_K_M에 최소 오프로드 `-ngl 33`을 더한 조합**이었습니다. 이런
답은 사양표를 아무리 들여다봐도 나오지 않습니다.

## 2분 체험

정말 되는지 직접 확인하는 가장 빠른 길입니다. 258 MB짜리 작은 모델로
전체 파이프라인(다운로드 → 양자화 → 품질 게이트 → 벤치마크)이 1분
남짓에 끝납니다:

```bash
pip install fituna            # Python 3.11+ 가상환경에 (macOS 시스템 python3는 3.9)
brew install llama.cpp        # 엔진. 다른 플랫폼은 소스 빌드 (아래 '설치' 참고)
fituna fetch-corpus --lang en --out wiki.txt
fituna run --hf bartowski/SmolLM2-135M-Instruct-GGUF \
  --target-tps 240 --max-quality-loss 5 --ctx 2048 --wikitext wiki.txt --out ./out
```

위 명령을 그대로 M3 Pro에서 실행하면 **58초** 만에 `MEETS TARGET —
Q8_0 @ ngl=24, 249.16 tok/s, 손실 0.29%`라는 판정과 함께, 복사해서 바로
쓸 수 있는 `llama-server` 명령이 출력됩니다. 같은 명령을 `--resume`으로
다시 돌리면 캐시에서 **0.8초** 만에 같은 답이 나옵니다.

## 실측 결과

크기가 다른 세 모델에 각각 목표를 걸고 탐색한 결과입니다. 세 번 모두
"가장 무난한 선택"이라던 Q8_0이 속도 목표에서 탈락했습니다:

| 모델 | 목표 | "당연한" 선택의 실측 | FiTuna가 찾은 답 |
|---|---|---|---|
| Qwen3-4B-Instruct | 30 tok/s, ≤5% 손실 | Q8_0: 24.22 tok/s ❌ (품질도 Q6_K보다 나쁘게 측정) | **Q4_K_M @ ngl=33 → 30.81 tok/s, 1.73%** ✅ |
| SmolLM2-135M | 240 tok/s, ≤5% 손실 | Q8_0: 205.91 tok/s ❌ | **Q6_K → 249.50 tok/s, 0.53%** ✅ (더 작은 Q4_K_M이 더 느린 역전 실측) |
| Midm-2.0-Mini (한국어) | 40 tok/s, ≤5% 손실 | Q8_0: 34.26 tok/s ❌ | **Q4_K_M @ ngl=48 → 44.62 tok/s, 2.58%** ✅ |

Apple M3 Pro, llama.cpp build 9960. 전체 로그·재실행 변동성 분석:
[docs/RESULTS.md](docs/RESULTS.md) · 사용 시나리오:
[docs/USE_CASES.md](docs/USE_CASES.md) · NVIDIA/Linux 재현(무료 T4):
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leeyunseokarchive/fituna/blob/main/notebooks/colab_nvidia_verification.ipynb)

## 챗봇에게 물어보면 되지 않나?

당연한 반문이라, 실제로 실험했다. FiTuna의 실측 시나리오 3건과 동일한
질문을 챗봇(Claude, 프로젝트 정보가 없는 새 세션)에게 그대로 묻고, 답변
전문을 기록한 뒤 실측값과 대조했다 — **세 번 모두 챗봇의 1순위 추천이
실측에서 목표 미달이었다**:

| 시나리오 · 목표 | 챗봇 추천 · 예측 | 같은 설정의 실측 | 실측이 찾은 답 |
|---|---|---|---|
| Qwen3-4B · 30 tok/s | Q5_K_M — "35~45 예상" | **29.59 미달**¹ | Q4_K_M @ ngl=33 → 30.81 ✅ |
| SmolLM2 · 240 tok/s | Q8_0 — "여유 있게 넘김" | **205.91 미달** | Q6_K → 249.50 ✅ |
| Midm(한국어) · 40 tok/s | Q6_K — "50~70 예상", "Q4_K_M 피하라" | **38.96 미달**¹ | **피하라던 Q4_K_M** @ ngl=48 → 44.62 ✅ |

¹ 1 tok/s 안팎의 경계선 판정 — 단, 예측 수치의 30%+ 괴리는 마진 문제가 아니다.

세 답변 모두 `-ngl 99`(전량 오프로드)를 권했고 — "목표를 만족하는 최소
오프로드"라는 개념은 실측 없이 존재할 수 없다 — 셋 다 정직하게 "직접
`llama-bench`로 재보라"로 끝났다. **FiTuna가 바로 그 실측이다.** 질문·답변
전문과 방법·한계(챗봇 응답의 세션별 변동 포함):
[docs/CHATBOT_COMPARISON.md](docs/CHATBOT_COMPARISON.md)

실측 없이 알 수 없는 게 무엇인지는 오프로드 곡선이 가장 잘 보여준다.
층 하나 차이로 목표 통과와 탈락이 갈리고, 절반을 올리면 속도는 절반이
아니라 4분의 1이 된다:

![Midm-2.0-Mini Q4_K_M의 GPU 오프로드 층수별 실측 생성 속도 곡선 — 층 1개 차이로 목표 통과와 탈락이 갈린다](assets/ngl-curve.svg)

## 동작 원리

```mermaid
flowchart LR
    A["입력<br/>F16 GGUF<br/>목표 tok/s · 품질예산 %"] --> B["1단계 · 품질 실측<br/>전 후보 양자화 후<br/>perplexity 측정"]
    B --> C{"품질<br/>게이트"}
    C -->|"탈락 (조기종료 A)"| X["다음 후보"]
    C -->|"통과 · 실측 품질순 정렬"| D["2단계 · 속도 실측<br/>llama-bench"]
    D --> E{"풀오프로드로<br/>목표 도달?"}
    E -->|"미달 (조기종료 B)"| X
    E -->|도달| F["ngl 이진탐색<br/>최소 오프로드 확정"]
    F --> G["산출물<br/>양자화 .gguf +<br/>llama-server 명령"]
    B -.실측값 저장.-> H[("sqlite3 캐시<br/>--resume < 1초")]
    D -.-> H
```

FiTuna는 두 단계로 움직입니다. 1단계에서 **모든** 후보를 양자화해 품질
손실을 먼저 재는데, 측정하지 않은 숫자로는 후보를 줄 세울 수 없기
때문입니다. 2단계는 그 실측 품질 순서대로 속도를 재고, 목표를 놓친
후보는 추가 벤치마크 없이 바로 버립니다. 모든 측정값은 sqlite3에
캐시되며, 캐시 키에 llama.cpp 빌드 버전까지 들어가므로 엔진을 업그레이드한
뒤 예전 수치를 잘못 재사용하는 일이 없습니다. 알고리즘 상세:
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 설치

```bash
pip install fituna
```

Python 3.11+ 필요(macOS 시스템 `python3`는 3.9 — `python3.13 -m venv`로
가상환경을 먼저). 런타임 의존성은 없습니다. 엔진인 llama.cpp도 필요합니다:

```bash
brew install llama.cpp        # macOS/Linux Homebrew
```

<details>
<summary><b>소스 빌드 · 개발 설치</b></summary>

```bash
# llama.cpp 소스 빌드 (모든 플랫폼, NVIDIA는 -DGGML_CUDA=ON 추가)
git clone https://github.com/ggml-org/llama.cpp
cmake -S llama.cpp -B llama.cpp/build && cmake --build llama.cpp/build --config Release
# 이후 fituna 명령에 --llama-bin-dir llama.cpp/build/bin 추가

# FiTuna 개발 설치
git clone https://github.com/leeyunseokarchive/fituna
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e fituna
```

</details>

## 명령어

처음이라면 `fituna quickstart`가 가장 쉽습니다 — 아래 명령들을 몰라도
마법사가 환경 점검부터 탐색 실행까지 순서대로 안내합니다. 각 명령의 전체
옵션은 `fituna <명령> -h`로 볼 수 있습니다.

| 명령 | 역할 |
|---|---|
| `fituna quickstart` | 6단계 대화형 마법사 — 환경 점검부터 탐색 실행까지. 조립한 `fituna run` 명령을 실행 전에 보여줌 |
| `fituna run` | 탐색 본체. `--model <F16.gguf>` 또는 `--hf repo[:file]`(HF에서 자동 다운로드), `--json` 지원 |
| `fituna doctor` | 환경 9개 항목 점검. 실패마다 해결 명령 제시 |
| `fituna fetch-corpus` | 품질 측정용 코퍼스 다운로드 (`--lang en/ko`, 표준 라이브러리만 사용) |
| `fituna detect-hw` | GPU·VRAM·CPU·RAM 자동 감지 결과 확인 |
| `fituna-mcp` | AI 에이전트용 MCP 서버 (아래 참고) |

<details>
<summary><b>품질 측정 코퍼스 고르기</b> — 같은 quant도 언어에 따라 2~3배 다른 손실</summary>

품질손실은 텍스트 코퍼스에 대한 perplexity 증가율이므로, 실제 사용할
텍스트와 비슷할 때만 의미가 있습니다. UTF-8 파일이면 무엇이든 됩니다
(`--quality-corpus`):

```bash
fituna fetch-corpus --lang en --out wikitext-2-raw-test.txt        # wikitext-2
fituna fetch-corpus --lang ko --out kowiki-corpus.txt --rows 500   # 한국어 위키백과
```

Run 3에서는 코퍼스만 바꿔도 도구의 판정이 바뀌었습니다
([실측과 단서 조항](docs/RESULTS.md#run-3--english-vs-korean-quality-corpus-same-model-same-quants)).
두 프리셋 모두 CC BY-SA 3.0이며 다운로드 완료 시 라이선스 고지를 출력합니다.

</details>

<details>
<summary><b>디스크 사용량 · 캐시</b></summary>

탐색은 품질 단계에 도달한 모든 후보를 양자화합니다 — 4B 모델의 후보 4개
기준 약 12 GB. 파일은 재실행 시 재사용되고 `--quant`로 후보를 좁혀 용량을
제한할 수 있습니다. 결과는 모델 지문 × 하드웨어 × llama.cpp 빌드 버전을
키로 sqlite3에 캐시되며, `--resume`은 1초 미만으로 재응답합니다.

</details>

<details>
<summary><b>라이브러리로 사용</b></summary>

런타임 의존성이 없어 모듈을 바로 임포트할 수 있습니다:

```python
from fituna.hardware import detect_hardware

hw = detect_hardware()
print(f"{hw.gpu_vendor.value}: {hw.gpu_name}, {hw.vram_mb} MB VRAM")
# apple: Apple M3 Pro, 18432 MB VRAM
```

탐색 자체는 `fituna.search.search()`를 호출하면 됩니다 — 필요한
`ModelInfo`·`BinaryPaths`·코퍼스 경로는 `fituna run`이 조립해 주는 것과
같습니다 ([search.py](fituna/search.py), [config.py](fituna/config.py)).

</details>

## MCP 서버 — AI 에이전트에게 실측 답변을

챗봇에게 "내 컴퓨터에 맞는 로컬 모델 설정"을 물으면 사양표에서 추측한
답이 돌아옵니다. FiTuna의 MCP 서버를 연결하면 에이전트가 추측 대신 실측
결과를 받아 갑니다:

```bash
claude mcp add fituna -- fituna-mcp      # stdio를 지원하는 모든 MCP 클라이언트
```

| 도구 | 반환 |
|---|---|
| `fituna_detect_hardware` | GPU 벤더·이름, VRAM, CPU 코어, RAM |
| `fituna_recommend` | 실측 탐색 결과 — 승자 설정, 실측 tok/s·품질손실, 실행 명령. 재요청 ~1초(캐시) |

외부 SDK 없이 표준 라이브러리로 구현한 JSON-RPC 2.0/stdio입니다
([mcp_server.py](fituna/mcp_server.py)).

## 범위와 한계

FiTuna는 **추천까지만** 합니다. 산출물은 탐색 중에 이미 만들어진 양자화
`.gguf` 파일과 복사해 쓰는 `llama-server`/`llama-cli` 명령이고
(`--export-ollama`를 주면 Ollama Modelfile도 함께), 모델을 실제로 띄우는
일은 llama.cpp에 맡깁니다([설계 근거](docs/ARCHITECTURE.md#why-this-shape)).
현재의 한계는 다음과 같습니다:

- **단일 GPU만 지원** — `--tensor-split` 없음 ([#11](https://github.com/leeyunseokarchive/fituna/issues/11), 멀티 GPU 기기 제공 환영)
- **Windows AMD 자동 감지 불가** — `--gpu amd --vram-mb <N>`으로 수동 지정
- **품질 = 선택한 코퍼스의 perplexity** — 대리 지표. 실제 작업과 비슷한 텍스트로 측정할 것
- **판정은 `--ppl-chunks`에 의존** — 예산에 가까운 후보는 재측정 후 신뢰 ([#8](https://github.com/leeyunseokarchive/fituna/issues/8), [측정된 영향](docs/RESULTS.md#how-big-is-a-perplexity-gap-the-error-bar-we-had-been-discarding))
- **벤치마크는 발열에 민감** — 목표와 몇 tok/s 차이의 판정은 경계선 ([변동성 분석](docs/RESULTS.md#run-to-run-variance-measured-not-hidden))
- **실기 E2E는 macOS·Linux** — Windows는 단위테스트·CI까지 ([#12](https://github.com/leeyunseokarchive/fituna/issues/12))

## 기여하기

코드베이스는 작고 의존성이 없으며 계약 우선으로 설계됐습니다 —
[fituna/config.py](fituna/config.py)에서 시작하세요. 유닛 테스트 256개와
3-OS × 2-Python CI가 지킵니다. 로드맵:
[v0.3.0 마일스톤](https://github.com/leeyunseokarchive/fituna/milestone/1) ·
[good first issue #10](https://github.com/leeyunseokarchive/fituna/issues/10) ·
[CONTRIBUTING.md](CONTRIBUTING.md) · [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

## 라이선스

[MIT](LICENSE) © FiTuna contributors ·
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) · [SBOM](docs/SBOM.md) ·
[오픈소스 활용](docs/OPEN_SOURCE_USAGE.md) ·
[AI 활용 개발 공개](docs/AI_MODEL_USAGE.md) · [CHANGELOG.md](CHANGELOG.md) ·
[SECURITY.md](SECURITY.md)
