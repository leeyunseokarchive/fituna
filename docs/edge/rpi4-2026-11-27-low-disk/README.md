# Raspberry Pi 4(4GB)에서 `--low-disk` 검증

관련 이슈: [#92](https://github.com/leeyunseokarchive/fituna/issues/92) (저용량 모드), [#56](https://github.com/leeyunseokarchive/fituna/issues/56) (엣지 기기)
검증 대상: FiTuna 0.3.8의 `--low-disk`([#106](https://github.com/leeyunseokarchive/fituna/pull/106))

## 3줄 요약

- Raspberry Pi 4(4GB, 방열판, 팬 없음, CPU 전용)에서 SmolLM2-135M F16으로 `--low-disk`를 시나리오 9개로 검증했고, 모두 기대대로 동작했습니다. **버그는 찾지 못했습니다.**
- 같은 조건에서 `--out`의 디스크 최대 사용량은 기본 모드 **500,751,616 B(후보 4개 합)** → 저용량 모드 **144,811,072 B(가장 큰 후보 Q8_0 하나)** 로 **71% 줄었고**, 판정, 품질은 같았으며 실행 시간은 **3~5% 늘었습니다**.
- 쓸 수 있는 공간이 253 MB인 볼륨에서 기본 모드는 Q6_K 양자화 중 실패했고 저용량 모드는 성공했습니다. 다만 실패 메시지가 디스크 부족을 알려 주지 않습니다(아래 개선 제안 1).

## 측정 환경

| 항목 | 값 |
|---|---|
| 기기 | Raspberry Pi 4 Model B Rev 1.5, RAM 4 GB(`detect-hw`: 3,795 MB), 4코어 |
| OS | Debian GNU/Linux 13 (trixie), 64-bit(aarch64) |
| 냉각 | 없음(방열판, 냉각팬 모두 없음) |
| Python | 3.13.5 (venv) |
| FiTuna | 0.3.8 (`pip install -U fituna`) |
| llama.cpp | commit `ed2153e`, 기기에서 직접 빌드(`llama-quantize`, `llama-perplexity`, `llama-bench`) |
| 원본 모델 | `SmolLM2-135M-Instruct-f16.gguf` (bartowski/SmolLM2-135M-Instruct-GGUF, 270,885,952 B). `--out` 밖에 둠 |
| 품질 코퍼스 | `fituna fetch-corpus --out wiki.txt` |
| 측정일 | 2026-11-27 (14:00 부팅, 측정 14:27~16:20) |

`detect-hw` 결과는 `gpu_vendor: none`, `cpu_cores: 4`, `ram_mb: 3795`로 기기와 일치했습니다.

### 공통 옵션

```bash
COMMON="--model $BASE --quality-corpus wiki.txt --llama-bin-dir $BIN \
  --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M --ppl-chunks 8 --ctx 1024 --max-quality-loss 10"
```

- 반복 실행이 많아서 `--ppl-chunks 8`, `--ctx 1024`로 줄였습니다.
- 각 실행은 `env.sh`의 `measure` 함수로 감쌌습니다. `/usr/bin/time -v`로 시간, 최대 RSS를 재고, `peak_disk.sh`가 1초마다 `du -sb <--out>`을 재서 최댓값을 `.peak`에 남깁니다.
- 시나리오마다 `--out`을 새 폴더로 써서 캐시가 섞이지 않게 했습니다(D, E는 일부러 같은 폴더를 재사용).

## 후보별 실측 (기준선)

`--target-tps 9999`로 모든 후보를 탈락시켜 속도를 얻었습니다(`base_all.log`).

| 품질 순위(실측) | 후보 | 파일 크기(B) | 품질 손실 | gen tok/s |
|---:|---|---:|---:|---:|
| 1 | Q8_0 | 144,811,072 | 0.42 % | 20.71 |
| 2 | Q6_K | 138,382,912 | (미표시) | 21.43 |
| 3 | Q5_K_M | 112,103,488 | 3.87 % | 24.03 |
| 4 | Q4_K_M | 105,454,144 | 5.38 % | 24.94 |

원본 perplexity는 19.6798입니다. 진행 로그는 탈락한 후보의 품질 손실만 출력해서 Q6_K 값은 로그에 없습니다. 이 결과로 시나리오 A의 목표를 **22 tok/s**로 정했습니다(Q8_0, Q6_K 탈락, Q5_K_M 합격).

## 시나리오별 결과

| # | 확인 내용 | 로그 | 결과 |
|---|---|---|---|
| A | 기본 모드와 판정이 같은가 | `base_T`, `low_T` | ✅ 둘 다 Q5_K_M, 품질 손실 3.87 %, perplexity 20.4406로 같음 |
| B | 진 후보는 지우고 이긴 후보만 남기는가 | `low_T` | ✅ Q8_0, Q6_K는 벤치 후 삭제, Q5_K_M만 남음, `.tmp` 없음 |
| C | 모두 탈락하면 best-effort만 다시 만드는가 | `low_none` | ✅ exit 3, Q4_K_M(5.38 %)만 다시 만들어짐 |
| D-1 | `--resume` 재실행이 아무것도 다시 재지 않는가 | `low_resume1` → `low_resume2` | ✅ 8:12 → **1.04초**. baseline, 품질, 벤치, 양자화 모두 없음 |
| D-2 | 결과 파일만 지웠을 때 그것만 다시 만드는가 | `low_resume3` | ✅ **3.37초**, `[Q5_K_M] re-quantizing` 한 줄만 |
| E-1 | 양자화 도중 Ctrl-C 후 이어서 되는가 | `low_kill1` → `low_kill2` | ✅ 아래 참고 |
| E-2 | 벤치 도중 Ctrl-C 후 이어서 되는가 | `low_killb1` → `low_killb2` | ✅ 아래 참고 |
| F | 품질 조기 종료(early-exit A) 후보도 지우는가 | `low_q` | ✅ `--max-quality-loss 5`에서 Q4_K_M 탈락 직후 삭제, Q8_0만 남음 |
| G | 실제로 디스크가 부족할 때 | `small_default`, `small_default2`, `small_low` | ✅ 기본 모드 실패, 저용량 모드 성공 (아래 참고) |

### 디스크, 시간 비교

| 비교 | 모드 | 실행 시간 | 최대 RSS | `--out` 최대 사용량 | 끝난 뒤 남은 후보 |
|---|---|---:|---:|---:|---|
| 목표 22 (A) | 기본 `base_T` | 7:58.72 | 665,012 KB | 500,751,616 B | 4개 |
| | 저용량 `low_T` | 8:24.41 (**+5.4 %**) | 665,184 KB | **144,811,072 B** | Q5_K_M 1개 |
| 목표 9999 (C) | 기본 `base_all` | 9:14.45 | 664,984 KB | 500,751,616 B | 4개 |
| | 저용량 `low_none` | 9:32.01 (**+3.2 %**) | 665,124 KB | **144,811,072 B** | Q4_K_M 1개 |

- 기본 모드의 최대치는 후보 4개 크기의 합과 **바이트 단위로 같고**, 저용량 모드의 최대치는 가장 큰 후보(Q8_0) 크기와 **바이트 단위로 같습니다**. #92의 "원본 + 가장 큰 후보 하나"가 그대로 맞았습니다(원본은 `--out` 밖에 있어서 위 숫자에 포함되지 않습니다).
- `--resume`을 켠 `low_resume1`의 최대치는 144,844,376 B로, 캐시 파일(약 32 KB)만큼 더 큽니다.
- 추가 시간은 벤치한 후보를 다시 양자화하는 비용입니다. 135M 모델은 양자화가 후보당 1~3초라 차이가 작았습니다. 큰 모델에서는 비율이 커질 수 있습니다.
- 최대 RSS는 두 모드가 같습니다. 저용량 모드는 디스크만 줄이고 메모리 사용은 바꾸지 않습니다.

### E: 중간에 끊었을 때

**E-1 (양자화 도중).** Q4_K_M을 양자화하는 중에 Ctrl-C를 눌렀습니다. `--out`에는 쓰다 만 `...Q4_K_M.gguf.tmp.70704`(40,767,040 B, 완성본의 약 39 %)와 캐시만 남았고, 완성본 이름의 파일은 없었습니다. 같은 명령으로 다시 실행하자

- baseline과 Q8_0, Q6_K, Q5_K_M 품질 측정은 캐시에서 가져왔고,
- Q4_K_M만 처음부터 양자화했으며,
- 끝난 뒤 `.tmp` 파일은 남지 않았고, 결과는 A와 같았습니다(약 5분, 처음부터 하면 약 8분).

**E-2 (벤치 도중).** Q5_K_M 벤치 중에 Ctrl-C를 눌렀습니다. 직후 `ps`에 `llama-bench`, `llama-quantize`가 남지 않았습니다. 다시 실행하자 Q8_0, Q6_K 벤치는 캐시에서 가져왔고, 남아 있던 Q5_K_M 파일은 다시 만들지 않고 재사용했습니다(`re-quantizing` 줄 없음, 파일 수정 시각 그대로). 결과는 A와 같았습니다.

### G: 디스크가 실제로 부족할 때

300 MB 루프백 파일 시스템(`df` 기준 사용 가능 253 MB)을 만들어 `--out`으로 썼습니다. 원본은 SD카드에 두었습니다.

```bash
fallocate -l 300M ~/small.img && mkfs.ext4 -q ~/small.img
sudo mount -o loop ~/small.img /mnt/small && sudo chown $USER /mnt/small
```

| 모드 | 결과 | 끝난 뒤 상태 |
|---|---|---|
| 기본 | **exit 1**. Q8_0(144.8 MB)을 만든 뒤 Q6_K 양자화 중 실패 | Q8_0만 남음, `.tmp` 없음, 사용 가능 114 MB |
| 저용량 | **exit 0**. Q5_K_M, 품질 손실 3.87 % (A와 같음) | Q5_K_M만 남음, 사용 가능 146 MB |

기본 모드는 두 번 실행했고 두 번 모두 같은 지점에서 실패했습니다. 두 번째 실행은 첫 번째가 남긴 Q8_0을 재사용했습니다(`[Q8_0] quantizing` 다음 1 ms 만에 `evaluating quality`).

## 발열

- 방열판과 냉각팬 없이 측정했습니다. 세션이 끝난 뒤 `vcgencmd get_throttled`는 `0xe0000`이었습니다. 부팅(14:00) 이후 soft temperature limit, throttling, ARM 클럭 상한이 발생했고 저전압은 없었다는 뜻입니다.
- 시나리오 F를 실행하는 동안 5초 간격으로 기록했습니다(`thermal.log`, 68개).
  - 온도 50.1~**85.2°C**
  - 68개 중 36개(53 %)가 `0xe0008`(지금 soft temp limit에 걸려 있음)
  - 부하 중 ARM 클럭은 1.58~1.80 GHz 사이에서 오르내림
- 그래도 같은 후보의 생성 속도는 약 1.5시간 동안 크게 흔들리지 않았습니다. 모든 측정이 비슷하게 뜨거운 상태에서 진행됐기 때문으로 보입니다.

| 후보 | 측정 횟수 | gen tok/s 범위 | 차이 |
|---|---:|---|---:|
| Q8_0 | 8 | 20.39 ~ 20.86 | 2.3 % |
| Q6_K | 8 | 20.89 ~ 21.60 | 3.4 % |

(캐시에서 읽은 값은 제외했습니다.) 모드 비교에는 영향이 없지만, 절대 속도는 냉각이 있는 Pi 4보다 낮을 수 있습니다.

## 개선 제안 (버그 아님)

1. **디스크 부족 실패를 알아보기 어렵습니다.** G의 기본 모드 실패 로그는 457줄이고, FiTuna 메시지(`llama-quantize failed for quant='Q6_K' (exit code 1)`)는 5번째 줄에 있습니다. 나머지는 llama-quantize의 텐서 출력이며, 마지막 줄은 `llama_model_quantize: failed to quantize: basic_ios::clear: iostream error`입니다. 디스크 공간이나 `--low-disk`는 언급되지 않습니다. 양자화가 실패했을 때 `--out`의 남은 공간이 작으면 "디스크가 가득 찬 것 같습니다. `--low-disk`를 써 보세요"를 덧붙이면 좋겠습니다. #92의 열린 질문(필요한 공간이 부족할 때 플래그를 권할지)과도 이어집니다.
2. **마지막 후보를 지웠다가 바로 다시 만듭니다.** C에서 Q4_K_M은 벤치 직후 삭제(15:18:04.534)됐다가 best-effort로 다시 양자화됐습니다(약 2.5초). 마지막으로 벤치한 후보가 best-effort면 지우지 않아도 됩니다. 큰 모델에서는 몇 분을 아낄 수 있습니다.
3. **끊긴 뒤 남은 `.tmp`는 같은 후보를 다시 양자화할 때만 지워집니다.** E-1에서는 같은 명령으로 재실행해서 지워졌지만, 다음 실행에서 `--quant` 목록이 바뀌면 남을 수 있습니다. 시작할 때 `--out`의 오래된 `*.gguf.tmp.*`를 정리하는 방법을 생각해 볼 수 있습니다.
4. **결과 문구.** 저용량 모드에서도 `artifact:` 줄은 `already produced during the search`로 나옵니다. C처럼 탐색이 끝난 뒤 다시 만든 파일에는 조금 맞지 않습니다(`report.py`의 `_artifact_line`).

## 확인하지 않은 것

- 135M보다 큰 모델. 양자화 시간이 길어지면 추가 시간 비율이 달라질 수 있습니다.
- `--ctx 4096`(기본값). `llama-bench` 타임아웃(300초)에 걸리는지는 확인하지 않았습니다.
- `--quality-metric kld`, `--export-ollama`, `--json`과 함께 쓴 경우.
- 방열판이나 냉각팬을 단 상태.

## 파일

| 파일 | 내용 |
|---|---|
| `detect-hw.txt`, `list-binaries.txt`, `llama_commit.txt` | 환경 |
| `env.sh`(measure 함수), `peak_disk.sh` | 측정에 쓴 스크립트 |
| `base_all.*`, `base_ok.*` | 기준선 (목표 9999, 1) |
| `base_T.*`, `low_T.*` | A, B |
| `low_none.*` | C |
| `low_resume1.*`, `low_resume2.*`, `low_resume3.*` | D |
| `low_kill1.log`, `low_kill2.log`, `low_killb1.log`, `low_killb2.log` | E |
| `low_q.*` | F |
| `small_default.log`, `small_default2.log`, `small_low.log` | G |
| `thermal.log`, `throttled_final.txt` | 발열 |

`.log`는 FiTuna 출력, `.time`은 `/usr/bin/time -v`, `.peak`는 `--out` 최대 크기(바이트), `.temp`는 시작, 끝 온도입니다.
