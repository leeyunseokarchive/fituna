# Result Report Layout-Preserving Redo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 공식 양식과 원본 문체를 보존하면서 결과보고서 본문을 5쪽 이내로 압축하고 붙임을 바로잡은 별도 DOCX를 만든다.

**Architecture:** 원본 DOCX를 별도 파일로 복사한 뒤 기존 본문 표의 우측 셀 텍스트만 최소 수정한다. 표 구조와 섹션 설정은 수정 전후 XML 지문으로 비교하고, LibreOffice 렌더링으로 실제 페이지 수와 시각 품질을 확인한다.

**Tech Stack:** Python 3, python-docx/lxml, ZIP/XML 검사, LibreOffice headless, poppler.

## Global Constraints

- 원본 DOCX를 덮어쓰지 않는다.
- `docx-style-guide`를 적용하지 않는다.
- 본문 표의 행·열·셀 병합, 페이지 방향, 여백, 제목 체계, 글꼴 체계를 변경하지 않는다.
- 새 도식·그래프를 넣지 않고 원본 실측 비교표를 유지한다.
- 본문은 5쪽 이내로 맞춘다.
- 붙임 1은 기존 가로 SBOM 양식을 유지하고, 붙임 2는 공식 조건에 따라 삭제한다.

---

### Task 1: 원본 구조 기준선과 편집 스크립트

**Files:**
- Create: `/Users/leeyunseok/Desktop/Projects/OpenSourceDeveloperCompetition/_workspace/2026-08-27-report-redo/edit_report.py`
- Read: `/Users/leeyunseok/Desktop/Projects/OpenSourceDeveloperCompetition/2026 오픈소스 개발자대회 결과보고서_접수번호(팀명)/2026 오픈소스 개발자대회 결과보고서_433(FiTuna).docx`

**Interfaces:**
- Consumes: 원본 DOCX 경로와 별도 출력 경로.
- Produces: `snapshot_structure(path)`, `edit_report(source, output)`, `verify_structure(before, after)`.

- [ ] **Step 1: 원본 SHA-256, 섹션 설정, 표별 행·열·병합 구조를 기록한다.**

Run: `uv run --with python-docx --with lxml python _workspace/2026-08-27-report-redo/edit_report.py --inspect`

Expected: 원본 해시, 2개 섹션, 본문 표 구조와 총 페이지 10쪽을 출력한다.

- [ ] **Step 2: 원본을 `_재수정본.docx`로 복사하고 기존 본문 셀 안의 문단만 교체한다.**

본문은 문제·해결·구현·검증 순으로 읽히게 정리하되 제목과 어조는 원본을 따른다. 문단·런 서식은 기존 문단에서 상속하고 표 구조는 수정하지 않는다.

- [ ] **Step 3: SBOM에서 독점 도구를 제외하고 실제 오픈소스 구성요소만 기존 행에 기재한 뒤 붙임 2를 제거한다.**

Expected: 붙임 1의 제목·열·가로 방향은 원본과 같고, 붙임 2의 제목과 표는 남지 않는다.

- [ ] **Step 4: 구조 자체 검사를 실행한다.**

Run: `REPORT_OUTPUT=$(find .. -type f -name '*433(FiTuna)_재수정본.docx' -print -quit); uv run --with python-docx --with lxml python ../_workspace/2026-08-27-report-redo/edit_report.py --verify-output "$REPORT_OUTPUT"`

Expected: `PASS: source unchanged; body table structure unchanged; section geometry unchanged; appendix 2 absent`.

### Task 2: 5쪽 맞춤과 시각 검증

**Files:**
- Modify: `/Users/leeyunseok/Desktop/Projects/OpenSourceDeveloperCompetition/2026 오픈소스 개발자대회 결과보고서_접수번호(팀명)/2026 오픈소스 개발자대회 결과보고서_433(FiTuna)_재수정본.docx`
- Generate: `/private/tmp/fituna-result-report-redo/*.pdf`
- Generate: `/private/tmp/fituna-result-report-redo/page-*.png`

**Interfaces:**
- Consumes: Task 1의 별도 수정본.
- Produces: 본문 5쪽 이내의 검증 완료 DOCX.

- [ ] **Step 1: 격리된 LibreOffice 프로필로 수정본을 PDF 변환한다.**

Run: `REPORT_OUTPUT=$(find .. -type f -name '*433(FiTuna)_재수정본.docx' -print -quit); /Applications/LibreOffice.app/Contents/MacOS/soffice -env:UserInstallation=file:///private/tmp/fituna-lo-redo --headless --convert-to pdf --outdir /private/tmp/fituna-result-report-redo "$REPORT_OUTPUT"`

Expected: 변환 성공 및 PDF 생성.

- [ ] **Step 2: 본문 종료 페이지와 총 페이지 수를 확인한다.**

Expected: 붙임 1이 6쪽에서 시작하고 총 7쪽 이내이다.

- [ ] **Step 3: 144dpi PNG로 모든 페이지를 렌더링해 육안 검사한다.**

Run: `REPORT_PDF=$(find /private/tmp/fituna-result-report-redo -type f -name '*재수정본.pdf' -print -quit); pdftoppm -png -r 144 "$REPORT_PDF" /private/tmp/fituna-result-report-redo/page`

Expected: 모든 페이지에서 표·문장·실측 비교표가 잘리지 않고 겹치지 않는다.

- [ ] **Step 4: 5쪽을 초과하면 글꼴·여백을 줄이지 않고 셀 안의 중복 문장만 추가 삭제한다.**

Expected: 본문 5쪽 이내를 만족하면서 필요성, 핵심 기능, 실측 결과, 공개 개발 근거, 한계와 로드맵이 남는다.

- [ ] **Step 5: 최종 구조·원본 해시·렌더링을 다시 확인한다.**

Expected: `PASS: original SHA-256 unchanged; body <= 5 pages; layout preserved; all pages visually checked`.
