# 3분 시연 영상 시나리오

이 문서는 FiTuna 데모 영상을 그대로 촬영·편집할 수 있도록 컷 단위로 정리한
스크립트다. 각 컷마다 "화면", "터미널 입력", "예상 출력", "내레이션"을
명시했다. 설치·다운로드처럼 오래 걸리는 구간은 배속 편집을 전제로 한다.

**출력 블록의 수치는 Apple M3 Pro + llama.cpp Homebrew build 9960 실측값**
(`docs/RESULTS.md`와 동일)이다. 다른 하드웨어에서 녹화하면 절대값은 달라지므로
그 자리에서 나온 실측값을 그대로 쓰면 된다 — 로그의 *형태*(어떤 단계에서
무엇을 출력하는지, 조기종료가 어디서 발동하는지)는 동일하다.

라이브 탐색은 **SmolLM2-135M-Instruct**(Apache 2.0)를 쓴다: 콜드 캐시 기준
전체 탐색이 약 76초라 배속 없이도 부담이 없고, `--hf`로 다운로드부터
결과까지 명령 한 줄에 담긴다.

## 목표

빈 머신에서 시작해 **pip 설치 → 명령 한 줄 → 바로 쓸 수 있는 양자화 모델
파일**까지 3분 안에 보여준다. 시청자가 가져가야 할 메시지는 세 가지:

1. quant × ngl × ctx 조합을 사람이 수동으로 벤치마크할 필요가 없다.
2. 품질(perplexity)을 먼저 실측하고, 그 순서대로 속도를 확인하다가 목표를
   만족하는 순간 멈춘다(조기종료).
3. 결과는 점수가 아니라 **이미 만들어진 gguf 파일**이고, 바로 쓰는 방법
   세 가지(로컬 API 서버 / Ollama / `llama-cli`)가 함께 출력된다.
4. 같은 실측을 사람이 아닌 **AI 에이전트도 MCP로** 쓸 수 있다 — 챗봇의
   사양표 추측 대신 실측 기반 답변.

## 내레이션 원칙

- 화면에서 지금 일어나는 일만 말한다. 화면에 없는 주장은 하지 않는다.
- 과장 형용사("놀랍게도", "혁신적인" 등) 금지. 수치가 있으면 수치로 말한다.
- 용어는 첫 등장에서 한 문장으로 정의하고 다시 설명하지 않는다.
- 같은 정보를 두 번 말하지 않는다.

## 사전 준비 (녹화 최소 하루 전에 끝낼 것)

- [ ] 녹화 머신에서 `brew uninstall llama.cpp`·가상환경 삭제 등으로 "빈 상태"를
  재현할 수 있는지 확인. 완전 초기화가 부담스러우면 설치 컷만 별도 테이크로
  찍어도 된다.
- [ ] **리허설 1회**: 아래 전체 명령을 한 번 돌려 소요 시간을 실측하고,
  `rm -rf ./out`으로 초기화한 뒤 본 촬영을 시작한다(`--hf` 다운로드와
  탐색이 모두 처음부터 다시 돈다). 76초를 크게 넘기면 `--target-tps`
  조정 또는 배속 구간 확대로 대응.
- [ ] 네트워크 상태 확인 — 본 촬영에서 모델(258 MB)과 코퍼스를 라이브로
  다운로드한다.
- [ ] 8번 MCP 컷 리허설 — `claude mcp add fituna -- fituna-mcp` 등록 후
  같은 질문을 던져 에이전트가 `fituna_recommend`를 호출하고 캐시 실측값으로
  답하는지 확인. 본 촬영 전 `claude mcp remove fituna`로 초기화.
- [ ] 터미널 폰트를 녹화 해상도 기준으로 충분히 키우고, 프롬프트는 `$`
  정도로 짧게 설정.
- [ ] 화면 녹화 도구·마이크 테스트, 알림(메신저 팝업 등) 끄기.

## 타임라인 (총 ~3분 15초 — 3분을 지켜야 하면 아래 "컷 옵션" 참고)

### 1. 0:00–0:15 — 문제 제시

- **화면**: 터미널만. (선택) llama.cpp `--help`의 긴 옵션 목록을 잠깐 비춘다.
- **내레이션**:
> 안녕하세요. FiTuna의 시연자 이윤석입니다.
  > FiTuna는 오픈웨이트 LLM 모델명과 목표 추론 속도(tok/s)를 입력하면 내 기기에서 해당 목표를 충족하는 양자화 정도, GPU 레이어, 컨텍스트 길이 조합을 단순 추정아닌, 실측을 기반으로 산출하도록 도와주는 오픈소스 CLI 도구입니다. 이를 통해 시행착오 없이, 원하는 속도와 품질의 로컬 LLM 실행 환경을 빠르게 구성할 수 있습니다"
- **화면 전환**: `clear`.

### 2. 0:15–0:45 — 설치 (배속)

터미널 입력(세 단계, 각각 실행 장면을 배속으로):

```bash
$ brew install llama.cpp
$ python3.13 -m venv .venv && source .venv/bin/activate
$ pip install fituna
```

- **내레이션**:
> 먼저 Homebrew로 llama.cpp를 설치합니다. FiTuna는 별도 런타임 의존성 없이 llama.cpp만 있으면 동작합니다.
> 다음으로 Python 가상환경을 만들고, pip로 FiTuna를 설치합니다. 설치는 여기까지입니다.
- **편집**: brew 설치 로그는 4~8배속. pip 설치는 수 초라 실시간도 무방.

### 3. 0:45–1:05 — 코퍼스 준비와 명령 입력

터미널 입력:

```bash
$ fituna fetch-corpus --lang en --out wiki.txt
$ fituna -v run --hf bartowski/SmolLM2-135M-Instruct-GGUF \
    --target-tps 240 --max-quality-loss 5 \
    --ctx 4096 --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M \
    --ppl-chunks 32 --quality-corpus wiki.txt --out ./out --resume
```

- **내레이션** (명령을 화면에 띄운 채, 플래그를 위에서부터):
> 먼저 fetch-copus 명령어로 품질 측정에 사용할 영어 위키텍스트를 다운로드합니다.
-v 플래그는 진행 로그를 자세히 출력하도록 도와줍니다.
--hf 플래그를 사용해서 원본 모델인 SmolLM2 135M 양자화 버전을 Hugging Face 저장소에서 불러오겠습니다.
--target-tps 플래그로 목표 생성 속도를 초당 240토큰 설정한 뒤, --max-quality-loss 플래그로 품질 손실 정도를 5%로 제한하겠습니다.
--ctx 플래그와 --quant 플래그는 각각 한 번에 유지할 수 있는 최대 컨텍스트 길이와 시험할 양자화 수준 후보를 지정할 수 있습니다.
--ppl-chunks 플래그로 품질 측정에 사용할 코퍼스 분량을 설정한 뒤, --quality-corpus 플래그로 실측에 사용할 위키텍스트를, --out 플래그로 결과 저장 폴더를 지정합니다.
--resume 플래그는 측정 결과를 캐시에 저장합니다.

- **편집**: 나레이션이 언급하는 플래그를 순서대로 하이라이트하면 따라가기
  쉽다.

### 4. 1:05–1:55 — 탐색 실행 (핵심 컷)

```
license: apache-2.0 (weights published by bartowski/SmolLM2-135M-Instruct-GGUF; their terms, not FiTuna's)
downloading https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-f16.gguf
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

- **내레이션** (로그 진행에 맞춰 세 토막):
  > (다운로드 중) "모델을 받고 있습니다. 라이선스도 함께 표시됩니다."
  >
  > (quantizing/evaluating 반복 구간) "모든 후보를 양자화하고 perplexity를
  > 측정합니다. perplexity는 모델이 텍스트를 얼마나 잘 예측하는지를 나타내는
  > 품질 지표입니다."
  >
  > (bench 구간) "perplexity가 낮은 순서대로 초당 처리 토큰 수를 잽니다. 보시다시피 실측 결과가 초당 205 토큰으로
  > 목표인 초당 240 토큰에 못 미쳐 바로 건너뜁니다. 다음 후보 Q6_K가 초당 249.5토큰으로 목표를
  > 만족하는 순간 탐색이 멈춥니다."
- **화면 강조**: `early-exit B` 줄과 `found ngl=30 meeting target` 줄에
  하이라이트.
- **편집**: 다운로드와 quantizing/evaluating 반복 구간은 2~4배속. 조기종료가
  드러나는 bench 구간은 실시간 유지 — 심사 관점에서 "왜 그 판단이 났는지"가
  보이는 구간이다.

### 5. 1:55–2:25 — 결과 확인

탐색이 끝나면 최종 리포트가 출력된다(M3 Pro 실측 재현 — gguf 파일명의 해시,
`llama-server`/`llama-cli` 경로는 녹화 환경 값이 그대로 찍힌다):

```
FiTuna result: MEETS TARGET

  quant           : Q6_K
  ngl             : 30
  ctx             : 4096

  prompt tok/s (pp): 2939.98
  gen tok/s    (tg): 249.50

  perplexity      : 18.3377 (baseline 18.2407)
  quality loss    : 0.53%

  artifact: out/SmolLM2-135M-Instruct-d4777063db8a-Q6_K.gguf  (111.0 MB -- already produced during the search)

  1) local API server (OpenAI-compatible):
       /opt/homebrew/bin/llama-server -m out/SmolLM2-135M-Instruct-d4777063db8a-Q6_K.gguf -ngl 30 -c 4096 --port 8080
  2) import into Ollama: re-run with --export-ollama to write a Modelfile beside the artifact
  3) terminal chat (interactive check):
       /opt/homebrew/bin/llama-cli -m out/SmolLM2-135M-Instruct-d4777063db8a-Q6_K.gguf -ngl 30 -c 4096
```

- **내레이션**:
  > "결과 로그에서는 가장 적은 비용으로 목표를 달성한 조합과 실측 결과를 확인할 수 있습니다. 하단의 `artifact` 줄의 gguf 파일은 탐색 도중 이미 만들어진
  > 것이라 추가 작업 없이 아래 세 가지 방법으로 바로 사용할 수 있습니다."
- **화면 강조**: `artifact:` 줄 → 세 가지 사용법 블록 순서로 하이라이트.
  이 블록은 최소 2초 이상 화면에 고정한다.

### 5-1. (+약 10~15초, 타임라인 재조정 필요) — 터미널 채팅 즉시 실행

터미널 입력 (5번 리포트의 "3) terminal chat" 줄을 그대로 복사):

```bash
$ /opt/homebrew/bin/llama-cli -m out/SmolLM2-135M-Instruct-d4777063db8a-Q6_K.gguf -ngl 30 -c 4096
```

- **내레이션**:
> "예를 들어 3번 terminal chat 명령어를 그대로 실행하면, 설정한 목표인 초당
  > 240토큰, 최대 컨텍스트 길이 4096을 만족하는 최소 자원 구성 조합인 Q6_K
  > 양자화, 30층 오프로드 모델을 터미널에서 채팅 모드로 바로 실행할 수
  > 있습니다."
- **화면**: llama-cli 프롬프트가 뜨고 짧은 대화 한두 마디 후 `/bye`로 종료.
- **편집**: 실행~첫 응답 구간은 실시간 유지, 이후 대화는 잘라도 무방.
- **주의**: 실제 녹화에서 나온 quant/ngl 값이 다르면(예: Q8_0/ngl=28) 리포트에
  찍힌 값 그대로 내레이션 수치를 바꿔 말한다.

### 6. 2:25–2:37 — Ollama 내보내기

터미널 입력(같은 명령에 `--export-ollama`만 추가 — `--resume` 캐시 덕에
재탐색 없이 곧바로 끝난다):

```bash
$ fituna run --hf bartowski/SmolLM2-135M-Instruct-GGUF \
    --target-tps 240 --max-quality-loss 5 \
    --ctx 4096 --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M \
    --ppl-chunks 32 --quality-corpus wiki.txt --out ./out --resume --export-ollama
$ cat out/Modelfile
```

예상 출력:

```
FROM ./SmolLM2-135M-Instruct-d4777063db8a-Q6_K.gguf
PARAMETER num_gpu 30
PARAMETER num_ctx 4096
```

- **내레이션**:
  > "`--export-ollama`를 붙이면 찾아낸 구성이 그대로 담긴 Ollama Modelfile이
  > 생성됩니다. 탐색 결과가 다른 도구의 입력으로 바로 이어집니다."

### 7. 2:37–2:49 — 캐시 재현

터미널 입력(4번과 동일한 명령 재실행):

```bash
$ fituna run --hf bartowski/SmolLM2-135M-Instruct-GGUF \
    --target-tps 240 --max-quality-loss 5 \
    --ctx 4096 --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M \
    --ppl-chunks 32 --quality-corpus wiki.txt --out ./out --resume
```

첫 줄에 `model already on disk, reusing: out/SmolLM2-135M-Instruct-f16.gguf`가
찍히고, quantize/bench/perplexity 없이 캐시에서 읽어 **1초 미만**(실측
0.75초)에 5번과 동일한 리포트가 출력된다.

- **내레이션**:
  > "같은 명령을 한 번 더 실행하면, 모델과 측정값 모두 캐시에서 읽어 1초
  > 안에 같은 답이 나옵니다. 벤치마크 결과가 재현 가능한 산출물로 남는다는
  > 뜻입니다."

### 8. 2:49–3:05 — MCP 연동 (AI 에이전트가 실측을 쓰게 하기)

터미널 입력(캐시가 따뜻한 상태라 에이전트의 답이 ~1초에 나온다):

```bash
$ claude mcp add fituna -- fituna-mcp
$ claude "이 머신에서 SmolLM2-135M을 초당 240토큰 이상으로 돌리려면 어떤 설정이 좋아?"
```

에이전트가 `fituna_recommend` 도구를 호출하고, 캐시에 남은 실측 결과로
5번 컷과 동일한 구성(Q6_K, ngl=30, 249.5 tok/s)을 근거로 답한다.

- **내레이션**:
  > "그 외에도 FiTuna MCP를 설치하면 에이전트에게 추측에 의거한 답변이 아닌,
   실측 결과를 바탕으로 로컬 모델 설정을 추천받을 수 있습니다."
- **화면 강조**: 에이전트 답변 속 실측 수치(249.5 tok/s)가 5번 컷 리포트와
  일치하는 부분에 하이라이트.
- **리허설 필수**: 에이전트가 `fituna_recommend`를 실제로 호출하는지, 인자
  (모델 경로·target)를 제대로 넘기는지 사전에 확인. 불안정하면 도구 호출
  장면을 별도 테이크로 찍는다.

### 9. 3:05–3:15 — 마무리

- **화면**: 터미널을 클리어하고 FiTuna 로고 또는 README 제목만 남긴다(선택).
- **내레이션**:
  > "설치부터 실행 가능한 모델 파일까지 3분이었습니다. 추측 대신 실측으로,
  > 내 하드웨어의 최적 구성을 찾는 도구 — FiTuna입니다."

## 만약 시간이 부족하면 (컷 옵션)

- 4번 탐색 구간이 길어지면 quantizing/evaluating 반복 로그의 배속을 더
  올린다. 조기종료 발생 줄은 자르지 말 것 — 판단 근거가 사라진다.
- 6번(Ollama)·7번(캐시)·8번(MCP)은 서로 독립이라 일부만 남겨도 된다.
  3분을 지켜야 하면 둘만 고른다. 우선순위는 8번(MCP) ≥ 7번(캐시) —
  에이전트 연동과 재현성이 더 고유한 메시지고, Ollama는 5번 리포트의
  "2) import into Ollama" 줄이 이미 언급한다.

## 만약 목표를 만족하는 조합이 없다면 (대비 시나리오)

모든 quant가 속도 미달로 탈락하면 `fituna run`은 종료 코드 3과 함께
`NoFeasibleConfigError`를 내고, 가장 빨랐던 시도 정보를 에러 메시지에 담아
출력한다. `--target-tps`를 비현실적으로 높게(예: 500) 걸면 의도적으로 재현할
수 있다 — "목표를 못 만족해도 조용히 실패하지 않는다"는 메시지용. 본편 3분에는
넣지 않고 질의응답·보너스 클립용으로만 쓴다.

## 준비물 요약

- 네트워크 (모델 258 MB + 코퍼스 라이브 다운로드).
- Homebrew, python3.13 사용 가능한 macOS 머신 (다른 환경이면 설치 컷의
  명령만 해당 환경에 맞게 교체).
- 8번 MCP 컷용 MCP 클라이언트 (예: Claude Code CLI) 설치·로그인.
- 리허설 1회 완료 + `rm -rf ./out`으로 초기화한 상태에서 본 촬영 시작.

## 촬영 후 편집 체크리스트

- [ ] 각 컷의 내레이션과 화면 타이밍이 맞는지 확인.
- [ ] 배속 구간(설치·다운로드·quantize 반복)과 실시간 구간(조기종료·결과)이
  구분되는지, 배속 표시(x4 등)를 넣었는지 확인.
- [ ] `early-exit B` 줄과 `found ngl=30 meeting target` 줄에 하이라이트가
  들어갔는지 확인.
- [ ] 최종 리포트의 `artifact:` 줄과 세 가지 사용법 블록이 최소 2초 이상
  고정되는지 확인.
- [ ] 8번 MCP 컷에서 에이전트 답변의 실측 수치가 5번 리포트와 일치하는지,
  그 부분에 하이라이트가 들어갔는지 확인.
- [ ] 전체 길이 확인 — 컷 전부 포함 시 ~3분 15초. 3분(±10초) 제한이면
  "컷 옵션"대로 6·7·8 중 둘만 남긴다.
