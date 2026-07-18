# 3분 시연 영상 시나리오

이 문서는 FiTuna 데모 영상을 그대로 촬영/편집할 수 있도록 컷 단위로 정리한
스크립트다. 각 컷마다 "화면", "터미널 입력", "예상 출력", "내레이션(멘트)"을
모두 명시했다. **아래 출력 블록의 수치는 Apple M3 Pro + llama.cpp Homebrew
build 9960에서 실제로 측정된 값**(`docs/RESULTS.md`와 동일)이다. 다른 하드웨어
에서 녹화하면 절대값은 달라지므로 그 자리에서 나온 실측값을 그대로 쓰면 된다 —
로그의 *형태*(어떤 단계에서 무엇을 출력하는지, 조기종료가 어디서 발동하는지)는
동일하다.

라이브 탐색 컷은 **SmolLM2-135M-Instruct**(Apache 2.0)를 쓴다: 콜드 캐시
기준 전체 탐색이 **약 76초**라 3분 영상 안에 실시간으로 담긴다. 보고서의 주
결과(Qwen3-4B)는 탐색이 10분 이상이므로 영상에서는 결과 화면만 보여주거나
배속 편집으로 처리한다.

## 목표

FiTuna가 "모델 지정 → 하드웨어/품질 제약 조건 → 최적 양자화·실행 설정 자동
탐색 → 바로 실행 가능한 커맨드 출력"까지 **한 번의 CLI 호출**로 끝난다는 것을
보여준다. 강조 포인트는 세 가지:

1. 사람이 quant × ngl × ctx 조합을 수동으로 벤치마크할 필요가 없다.
2. 품질(perplexity) 우선 필터 덕분에 "품질 저하가 허용 범위 안에서 가장 좋은"
   조합을 찾으며, 목표를 만족하는 순간 즉시 멈춘다(조기종료).
3. 결과물은 추상적인 점수가 아니라 **그대로 복사해서 실행 가능한 커맨드**다.

## 사전 준비 (녹화 최소 하루 전에 끝낼 것)

- [ ] 데모용 모델: `SmolLM2-135M-Instruct-f16.gguf` (F16, 258MB — HuggingFace
  `bartowski/SmolLM2-135M-Instruct-GGUF`에서 다운로드, Apache 2.0). 135M이라
  콜드 탐색이 ~76초로 3분 안에 라이브로 들어간다.
- [ ] `wikitext-2-raw-test.txt` 준비 (README의 export 스니펫 참고, CC BY-SA).
  perplexity 계산용 코퍼스.
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
$ fituna run --model SmolLM2-135M-Instruct-f16.gguf \
    --target-tps 240 --max-quality-loss 5 \
    --ctx 4096 --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M \
    --ppl-chunks 32 --wikitext wikitext-2-raw-test.txt --out ./out --resume -v
```

`-v`(verbose)로 진행 로그가 자세히 보이게 한다. 아래는 M3 Pro에서 실측된
로그(콜드 캐시 기준 전체 ~76초). 조기종료 B가 어떻게 드러나는지가 핵심이다.

```
INFO fituna: computing baseline perplexity on base GGUF
INFO fituna: [Q8_0] quantizing
INFO fituna: [Q8_0] evaluating quality
INFO fituna: [Q6_K] quantizing
INFO fituna: [Q6_K] evaluating quality
INFO fituna: [Q5_K_M] quantizing
...
INFO fituna: [Q8_0] bench full-offload (ngl=30)
INFO fituna: [Q8_0] full-offload 205.91 tok/s < target 240.00, skipping (early-exit B)
INFO fituna: [Q6_K] bench full-offload (ngl=30)
INFO fituna: [Q6_K] found ngl=30 meeting target -- done
```

- **내레이션 (로그가 흐르는 동안)**:
  > "모든 후보의 품질을 먼저 실측합니다 — 이 순서는 통념이 아니라 방금 잰
  > perplexity 기준입니다. 그 다음 품질이 좋은 순서대로 속도를 봅니다.
  > '당연히 가장 좋을' Q8_0은 실측 205 tok/s로 목표 240에 못 미쳐 즉시
  > 건너뛰고, 다음 후보 Q6_K가 249.5 tok/s로 목표를 만족하는 순간 탐색이
  > 멈춥니다. 품질손실은 0.53%에 불과합니다. 더 낮은 품질의 quant는 시도조차
  > 하지 않아요."
- **화면 강조**: `early-exit B` 줄과 `found ngl=30 meeting target` 줄에
  자막/하이라이트.
- **덧붙일 포인트(자막)**: 이 하드웨어에선 Q4_K_M(244.34 tok/s)이 더 큰
  Q6_K(249.50 tok/s)보다 오히려 *느리다* — 파일 크기 기반 직관이 틀리는
  실측 사례.

### 4. 2:20–2:50 — 결과 확인

탐색이 끝나면 사람이 읽는 최종 리포트가 출력된다 (M3 Pro 실측):

```
FiTuna result: MEETS TARGET

  quant           : Q6_K
  ngl             : 30
  ctx             : 4096
  gguf            : out/SmolLM2-135M-Instruct-d4777063db8a-Q6_K.gguf

  prompt tok/s (pp): 2939.98
  gen tok/s    (tg): 249.50

  perplexity      : 18.3377 (baseline 18.2407)
  quality loss    : 0.53%

  run command:
    llama-cli -m out/SmolLM2-135M-Instruct-d4777063db8a-Q6_K.gguf -ngl 30 -c 4096
```

- **내레이션**:
  > "결과는 선택된 quant, ngl, ctx, 실측 tok/s, 품질 손실률, 그리고 그대로
  > 복사해서 실행 가능한 `llama-cli` 커맨드까지 한 번에 나옵니다."
- 화면에서 `llama-cli ...` 줄을 마우스로 드래그해 복사하는 동작을 보여주면
  "그대로 실행 가능"이라는 메시지가 시각적으로 강화된다.
- **캐시 재사용 보여주기**: 같은 커맨드를 한 번 더 실행한다(--resume 포함).
  이번에는 quantize/bench/perplexity를 다시 돌리지 않고 `.fituna_cache.sqlite3`
  에서 즉시 읽어와 **1초 미만**(실측 0.75초)에 동일한 결과가 출력된다.
  > "`--resume` 캐시 덕에 같은 모델·하드웨어·llama.cpp 빌드 조합이면 1초 안에
  > 같은 답이 재현됩니다. 벤치마크가 재현 가능한 산출물이 된다는 뜻입니다."
- **(선택) 보고서 주 결과 언급**: Qwen3-4B 실측 결과 화면(docs/RESULTS.md의
  표)을 잠깐 비추며:
  > "4B급 모델에서는 통념상 최상인 Q8_0이 실측 품질에서도 Q6_K에 밀리고,
  > 속도에서도 목표 미달이었습니다. 최종 답은 Q4_K_M을 GPU 레이어 33개만
  > 올리는 구성 — 이런 답은 실측 없이는 나올 수 없습니다."

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

- SmolLM2-135M-Instruct-f16.gguf (라이브 탐색용, Apache 2.0).
- `wikitext-2-raw-test.txt` (README의 export 스니펫 참고, CC BY-SA 라이선스).
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
