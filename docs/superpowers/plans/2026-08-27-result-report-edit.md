# Result Report Edit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 원본 결과보고서를 보존하면서 심사 근거 중심의 본문 5쪽과 수정된 SBOM 2쪽으로 구성된 별도 DOCX를 만든다.

**Architecture:** 하나의 Python 스크립트가 원본 DOCX를 복제해 본문 표의 셀을 재작성하고, 두 개의 300dpi 도식을 생성·삽입하며, AI 모델 붙임을 제거한다. LibreOffice로 PDF 렌더링한 뒤 페이지 수와 모든 페이지 이미지를 검사해 분량과 가독성을 맞춘다.

**Tech Stack:** Python 3.11, python-docx, matplotlib, LibreOffice headless, poppler `pdfinfo`/`pdftoppm`.

## Global Constraints

- 원본 DOCX를 덮어쓰거나 변경하지 않는다.
- 본문은 정확히 5쪽, 붙임 1 SBOM은 2쪽, 최종 총 7쪽이다.
- 기존 대회 양식의 표 구조와 옅은 청색 계열을 유지한다.
- `docx-style-guide`는 적용하지 않는다.
- 공개 `main` 기준 테스트 256개, 병합 PR 28건, v0.3.0 이슈 8건 전건 처리라는 현재 사실을 사용한다.
- 붙임 2 AI 모델 기술 명세서는 삭제한다.
- 그래프 내부 최소 글자는 최종 삽입 크기에서 약 9pt 이상을 확보한다.

---

### Task 1: 편집 스크립트와 시각자료 작성

**Files:**
- Create: `/Users/leeyunseok/Desktop/Projects/OpenSourceDeveloperCompetition/_workspace/2026-08-27-report-edit/build_result_report.py`
- Generate: `/private/tmp/fituna-result-report-assets/architecture.png`
- Generate: `/private/tmp/fituna-result-report-assets/benchmark.png`

**Interfaces:**
- Consumes: 원본 `*433(FiTuna).docx`, 공개 저장소의 실제 파일명과 검증 수치.
- Produces: `generate_architecture(path: Path)`, `generate_benchmark(path: Path)`, `build_report(source: Path, output: Path)`, `self_check(output: Path)`.

- [ ] **Step 1: 단일 스크립트에 경로·상수·검증값을 정의한다**

```python
SPEED_MEAN = (30.49, 28.92, 32.68)
SPEED_SD = (0.88, 1.37, 1.71)
PASS_COUNTS = (2, 1, 3)
QUALITY_LOSS = (1.53, 1.75, 1.75)
assert all(v <= 5 for v in QUALITY_LOSS)
```

- [ ] **Step 2: 계층형 아키텍처 도식을 만든다**

```python
layers = (
    ("환경 감지", "GPU·메모리·모델 정보를 읽어 탐색 조건을 정한다.", "hardware.py · binaries.py · model_info.py"),
    ("탐색·실행", "품질을 먼저 측정하고 목표 속도를 만족하는 최소 설정을 찾는다.", "search.py · quantize.py · bench.py · quality.py"),
    ("캐시·진단", "실측 결과를 재사용하고 실행 전 문제와 해결 방법을 알려 준다.", "cache.py · doctor.py · corpus.py"),
)
```

- [ ] **Step 3: 상세 속도 비교 그래프를 만든다**

```python
labels = ("Claude Opus 5\nQ5_K_M · ngl 36\n△ 2/3회 통과",
          "ChatGPT 5.6 Sol\nQ4_K_M · ngl 28\n× 1/3회 통과",
          "FiTuna\nQ4_K_M · ngl 33\n○ 3/3회 통과")
```

목표선 라벨은 막대 뒤가 아니라 마지막에 그린다. 제목·실험 조건·품질손실·Gemini 제외 사유는 워드 본문 텍스트로 둔다.

- [ ] **Step 4: 최소 자체 검사를 실행한다**

Run: `python3 _workspace/2026-08-27-report-edit/build_result_report.py --assets-only --check`

Expected: `PASS: visual assets and benchmark constants`

### Task 2: 본문 5쪽과 SBOM 2쪽 편집

**Files:**
- Modify by copy only: 원본 `2026 오픈소스 개발자대회 결과보고서_433(FiTuna).docx`
- Create: 원본과 같은 폴더의 `2026 오픈소스 개발자대회 결과보고서_433(FiTuna)_수정본.docx`

**Interfaces:**
- Consumes: Task 1의 PNG 두 개와 편집 설계서.
- Produces: 원본과 다른 경로의 수정본 DOCX.

- [ ] **Step 1: 원본 SHA-256을 기록하고 별도 출력 경로를 확정한다**

Run: `source_doc=$(find . -path '*결과보고서*' -name '*433*FiTuna*.docx' ! -name '*수정본*' -print -quit); shasum -a 256 "$source_doc"`

Expected: 64자리 해시 한 개 출력.

- [ ] **Step 2: 본문 표를 근거 중심으로 재작성한다**

페이지 흐름은 `개요·필요성 → 구조 → 구현·차별성 → 실측 검증 → 오픈소스 완성도·로드맵`으로 구성한다. Gartner 문장, 반복된 기능 설명, 심사 근거와 연결되지 않는 시장 통계는 삭제한다. 아키텍처 도식과 속도 그래프는 각각 전체 셀 폭으로 삽입한다.

- [ ] **Step 3: SBOM을 핵심 오픈소스 구성요소로 고친다**

```text
Python/CPython, llama.cpp, GGUF/ggml, rocm-smi, sysctl,
WikiText-2·한국어 위키백과, setuptools, pytest
```

독점 도구 `nvidia-smi`, `system_profiler`는 오픈소스 SBOM 행에서 제외한다.

- [ ] **Step 4: 붙임 2의 제목·안내·명세 표와 사이 공백 문단을 제거한다**

Expected: 수정본 최상위 표 수 5개(제목, 팀 정보, 본문, 붙임1 제목, SBOM).

- [ ] **Step 5: 수정본 구조 자체 검사를 실행한다**

Run: `output_doc=$(find . -path '*결과보고서*' -name '*433*FiTuna*수정본.docx' -print -quit); python3 _workspace/2026-08-27-report-edit/build_result_report.py --check-output "$output_doc"`

Expected: `PASS: separate output, 5 tables, appendix 2 absent, SBOM revised`

### Task 3: 렌더링과 최종 품질 검증

**Files:**
- Generate: `/private/tmp/fituna-result-report-render/*.pdf`
- Generate: `/private/tmp/fituna-result-report-render/page-*.png`
- Final output: `2026 오픈소스 개발자대회 결과보고서_433(FiTuna)_수정본.docx`

**Interfaces:**
- Consumes: Task 2 수정본.
- Produces: 7쪽 렌더링 검증 결과와 최종 DOCX.

- [ ] **Step 1: LibreOffice로 PDF를 렌더링한다**

Run: `output_doc=$(find . -path '*결과보고서*' -name '*433*FiTuna*수정본.docx' -print -quit); /Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir /private/tmp/fituna-result-report-render "$output_doc"`

Expected: PDF 생성 성공.

- [ ] **Step 2: 페이지 수를 검사한다**

Run: `rendered_pdf=$(find /private/tmp/fituna-result-report-render -name '*수정본.pdf' -print -quit); pdfinfo "$rendered_pdf" | rg '^Pages:'`

Expected: `Pages: 7`.

- [ ] **Step 3: 모든 페이지를 이미지로 변환해 육안 검사한다**

Run: `rendered_pdf=$(find /private/tmp/fituna-result-report-render -name '*수정본.pdf' -print -quit); pdftoppm -png -r 144 "$rendered_pdf" /private/tmp/fituna-result-report-render/page`

Expected: `page-1.png`부터 `page-7.png`까지 생성되며, 본문은 5쪽에서 끝나고 SBOM은 6~7쪽에 위치한다. 표·도식·그래프의 잘림이나 겹침이 없다.

- [ ] **Step 4: 원본 보존을 재확인한다**

Run: `source_doc=$(find . -path '*결과보고서*' -name '*433*FiTuna*.docx' ! -name '*수정본*' -print -quit); shasum -a 256 "$source_doc"`

Expected: Task 2 Step 1과 같은 해시.

- [ ] **Step 5: 수정본만 최종 산출물로 전달한다**

Expected: 원본과 구별되는 `_수정본.docx` 파일 한 개를 링크한다.
