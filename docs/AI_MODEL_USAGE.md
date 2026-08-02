# AI 모델 활용 명세 — 붙임2

FiTuna 자체는 AI 모델을 내장·배포·파인튜닝·재학습하지 않는
**오케스트레이션 도구**입니다. 사용자가 실행 시점에 `--model`로 지정하는
기존 공개 모델(예: SmolLM2-135M-Instruct, Qwen3-4B-Instruct-2507,
Midm-2.0-Mini-Instruct 등)을
GGUF로 변환하고 양자화·벤치마크할 뿐, 특정 모델의 가중치를 저장소에
포함하거나 코드에 고정하지 않습니다. 붙임2가 구분하는 세 가지 AI 활용
유형(① 외부 모델 그대로 활용 ② 외부 모델 파인튜닝 ③ 자체 학습) 중 FiTuna
자체에 해당하는 것은 없습니다 — 아래 "활용 유형"은 FiTuna가 아니라
**FiTuna를 실행하는 사용자가 선택한 모델**의 활용 방식을 기준으로 작성되며,
아래는 (A) 재사용 가능한 빈 템플릿과 (B) 본 프로젝트의 시연·검증에 실제
사용한 모델 3개(Apache-2.0 2개, MIT 1개)를 채운 예시로 구성됩니다.

## A. 활용 명세 템플릿 (모델 선택 시마다 채워서 사용)

| 항목 | 내용 |
|------|------|
| 활용 유형 | 1. 외부 모델 그대로 활용 (FiTuna는 파인튜닝·재학습·증류를 수행하지 않고, 사용자가 지정한 기존 공개 모델의 GGUF 변환·양자화·벤치마크만 수행) |
| 기반 모델명 | (실행 시점에 `fituna run --model <경로>`로 지정한 모델명을 기재) |
| 기반 모델 라이선스 | (해당 모델의 공식 라이선스를 기재. 모델마다 상이하므로 다운로드 전 반드시 라이선스 페이지 확인) |
| 가중치 출처 URL | (실제 다운로드한 Hugging Face/공식 배포처 URL 기재) |
| FiTuna 소스 코드 라이선스 | MIT (본 저장소 `LICENSE` 참고, OSI 인증, 비상업적 이용 제한 없음) |
| FiTuna의 모델 관여 범위 | 가중치를 수정하지 않음. `llama-quantize`로 정밀도만 낮추고(GGUF 양자화), `llama-bench`/`llama-perplexity`로 처리량과 품질손실(perplexity 증가율)을 측정. 학습·파인튜닝·증류·가중치 병합 없음 |
| 상용 AI 보조 도구 활용 범위 | (본 프로젝트 개발 과정에서 사용한 상용 AI 코딩 보조 도구가 있다면 이름과 활용 범위를 구체적으로 기재. 아래 B절 참고) |

## B. 시연·검증 모델 활용 명세 (작성 예시 — 실제 값, 3건)

본 프로젝트가 시연·검증에 실제로 사용한 모델은 아래 세 개이며, 모두 OSI
승인 permissive 라이선스(Apache License 2.0 2건, MIT 1건)로 상업적 이용
제한이 없습니다. 라이선스는
HuggingFace API(`cardData.license`)로 2026-07-30에 직접 재확인했습니다
(원본·GGUF 저장소 모두; `docs/OPEN_SOURCE_USAGE.md` §3–4 참고).

### B-1. HuggingFaceTB/SmolLM2-135M-Instruct — 라이브 탐색 시연

`docs/DEMO_SCRIPT.md`의 시연 커맨드(`fituna run --model
SmolLM2-135M-Instruct-f16.gguf --target-tps 240 --max-quality-loss 5
--ctx 4096 --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M ...`)에서 실제로 사용한 모델
기준입니다. 콜드 탐색이 약 76초로 짧아 3분 시연 영상에 실시간으로 담을 수
있는 소형 모델로 선택했습니다.

| 항목 | 내용 |
|------|------|
| 활용 유형 | 1. 외부 모델 그대로 활용 |
| 기반 모델명 | HuggingFaceTB/SmolLM2-135M-Instruct (실제 다운로드한 GGUF: `bartowski/SmolLM2-135M-Instruct-GGUF`) |
| 기반 모델 라이선스 | Apache License 2.0 — HuggingFace API `cardData.license: apache-2.0`으로 원본·GGUF 두 저장소 모두 확인(2026-07-30). 특허·표시 조건은 있으나 상업적 이용·수정·배포 제한이 없는 OSI 승인 permissive 라이선스 |
| 가중치 출처 URL | https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct (다운로드한 GGUF: https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF) |
| FiTuna 소스 코드 라이선스 | MIT (본 저장소 `LICENSE` 참고, OSI 인증, 비상업적 이용 제한 없음) |
| FiTuna의 모델 관여 범위 | 가중치를 수정하지 않음. `llama-quantize`로 Q8_0/Q6_K/Q5_K_M/Q4_K_M을 생성하고 `llama-bench`(tok/s)·`llama-perplexity`(wikitext-2 기준 품질손실 %)로 측정해 목표를 만족하는 최소 자원 조합(quant/ngl/ctx)만 탐색·보고 (실측값: `docs/RESULTS.md` Run 1·4). 학습·파인튜닝·증류·가중치 병합 없음 |
| 상용 AI 보조 도구 활용 범위 | 코드 스캐폴딩(모듈 골격, argparse 서브커맨드 구조), 리팩터링, 문서(README/ARCHITECTURE 등) 초안 작성 보조에 Claude Code(Anthropic)를 사용. 핵심 탐색 알고리즘(품질 우선 필터 → ngl 이진탐색 조기종료 로직) 설계, 인터페이스 계약(`fituna/config.py`) 정의, 최종 코드 검증·테스트 작성 및 채택 여부 판단은 개발자가 직접 수행 |

### B-2. Qwen/Qwen3-4B-Instruct-2507 — 보고서 주 결과

`docs/RESULTS.md` Run 2/3(및 Colab 노트북의 선택적 4B 셀)에서 실제로
사용한 모델 기준입니다. 탐색에 10분 이상 걸려 시연 영상에는 결과 화면만
짧게 노출하고, 정식 실측 결과는 `docs/RESULTS.md`에 기록했습니다.

| 항목 | 내용 |
|------|------|
| 활용 유형 | 1. 외부 모델 그대로 활용 |
| 기반 모델명 | Qwen/Qwen3-4B-Instruct-2507 (실제 다운로드한 GGUF: `unsloth/Qwen3-4B-Instruct-2507-GGUF`) |
| 기반 모델 라이선스 | Apache License 2.0 — HuggingFace API `cardData.license: apache-2.0`으로 원본·GGUF 두 저장소 모두 확인(2026-07-30) |
| 가중치 출처 URL | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 (다운로드한 GGUF: https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF) |
| FiTuna 소스 코드 라이선스 | MIT |
| FiTuna의 모델 관여 범위 | 위와 동일한 절차(`llama-quantize`/`llama-bench`/`llama-perplexity`)를 4B급 모델에 적용 — 실측 품질·속도 모두에서 Q8_0이 Q6_K에 밀리는 역전 사례를 포함해 `docs/RESULTS.md` Run 2에 기록. 최종 채택 조합은 Q4_K_M, ngl=33(전체 오프로드가 아닌 최소 자원). 학습·파인튜닝·증류·가중치 병합 없음 |
| 상용 AI 보조 도구 활용 범위 | B-1과 동일 (프로젝트 공통 개발 관행) |

### B-3. K-intelligence/Midm-2.0-Mini-Instruct — 한국어 오픈웨이트 모델 실측

`docs/RESULTS.md` Run 5에서 사용한 모델입니다. 한국어 코퍼스로 품질을
평가하는 `--quality-corpus` 경로를 한국어 모델에 실제로 적용한 사례이며,
저장소에 기록된 세 번째 실측 대상 모델입니다.

| 항목 | 내용 |
|------|------|
| 활용 유형 | 1. 외부 모델 그대로 활용 |
| 기반 모델명 | K-intelligence/Midm-2.0-Mini-Instruct (2.3B, KT Corporation. 실제 다운로드한 GGUF: `mykor/Midm-2.0-Mini-Instruct-gguf`) |
| 기반 모델 라이선스 | MIT License — HuggingFace API `cardData.license: mit`으로 원본·GGUF 두 저장소 모두 확인, 원본 저장소의 `LICENSE.txt` 전문(“Copyright (c) 2025 KT Corporation”)도 직접 대조(2026-07-30). 두 저장소 모두 gated 아님 |
| 가중치 출처 URL | https://huggingface.co/K-intelligence/Midm-2.0-Mini-Instruct (다운로드한 GGUF: https://huggingface.co/mykor/Midm-2.0-Mini-Instruct-gguf) |
| FiTuna 소스 코드 라이선스 | MIT |
| FiTuna의 모델 관여 범위 | B-1·B-2와 동일한 절차를 한국어·영어 두 코퍼스에 각각 적용. 목표 40 tok/s에서 통념상 최선인 Q8_0이 34.26 tok/s로 미달하고 Q4_K_M(ngl=48)이 44.62 tok/s로 목표를 충족한 결과를 `docs/RESULTS.md` Run 5에 기록. 학습·파인튜닝·증류·가중치 병합 없음 |
| 상용 AI 보조 도구 활용 범위 | B-1과 동일 (프로젝트 공통 개발 관행) |

> 참고: 한국어 오픈웨이트 모델 후보 조사에서 EXAONE 4.0 계열은 라이선스
> 원문이 상업적 이용을 명시적으로 금지하고, Kanana-나노(kanana-nano, 이번에
> 검토한 모델)는 CC BY-NC 4.0(비상업, OSI 미승인)이므로 제외했습니다 — 이후
> 나온 Kanana-2 계열(`kanana-open-license`)은 재배포·상업 이용을 허용하는
> 별도 라이선스이며 이 배제 사유가 적용되지 않습니다. 대회 운영규정 제9조는
> 오픈웨이트를 최소 요건으로 두지만, 재배포·상업 이용까지 제약이 없는 모델을
> 택했습니다.

## 작성 안내

- 대회 제출 시 A절 템플릿을 실제로 사용/시연한 모델 기준으로 채운 표
  (B절과 같은 형태)가 최소 1개 이상 포함되어야 하며, 플레이스홀더
  상태(괄호 안내문)로만 제출하는 것은 금지됩니다. 본 문서는 B절에 그
  예시 3건(B-1, B-2, B-3)을 이미 채워 두었습니다.
- 여러 모델로 시연했다면 B절 형태의 표를 모델별로 추가하십시오.
- 모델별 라이선스는 시점에 따라 바뀔 수 있으므로, 실제 제출 직전
  해당 모델의 공식 라이선스 페이지를 재확인해 URL과 함께 최신 값으로
  갱신하십시오.
