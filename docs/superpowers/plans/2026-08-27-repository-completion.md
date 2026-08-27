# FiTuna Repository Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the repository with the submitted result report, harden the MCP request boundary, remove stale public claims, and leave a fully verified judge-ready working tree.

**Architecture:** Preserve the existing dependency-free package and the user's uncommitted demo/MCP work. Validate JSON-RPC once at the shared MCP boundary, then update the Korean and English public documentation from one measured dataset and one repository-owned SVG.

**Tech Stack:** Python 3.11+ stdlib, pytest development extra, Markdown, SVG, GitHub Actions.

## Global Constraints

- The submitted result report is the source of truth for chatbot-comparison values.
- Do not edit the submitted DOCX or invent benchmark results.
- Keep zero runtime dependencies and preserve the sequential stdio MCP server.
- Preserve and integrate existing changes in `docs/DEMO_SCRIPT.md`, `fituna/mcp_server.py`, and `tests/test_mcp_server.py`.
- Do not push or mutate GitHub settings.

---

### Task 1: Harden the MCP JSON-RPC boundary

**Files:**
- Modify: `tests/test_mcp_server.py`
- Modify: `fituna/mcp_server.py`

**Interfaces:**
- Consumes: newline-delimited JSON passed to `serve(stdin, stdout)`.
- Produces: `_handle(msg: object) -> Optional[dict[str, Any]]`, returning JSON-RPC `-32600` for a non-object request and `-32602` for non-object `params` or `arguments`.

- [ ] **Step 1: Install the existing development extra**

Run: `./.venv/bin/python -m pip install -e '.[dev]'`

Expected: editable `fituna==0.2.0` and pytest are installed; runtime dependencies remain unchanged.

- [ ] **Step 2: Add failing protocol tests**

Append tests that send `[]`, a non-object `params`, and string tool `arguments` through `serve()` and assert that the server emits `-32600`/`-32602` responses without raising:

```python
def _serve_one(message: object) -> dict:
    stdin = io.StringIO(json.dumps(message) + "\n")
    stdout = io.StringIO()
    mcp_server.serve(stdin, stdout)
    return json.loads(stdout.getvalue())


def test_rejects_non_object_request_without_stopping_server():
    response = _serve_one([])
    assert response["error"]["code"] == -32600


@pytest.mark.parametrize("params", [[], "bad"])
def test_rejects_non_object_params(params):
    response = _serve_one({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params})
    assert response["error"]["code"] == -32602


def test_rejects_non_object_tool_arguments():
    response = _serve_one({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "fituna_recommend", "arguments": "bad"}})
    assert response["error"]["code"] == -32602
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run: `./.venv/bin/python -m pytest tests/test_mcp_server.py -q`

Expected: the new tests fail with `AttributeError: 'list' object has no attribute 'get'` or the equivalent non-object boundary error.

- [ ] **Step 4: Add minimum shared-boundary validation**

Change `_handle` to accept `object`, reject a non-dict request before `.get()`, and validate `params` and `arguments` before dispatch. Preserve `None` as empty params/arguments and return standard JSON-RPC errors:

```python
def _error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _handle(msg: object) -> Optional[dict[str, Any]]:
    if not isinstance(msg, dict):
        return _error(None, -32600, "invalid request")
    # existing method/id handling
```

For `tools/call`, treat `None` as `{}` and return `_error(msg_id, -32602, "invalid params")` for every other non-dict value.

- [ ] **Step 5: Verify GREEN and commit**

Run: `./.venv/bin/python -m pytest tests/test_mcp_server.py -q`

Expected: all MCP tests pass.

Commit: `git add fituna/mcp_server.py tests/test_mcp_server.py && git commit -m 'fix: validate MCP JSON-RPC requests'`

### Task 2: Replace the chatbot comparison with report evidence

**Files:**
- Create: `assets/chatbot-comparison.svg`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/CHATBOT_COMPARISON.md`

**Interfaces:**
- Consumes: Qwen3-4B measurements recorded in the result report and `_workspace/2026-08-25-report-figure/chatbot_benchmark_results.md`.
- Produces: one bilingual-safe SVG plus Korean/English prose and tables containing identical values.

- [ ] **Step 1: Create the SVG from the measured values**

Use a static accessible SVG with title/description, a 30 tok/s target line, bars for Claude `30.49`, ChatGPT `28.92`, and FiTuna `32.68`, error bars `0.88`, `1.37`, `1.71`, and pass labels `2/3`, `1/3`, `3/3`. State that Gemini did not provide a setting and is excluded from numeric plotting.

- [ ] **Step 2: Update both README hero blocks and demo copy**

Add `[시연영상](https://youtu.be/ejNnWFm9V6I)` / `[Demo video](https://youtu.be/ejNnWFm9V6I)` beside the reviewer guide. Link the video once from the demo section. Remove the paragraph beginning with “아래 1)~3)” and its English counterpart; retain only the artifact/re-run explanation that is directly supported.

- [ ] **Step 3: Replace both chatbot sections**

Use the same four-row table as the report:

```text
FiTuna          Q4_K_M, ngl=33  32.68 +/- 1.71  1.75%  3/3
Claude Opus 5   Q5_K_M, ngl=36  30.49 +/- 0.88  1.53%  2/3
ChatGPT 5.6 Sol Q4_K_M, ngl=28  28.92 +/- 1.37  1.75%  1/3
Gemini 3.1 Pro  no configuration provided       -      -
```

Embed `assets/chatbot-comparison.svg` and state only that FiTuna met both targets on all three independent runs while using fewer GPU-offloaded layers than Claude's proposal.

- [ ] **Step 4: Replace the detailed comparison document**

Rewrite `docs/CHATBOT_COMPARISON.md` around the same environment, three independent speed runs, PPL values, formula, pass counts, and limitations. Remove the obsolete single-Claude/three-model transcript claims.

- [ ] **Step 5: Validate exact cross-file values and commit**

Run `rg` checks for all expected means/pass counts and confirm the obsolete phrases (`여유 있게 넘김`, `피하라던 Q4_K_M`, `세 번 모두 챗봇`) no longer appear in public comparison docs.

Commit: `git add README.md README.en.md docs/CHATBOT_COMPARISON.md assets/chatbot-comparison.svg && git commit -m 'docs: align chatbot comparison with report'`

### Task 3: Remove stale and malformed repository claims

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `SECURITY.md`
- Modify: `docs/DEMO_SCRIPT.md`

**Interfaces:**
- Consumes: public release v0.2.0 and current GitHub issue/milestone state.
- Produces: public docs that do not present closed issues as active work and pass whitespace checks.

- [ ] **Step 1: Fix security and roadmap text**

Change the supported release to `0.2.0`. Remove links to closed issues #8, #10, #11, and #12 from active roadmap/first-contribution language while retaining the factual limitations. Replace the first-contribution sentence with a direct link to `CONTRIBUTING.md`.

- [ ] **Step 2: Sweep README Markdown and Korean copy**

Remove broken strike-through/escape artifacts, trailing spaces, duplicated spacing, missing punctuation, and claims that `pip install fituna` also installs llama.cpp. Keep measured historical 0.1.0 evidence in `CHANGELOG.md` and `docs/LICENSE_COMPLIANCE.md` unchanged.

- [ ] **Step 3: Fix the existing demo-script whitespace**

Remove the trailing two spaces currently reported at `docs/DEMO_SCRIPT.md:75` without rewriting the user's demo content.

- [ ] **Step 4: Verify and commit**

Run: `git diff --check`

Expected: no whitespace errors.

Commit: `git add README.md README.en.md SECURITY.md docs/DEMO_SCRIPT.md && git commit -m 'docs: refresh repository guidance'`

### Task 4: Full repository verification

**Files:**
- Verify only; fix only failures caused by Tasks 1-3.

**Interfaces:**
- Consumes: completed working tree.
- Produces: reproducible verification evidence and a remaining remote-owner action list.

- [ ] **Step 1: Run code verification**

Run the full pytest suite, `python -m compileall -q fituna`, and all 17 module self-check commands from `.github/workflows/ci.yml`.

Expected: all tests and self-checks pass.

- [ ] **Step 2: Build and install the package in a disposable directory**

Run `./.venv/bin/python -m pip wheel . --no-deps -w <temporary-directory>` and install the wheel into a temporary venv, then run `fituna --help` and `fituna-mcp --selfcheck`.

Expected: one `fituna-0.2.0` wheel installs and both entry points run.

- [ ] **Step 3: Check documentation mechanically**

Use a stdlib-only temporary checker to confirm every relative Markdown link target exists, run `git diff --check`, parse the SVG as XML, and scan public Markdown for stale current-version/test/issue claims.

Expected: zero broken local targets, zero malformed XML/whitespace findings, and no known stale active links.

- [ ] **Step 4: Review final diff and public GitHub state**

Inspect `git diff origin/main...HEAD`, `git status`, branch protection, latest workflow runs, releases, open issues, and repository topics. Do not mutate remote settings.

- [ ] **Step 5: Commit verification-only fixes if any**

If validation required a scoped correction, commit only that correction as `chore: finish repository verification`. If no files changed, do not create an empty commit.
