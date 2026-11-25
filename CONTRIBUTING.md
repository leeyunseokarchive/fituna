# Contributing to FiTuna / FiTuna 기여 안내

[English](#english) · [한국어](#한국어)

## English

Thanks for your interest. FiTuna is a small Python CLI with no runtime dependencies, and contributions of any size are welcome. Issues and pull requests can be written in English or Korean.

### Ways to contribute

- **Report a test run on your hardware.** No code needed. Use the [test report form](https://github.com/leeyunseokarchive/fituna/issues/new?template=test_report.yml); [#93](https://github.com/leeyunseokarchive/fituna/issues/93) lists the commands to run.
- **Pick an issue.** [`good first issue`](https://github.com/leeyunseokarchive/fituna/labels/good%20first%20issue) is scoped for a first PR; [`help wanted`](https://github.com/leeyunseokarchive/fituna/labels/help%20wanted) needs hardware or knowledge the maintainer doesn't have.
- **Report a bug or suggest a feature** with the issue templates.
- **Ask a question or share an early idea** in [Discussions](https://github.com/leeyunseokarchive/fituna/discussions).

Before you start on an issue, leave a comment saying you're taking it, so two people don't open the same PR. For a new feature, open an issue first and agree on the approach before writing code. Check the pinned issues for any temporary policy, such as a release freeze.

### Development setup

```bash
git clone https://github.com/leeyunseokarchive/fituna.git
cd fituna
python3.11 -m venv .venv            # Python 3.11 or newer
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -e .
pip install pytest
```

### Running checks

```bash
pytest -q                           # unit tests (subprocess is mocked, fast)
python -m fituna.search             # a module self-check
python -m fituna.cli --selfcheck
```

CI runs the tests and every module self-check on Ubuntu, macOS, and Windows with Python 3.11 and 3.13 (see `.github/workflows/ci.yml`). Running against real llama.cpp binaries needs a build on `PATH` or `--llama-bin-dir`; see [Install](README.md#install) in the README.

### Guidelines

- **Contract first.** Data passed between modules is defined as frozen dataclasses in `fituna/config.py`. If you change one, update it and every caller in the same PR.
- **No runtime dependencies.** Using only the standard library is a deliberate feature. A PR that adds a dependency needs a strong reason.
- **Tests.** A behavior change needs a unit test or a self-check assertion. For a bug fix, add a test that fails before the fix and passes after. Mock the subprocess layer as `tests/test_search.py` does.
- **Style.** Follow the surrounding code. Don't add an abstraction for code with a single caller.
- **One change per PR.** Keep unrelated changes in separate PRs.
- **AI-assisted contributions are fine**, but you are responsible for every line: understand it, test it, and be ready to explain it in review.

### Pull requests

- Fill in the PR template checklist and link the issue (`Fixes #N`).
- You don't need to edit `CHANGELOG.md`. The maintainer records merged changes.
- Review comments are part of the process. Push fixes to the same branch and reply when they're ready.

### Reporting bugs

Use the bug report template and include:

- the full `fituna` command you ran
- OS and hardware (`fituna detect-hw`)
- llama.cpp build (`fituna list-binaries`)
- the error output

For security issues, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

### License

By contributing, you agree that your contribution is distributed under the [MIT License](LICENSE).

---

## 한국어

관심을 가져 주셔서 감사합니다. FiTuna는 런타임 의존성이 없는 작은 Python CLI이고, 크기와 관계없이 어떤 기여든 환영합니다. 이슈와 PR은 영어나 한국어 중 편한 언어로 써 주세요.

### 기여 방법

- **내 기기에서 실행해 보고 결과 알려 주기.** 코드 작성은 필요 없습니다. [실행 결과 제보 양식](https://github.com/leeyunseokarchive/fituna/issues/new?template=test_report.yml)으로 올려 주시면 되고, 실행할 명령은 [#93](https://github.com/leeyunseokarchive/fituna/issues/93)에 있습니다.
- **이슈 골라서 작업하기.** [`good first issue`](https://github.com/leeyunseokarchive/fituna/labels/good%20first%20issue)는 첫 PR에 맞는 크기로 정리한 이슈이고, [`help wanted`](https://github.com/leeyunseokarchive/fituna/labels/help%20wanted)는 메인테이너에게 없는 하드웨어나 지식이 필요한 이슈입니다.
- **버그 신고나 기능 제안**은 이슈 템플릿으로 올려 주세요.
- **사용법 질문이나 아직 막연한 아이디어**는 [Discussions](https://github.com/leeyunseokarchive/fituna/discussions)에 남겨 주세요.

이슈 작업을 시작하기 전에 맡겠다는 코멘트를 남겨 주세요. 두 사람이 같은 PR을 여는 일을 막을 수 있습니다. 새 기능은 코드를 쓰기 전에 이슈를 먼저 열어 방향을 맞춰 주세요. 릴리스 동결 같은 임시 정책은 고정된(pinned) 이슈에서 확인할 수 있습니다.

### 개발 환경 구성

```bash
git clone https://github.com/leeyunseokarchive/fituna.git
cd fituna
python3.11 -m venv .venv            # Python 3.11 이상
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -e .
pip install pytest
```

### 검사 실행

```bash
pytest -q                           # 단위 테스트(subprocess는 모의 객체, 빠름)
python -m fituna.search             # 모듈 self-check 예시
python -m fituna.cli --selfcheck
```

CI는 Ubuntu, macOS, Windows에서 Python 3.11과 3.13으로 테스트와 모든 모듈의 self-check를 실행합니다(`.github/workflows/ci.yml`). 실제 llama.cpp 바이너리로 실행하려면 `PATH`에 빌드가 있거나 `--llama-bin-dir`를 지정해야 합니다. README의 [Install](README.md#install) 절을 참고해 주세요.

### 작업 원칙

- **계약 우선.** 모듈 사이에서 주고받는 데이터는 `fituna/config.py`의 불변 dataclass로 정의합니다. 이를 바꾸면 같은 PR에서 모든 사용처를 함께 고쳐 주세요.
- **런타임 의존성 0개.** 표준 라이브러리만 쓰는 것은 의도한 특징입니다. 의존성을 추가하는 PR에는 분명한 근거가 필요합니다.
- **테스트.** 동작을 바꾸면 단위 테스트나 self-check assertion이 필요합니다. 버그 수정에는 수정 전에는 실패하고 수정 후에는 통과하는 테스트를 넣어 주세요. subprocess 계층은 `tests/test_search.py`처럼 모의 객체로 대체합니다.
- **스타일.** 주변 코드를 따릅니다. 호출하는 곳이 하나뿐인 코드를 위해 새 추상화를 만들지 마세요.
- **PR 하나에 변경 하나.** 관련 없는 변경은 PR을 나눠 주세요.
- **AI 도구를 써도 괜찮습니다.** 다만 모든 줄에 대한 책임은 기여자에게 있습니다. 이해하고, 테스트하고, 리뷰에서 설명할 수 있어야 합니다.

### PR 제출

- PR 템플릿의 확인 목록을 채우고 이슈를 연결해 주세요(`Fixes #N`).
- `CHANGELOG.md`는 고치지 않아도 됩니다. 머지된 변경은 메인테이너가 기록합니다.
- 리뷰 코멘트는 과정의 일부입니다. 같은 브랜치에 수정 커밋을 올리고 준비되면 답글을 남겨 주세요.

### 버그 신고

버그 신고 템플릿을 쓰고 다음 내용을 넣어 주세요.

- 실행한 `fituna` 명령 전체
- OS와 하드웨어(`fituna detect-hw` 출력)
- llama.cpp 빌드(`fituna list-binaries` 출력)
- 오류 출력

보안 문제는 공개 이슈 대신 [SECURITY.md](SECURITY.md)의 절차를 따라 주세요.

### 라이선스

기여한 내용은 [MIT License](LICENSE)로 배포하는 데 동의한 것으로 봅니다.
