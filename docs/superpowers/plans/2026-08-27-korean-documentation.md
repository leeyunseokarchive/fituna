# 한국어 문서 전환 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 한국인 심사위원이 FiTuna의 공개 문서를 번역 없이 읽을 수 있도록 영문 설명을 한국어로 전환하고 README에 문서 안내표를 추가한다.

**Architecture:** 파일 구조와 기술적 사실은 그대로 두고 Markdown의 설명 문구만 번역한다. 영문판 README, 내부 작업 기록, 법률 원문, 코드·명령·로그는 변경하지 않으며 기존 앵커 호환성을 유지한다.

**Tech Stack:** Markdown, Mermaid, Git, 표준 셸 검사 명령

## Global Constraints

- `README.en.md`와 `docs/superpowers/`는 번역하지 않는다.
- MIT 라이선스 원문, SPDX 식별자, 명령어, 코드, 로그, 파일명, 제품명, API와 프로토콜 이름은 원문을 유지한다.
- 수치, 버전, 날짜, 실측 결과와 기술적 주장을 바꾸지 않는다.
- 기존 상대경로 링크, 명시적 앵커, 표, Mermaid와 코드 블록 구조를 보존한다.

---

### Task 1: README 문서 안내표

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 소개 영역 아래에 문서 안내표 추가**

아키텍처, 개발·검증 방식, 기여 안내, 실측 결과, 오픈소스 활용,
라이선스 검증, 심사·재현 가이드를 문서명과 한 줄 설명으로 연결한다.

- [ ] **Step 2: 링크 대상 확인**

Run: `rg -n 'ARCHITECTURE.md|DEVELOPMENT.md|CONTRIBUTING.md|RESULTS.md|OPEN_SOURCE_USAGE.md|LICENSE_COMPLIANCE.md|REVIEWERS.md' README.md`

Expected: 일곱 문서 링크가 새 표에 모두 나타난다.

### Task 2: 최상위 프로젝트·커뮤니티 문서 번역

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `CODE_OF_CONDUCT.md`
- Modify: `CONTRIBUTING.md`
- Modify: `SECURITY.md`
- Modify: `THIRD_PARTY_NOTICES.md`

- [ ] **Step 1: 설명·제목·표를 한국어로 번역**

버전별 변경 기록, 기여 절차, 보안 정책과 제3자 고지를 자연스러운 한국어로
옮기되 MIT 라이선스 전문은 그대로 둔다.

- [ ] **Step 2: 예외 영역 확인**

Run: `git diff --check -- CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTING.md SECURITY.md THIRD_PARTY_NOTICES.md`

Expected: 출력 없이 종료 코드 0.

### Task 3: 핵심 개발·검증 문서 번역

**Files:**
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/DEVELOPMENT.md`
- Modify: `docs/RESULTS.md`

- [ ] **Step 1: 기술 설명을 한국어로 번역**

모듈명, CLI 플래그, 함수명, 수식, 측정값은 유지하고 주변 설명과 도표 레이블을
한국어로 옮긴다. `why-this-shape` 앵커는 명시적으로 보존한다.

- [ ] **Step 2: 구조 검사**

Run: `git diff --check -- docs/ARCHITECTURE.md docs/DEVELOPMENT.md docs/RESULTS.md`

Expected: 출력 없이 종료 코드 0.

### Task 4: 오픈소스·라이선스 근거 문서 번역

**Files:**
- Modify: `docs/OPEN_SOURCE_USAGE.md`
- Modify: `docs/LICENSE_COMPLIANCE.md`

- [ ] **Step 1: 근거 설명을 한국어로 번역**

라이선스명, 명령과 실제 검사 출력은 보존하고 해설, 표 머리글, 재현 절차의
설명만 한국어로 옮긴다.

- [ ] **Step 2: 법률·검사 원문 보존 확인**

Run: `git diff --check -- docs/OPEN_SOURCE_USAGE.md docs/LICENSE_COMPLIANCE.md`

Expected: 출력 없이 종료 코드 0.

### Task 5: 전체 문서 검증

**Files:**
- Verify: all modified Markdown files

- [ ] **Step 1: 제외 대상 변경 여부 검사**

Run: `git diff --name-only | rg '^(README\.en\.md|docs/superpowers/)'`

Expected: 새 계획 파일 외 번역 대상이 아닌 파일은 출력되지 않는다.

- [ ] **Step 2: Markdown과 앵커 검사**

Run: `git diff --check && rg -n '<a id="why-this-shape"></a>' docs/ARCHITECTURE.md`

Expected: 공백 오류가 없고 호환 앵커가 한 번 나타난다.

- [ ] **Step 3: 남은 영문 설명 검토**

각 수정 파일의 제목과 일반 문단을 검색해 남은 영어가 법률 원문, 코드, 명령,
로그, 고유명사 또는 기술 식별자인지 확인한다.

- [ ] **Step 4: 최종 diff 검토**

Run: `git diff --stat && git status --short`

Expected: 계획된 Markdown 문서만 변경되고 파일 구조 변경은 없다.
