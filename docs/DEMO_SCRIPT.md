# 3분 시연 영상 시나리오

## 목표

FiTuna가 "모델 지정 → 하드웨어/품질 제약 조건 → 최적 양자화·실행 설정 자동
탐색 → 바로 실행 가능한 커맨드 출력"까지 한 번의 CLI 호출로 끝난다는 것을
보여준다.

## 타임라인 (총 ~3분)

1. **0:00–0:20 — 문제 제시**
   - 화면: 터미널 + llama.cpp 문서 페이지.
   - 멘트: "GGUF 양자화 레벨과 `-ngl`/`-c` 조합은 수십 가지인데, 원하는
     속도와 품질을 동시에 만족하는 조합을 사람이 일일이 벤치마크하려면
     시간이 오래 걸립니다."

2. **0:20–0:40 — 하드웨어 자동 감지**
   ```
   fituna detect-hw
   ```
   - 출력: GPU 벤더/이름/VRAM, CPU 코어 수, RAM, OS가 표로 출력됨.

3. **0:40–2:20 — 탐색 실행 (핵심 데모)**
   ```
   fituna run --model ./models/Llama-3-8B-Instruct \
     --target-tps 20 --max-quality-loss 3 \
     --ctx 4096 --wikitext ./data/wikitext-2-raw --out ./out
   ```
   - 진행 로그가 실시간으로 흐름: 어떤 quant를 시도 중인지, perplexity
     품질 체크 결과, ngl 이진탐색 진행 상황, bench 결과(tok/s).
   - 목표(20 tok/s, 품질손실 3% 이내)를 만족하는 첫 조합을 찾는 순간
     조기 종료(early-exit)되는 것을 강조.

4. **2:20–2:50 — 결과 확인**
   - 최종 출력: 선택된 quant/ngl/ctx, 실측 tok/s, 품질손실 %,
     그대로 복사해 실행 가능한 `llama-cli ...` 커맨드.
   - `--resume`으로 같은 커맨드를 다시 돌리면 캐시 덕분에 즉시 재사용됨을
     짧게 보여줌 (sqlite3 캐시 언급).

5. **2:50–3:00 — 마무리**
   - 멘트: "FiTuna는 연산을 직접 하지 않습니다. llama.cpp 바이너리를
     오케스트레이션하고 결과를 해석할 뿐이라, 표준 라이브러리만으로
     동작하고 어떤 하드웨어에서도 가볍게 설치됩니다."

## 준비물

- Llama-3-8B-Instruct 등 데모용 모델 1개 (README의 설치 안내 참고).
- `data/wikitext-2-raw` (README에 다운로드 링크 명시, CC-BY-SA 라이선스).
- llama.cpp 빌드 산출물이 PATH에 있거나 `--llama-bin-dir`로 지정 가능한 상태.
