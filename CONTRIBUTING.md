# FiTuna 기여 안내

관심을 가져 주셔서 감사합니다. FiTuna는 외부 의존성 없이 동작하는 작은 Python
CLI이며, 누구나 쉽게 기여할 수 있도록 진입 장벽을 낮췄습니다.

## 개발 환경 구성

```bash
git clone <repo-url>
cd fituna
python3.11 -m venv .venv && source .venv/bin/activate   # Python 3.11 이상 필요
pip install -e .
pip install pytest
```

런타임 의존성은 없습니다. 개발 의존성은 `pytest`뿐입니다.

## 검사 실행

```bash
pytest -q                      # 단위 테스트(모의 subprocess 사용, 빠름)
python -m fituna.search        # 모듈별 자체 점검 예시
python -m fituna.cli --selfcheck
```

실제 바이너리 통합 검사에는 `PATH`에 등록된 llama.cpp 빌드 또는
`--llama-bin-dir` 설정이 필요합니다. 자세한 내용은 README의 빠른 시작 4단계를
참고하세요.

## 변경 작업 원칙

- **계약 우선**: 모듈 사이에서 주고받는 데이터 구조는 `fituna/config.py`의
  불변 dataclass에 정의합니다. 모듈 간 데이터가 달라지는 변경이라면 이곳의
  dataclass와 모든 사용처를 같은 PR에서 함께 고쳐 주세요.
- **의존성 0개 유지**: 런타임 의존성을 추가하는 PR에는 분명한 근거가
  필요합니다. 표준 라이브러리만 쓰는 것은 우연이 아니라 프로젝트의 특징입니다.
- **테스트**: 동작을 바꿀 때는 단위 테스트 또는 자체 점검 assertion이
  필요합니다. subprocess 계층은 `tests/test_search.py`처럼 모의 객체로
  대체하세요.
- **스타일**: 주변 코드의 방식을 따릅니다. 호출 지점이 하나뿐인 코드를 위해
  새 추상화를 만들지 마세요.

## 버그 제보

다음 내용을 담아 이슈를 열어 주세요.

- 실행한 전체 `fituna` 명령
- OS와 하드웨어 정보(`fituna detect-hw` 출력)
- llama.cpp 빌드 정보(`fituna list-binaries` 출력)
- 오류 출력

## 라이선스

기여한 내용은 MIT License에 따라 배포하는 데 동의한 것으로 봅니다(`LICENSE`
참조).
