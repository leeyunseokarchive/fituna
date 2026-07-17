# 3분 시연 영상 시나리오

이 문서는 FiTuna 데모 영상을 그대로 촬영/편집할 수 있도록 컷 단위로 정리한
스크립트다. 각 컷마다 "화면", "터미널 입력", "예상 출력", "내레이션(멘트)"을
모두 명시했다. **예상 출력 블록의 수치(tok/s, perplexity 등)는 실제 모델·
하드웨어·llama.cpp 빌드에 따라 달라지는 예시값**이며, 실제 녹화 시 그 자리에서
나온 실측값으로 자연스럽게 대체하면 된다. 로그의 *형태*(어떤 단계에서 무엇을
출력하는지, 조기종료 조건 A/B/C가 어디서 발동하는지)만 고정하면 된다.

## 목표

FiTuna가 "모델 지정 → 하드웨어/품질 제약 조건 → 최적 양자화·실행 설정 자동
탐색 → 바로 실행 가능한 커맨드 출력"까지 **한 번의 CLI 호출**로 끝난다는 것을
보여준다. 강조 포인트는 세 가지:

1. 사람이 quant × ngl × ctx 조합을 수동으로 벤치마크할 필요가 없다.
2. 품질(perplexity) 우선 필터 덕분에 "품질 저하가 허용 범위 안에서 가장 좋은"
   조합을 찾으며, 목표를 만족하는 순간 즉시 멈춘다(조기종료).
3. 결과물은 추상적인 점수가 아니라 **그대로 복사해서 실행 가능한 커맨드**다.

## 사전 준비 (녹화 최소 하루 전에 끝낼 것)

- [ ] 데모용 모델 1개를 로컬에 준비 (예: `./models/Llama-3-8B-Instruct`,
  GGUF 파일 또는 HF 포맷 디렉토리). 발표 시간(3분) 안에 탐색이 끝나야 하므로
  너무 큰 모델은 피한다 — 7B~8B급 권장. README 설치 안내 참고.
- [ ] `./data/wikitext-2-raw` 다운로드 (CC-BY-SA, README 링크 참고). perplexity
  계산용 코퍼스.
- [ ] llama.cpp 빌드 산출물(`llama-quantize`, `llama-bench`,
  `llama-perplexity`, `llama-cli`)이 `PATH`에 있거나 `--llama-bin-dir`로
  넘길 디렉토리를 파악해 둔다. `fituna list-binaries`로 사전 확인.
- [ ] **드라이런을 한 번 미리 돌려서** `./out` 아래에 quant된 gguf와
  `.fituna_cache.sqlite3`를 만들어 둔다. 본 촬영 직전에 `rm -rf ./out`으로
  캐시를 지워 "처음 실행하는 상황"을 재현한다 — 이렇게 하면 실제 탐색이 얼마나
  걸리는지 미리 알 수 있어 타임라인을 맞추기 쉽고, 3분을 넘길 것 같으면
  `--target-tps`를 낮추거나 더 작은 모델로 바꿔 리허설한다.
- [ ] 터미널 폰트 크기를 화면 녹화 해상도 기준으로 충분히 키운다(가독성).
  프롬프트는 짧게(`$` 정도)로 설정해 커맨드가 잘 보이게 한다.
- [ ] 화면 녹화 도구, 마이크 테스트, 알림/방해요소(메신저 팝업 등) 끄기.

## 타임라인 (총 ~3분)

### 1. 0:00–0:20 — 문제 제시

- **화면**: 터미널 + (선택) llama.cpp `--help` 또는 문서 페이지를 잠깐 비춘다.
- **내레이션**:
  > "GGUF 양자화 레벨(Q8_0부터 Q2_K까지)과 `-ngl`, `-c` 조합은 수십 가지인데,
  > 원하는 속도와 품질을 동시에 만족하는 조합을 사람이 일일이 벤치마크하려면
  > 시간이 오래 걸립니다. FiTuna는 이 탐색을 자동화합니다."
- **화면 전환**: 터미널만 남기고 클리어(`clear`).

### 2. 0:20–0:40 — 하드웨어 자동 감지

터미널 입력:

```bash
$ fituna detect-hw
```

예상 출력(개발 머신이 NVIDIA GPU를 가진 경우 예시):

```
GPU vendor   : nvidia
GPU name     : NVIDIA GeForce RTX 4090
VRAM         : 24564 MB
CPU cores    : 16
RAM          : 65536 MB
OS           : linux
```

- **내레이션**:
  > "먼저 `detect-hw`로 현재 하드웨어를 확인합니다. GPU 벤더와 VRAM, CPU
  > 코어 수, RAM이 자동으로 잡힙니다. GPU가 없거나 다른 하드웨어를 가정하고
  > 싶으면 `--gpu`, `--vram-mb`로 수동 지정도 가능합니다."
- Apple Silicon이나 CPU-only 환경에서 녹화한다면 위 출력 대신 실제 감지된
  값(`apple` / unified memory, 또는 `gpu_vendor: none`)을 그대로 사용한다.

### 3. 0:40–2:20 — 탐색 실행 (핵심 데모)

터미널 입력:

```bash
$ fituna run --model ./models/Llama-3-8B-Instruct \
    --target-tps 20 --max-quality-loss 3 \
    --ctx 4096 --wikitext ./data/wikitext-2-raw --out ./out -v
```

`-v`(verbose)를 켜서 진행 로그가 충분히 자세히 보이게 한다. 아래는 진행 로그의
**형태**를 보여주는 예시 — 조기종료 A/B/C가 로그 상에서 어떻게 드러나는지가
핵심이다.

```
2026-07-17 10:02:11 INFO fituna: resolved binaries: llama-quantize, llama-bench,
  llama-perplexity, llama-cli (llama.cpp b3xxx)
2026-07-17 10:02:11 INFO fituna: model: Llama-3-8B-Instruct, 32 layers, 8.03B params
2026-07-17 10:02:12 INFO fituna: baseline perplexity (F16): 5.812 (wikitext-2-raw)

--- stage 1: quality gate (quant 후보를 품질 내림차순으로 검증) ---
2026-07-17 10:02:40 INFO fituna: [Q8_0] quantize -> out/Llama-3-8B-Instruct-Q8_0.gguf
2026-07-17 10:03:05 INFO fituna: [Q8_0] perplexity 5.913 (+1.74%)  <= 3.0% OK
2026-07-17 10:03:41 INFO fituna: [Q6_K] quantize -> out/Llama-3-8B-Instruct-Q6_K.gguf
2026-07-17 10:04:02 INFO fituna: [Q6_K] perplexity 5.968 (+2.68%)  <= 3.0% OK
2026-07-17 10:04:35 INFO fituna: [Q5_K_M] quantize -> out/Llama-3-8B-Instruct-Q5_K_M.gguf
2026-07-17 10:04:57 INFO fituna: [Q5_K_M] perplexity 6.041 (+3.94%)  > 3.0% SKIP (품질 기준 초과)

--- stage 2: quant을 품질 내림차순으로 순회하며 속도 탐색 ---
2026-07-17 10:05:10 INFO fituna: [Q8_0] top bench: ngl=32(full) -> gen 14.2 tok/s
  (target 20.0) MISS -> 조기종료 B, 다음 quant로 이동
2026-07-17 10:05:38 INFO fituna: [Q6_K] top bench: ngl=32(full) -> gen 22.8 tok/s
  (target 20.0) HIT -> ngl 이진탐색 시작
2026-07-17 10:05:52 INFO fituna: [Q6_K] low bench: ngl=0(cpu-only) -> gen 6.1 tok/s
  (target 20.0) MISS -> GPU 오프로드 필요, 이진탐색 진행
2026-07-17 10:06:05 INFO fituna: [Q6_K] ngl=16 -> gen 15.9 tok/s  MISS  lo=17
2026-07-17 10:06:19 INFO fituna: [Q6_K] ngl=24 -> gen 21.4 tok/s  HIT   hi=24 (best)
2026-07-17 10:06:32 INFO fituna: [Q6_K] ngl=20 -> gen 18.7 tok/s  MISS  lo=21
2026-07-17 10:06:46 INFO fituna: [Q6_K] ngl=22 -> gen 20.9 tok/s  HIT   hi=22 (best)
2026-07-17 10:06:46 INFO fituna: [Q6_K] ngl 이진탐색 종료 (4/6 calls) -> 최소 ngl=22
2026-07-17 10:06:46 INFO fituna: 목표 충족: quant=Q6_K ngl=22 ctx=4096 -> 전체 탐색 조기종료
  (Q6_K보다 저품질인 Q5_K_M 이하는 이미 품질 게이트에서 제외되어 시도하지 않음)
```

- **내레이션 (로그가 흐르는 동안)**:
  > "Q8_0부터 품질을 먼저 검사합니다 — perplexity 손실이 3% 이내인 quant만
  > 통과시킵니다. Q5_K_M은 품질 기준을 넘어서 자동으로 제외됩니다. 그 다음
  > 남은 quant를 품질이 좋은 순서대로 순회하며 속도를 봅니다. Q8_0은 전체
  > 레이어를 GPU에 올려도 목표(20 tok/s)에 못 미쳐 즉시 건너뛰고, Q6_K는
  > 가능성이 있으니 `-ngl` 이진탐색으로 목표를 만족하는 **최소** GPU
  > 오프로드 레이어 수를 찾습니다. 목표를 만족하는 조합을 찾는 즉시 — 여기서는
  > Q6_K, ngl=22 — 탐색을 멈춥니다. 더 낮은 품질의 quant는 아예 시도조차
  > 하지 않아요."
- **화면 강조**: `조기종료 B`, `HIT`, `전체 탐색 조기종료` 줄이 나올 때
  자막이나 하이라이트 박스로 짚어준다.
- 만약 리허설에서 이 구간이 3분 예산에 비해 너무 길다면(quant가 여러 개 걸리는
  경우), `--ngl_max_calls`는 CLI 옵션이 아니므로 대신 `--target-tps`를 조금
  낮추거나 더 작은 모델로 바꿔서 리허설 단계에서 미리 조정한다.

### 4. 2:20–2:50 — 결과 확인

탐색이 끝나면 사람이 읽는 최종 리포트가 출력된다:

```
=== FiTuna search result ===
model         : ./models/Llama-3-8B-Instruct
selected quant: Q6_K   (baseline 대비 perplexity +2.68%, 허용 3.0%)
ngl / ctx     : 22 / 32 layers offloaded, ctx=4096
throughput    : prompt 812.4 tok/s, gen 20.9 tok/s  (목표 20.0 tok/s) -> MEETS TARGET
gguf          : out/Llama-3-8B-Instruct-Q6_K.gguf

바로 실행:
  llama-cli -m out/Llama-3-8B-Instruct-Q6_K.gguf -ngl 22 -c 4096
```

- **내레이션**:
  > "결과는 선택된 quant, ngl, ctx, 실측 tok/s, 품질 손실률, 그리고 그대로
  > 복사해서 실행 가능한 `llama-cli` 커맨드까지 한 번에 나옵니다. 이 커맨드를
  > 그대로 실행하면 방금 찾은 설정으로 바로 추론을 시작할 수 있습니다."
- 화면에서 `llama-cli ...` 줄을 마우스로 드래그해 선택하거나 복사하는 동작을
  보여주면 "그대로 실행 가능"이라는 메시지가 시각적으로 강화된다.
- **캐시 재사용 보여주기**: 같은 커맨드에 `--resume`만 붙여 다시 실행한다.

  ```bash
  $ fituna run --model ./models/Llama-3-8B-Instruct \
      --target-tps 20 --max-quality-loss 3 \
      --ctx 4096 --wikitext ./data/wikitext-2-raw --out ./out --resume
  ```

  이번에는 quantize/bench/perplexity를 다시 돌리지 않고 `.fituna_cache.sqlite3`
  에서 즉시 읽어와 몇 초 안에 동일한 결과가 출력된다.
  > "`--resume`을 붙이면 이미 계산한 벤치마크·품질 결과를 sqlite3 캐시에서
  > 즉시 재사용합니다 — 같은 모델·하드웨어 조합이면 llama.cpp를 다시 부르지
  > 않아요."

### 5. 2:50–3:00 — 마무리

- **화면**: 터미널을 클리어하고 FiTuna 로고/README 제목 정도만 남긴다(선택).
- **내레이션**:
  > "FiTuna는 연산을 직접 하지 않습니다. llama.cpp 바이너리를 오케스트레이션
  > 하고 그 결과를 해석할 뿐이라, 표준 라이브러리만으로 동작하고 어떤
  > 하드웨어에서도 가볍게 설치됩니다."

## 만약 시간이 부족하면 (컷 옵션)

- 3번(핵심 탐색) 구간이 길어질 경우, 로그 전체를 실시간으로 다 보여주지 않고
  1.5배속 정도로 편집하거나, `INFO` 로그 중 조기종료 A/B/C가 발생하는 줄만
  화면에 확대해서 컷 편집으로 이어붙인다. 실제 대회 심사에서는 "왜 그
  판단이 났는지"가 중요하므로 로그를 통으로 자르기보다 속도만 올리는 편이
  낫다.
- `detect-hw` 컷(2번)은 생략하고 바로 `fituna run` 커맨드에 `--gpu`,
  `--vram-mb`를 명시해 하드웨어를 화면에 텍스트로만 보여줘도 된다.

## 만약 목표를 만족하는 조합이 없다면 (대비 시나리오, 필요 시 별도 컷으로 활용 가능)

모든 quant가 조기종료 B로 탈락하면(즉, 가장 빠른 Q2_K조차 목표 속도 미달)
`fituna run`은 종료 코드 3과 함께 `NoFeasibleConfigError`를 발생시키고, 가장
빨랐던 시도 정보를 담아 에러 메시지를 출력한다. 이 상황을 의도적으로 보여주고
싶다면 `--target-tps`를 비현실적으로 높게(예: 500) 걸어 재현할 수 있다 —
"목표를 못 만족해도 FiTuna는 조용히 실패하지 않고 가장 근접했던 결과를
알려준다"는 메시지를 전달할 때 쓴다. 3분 분량에는 포함하지 않는 것을 기본으로
하되, 질의응답이나 보너스 클립으로 활용 가능하다.

## 준비물 요약

- Llama-3-8B-Instruct 등 데모용 모델 1개 (README의 설치 안내 참고).
- `data/wikitext-2-raw` (README에 다운로드 링크 명시, CC-BY-SA 라이선스).
- llama.cpp 빌드 산출물이 PATH에 있거나 `--llama-bin-dir`로 지정 가능한 상태.
- 리허설 1회 완료 + `./out`, `.fituna_cache.sqlite3` 초기화(`rm -rf ./out`)
  한 상태로 본 촬영 시작.

## 촬영 후 편집 체크리스트

- [ ] 각 컷의 내레이션과 화면 타이밍이 맞는지 확인.
- [ ] 로그에서 조기종료 A(품질 게이트 탈락)/B(속도 미달로 quant 스킵)/C(ngl=0
  으로 즉시 채택)가 실제로 발생한 줄에 자막 하이라이트를 넣었는지 확인.
- [ ] 최종 리포트의 `run_command` 줄이 화면에 최소 2초 이상 고정되어 시청자가
  읽을 수 있는지 확인.
- [ ] 전체 영상 길이가 3분(±10초) 이내인지 확인.
