# FiTuna repository completion design

## Goal

Make the public repository internally consistent, judge-ready, and resilient
without adding speculative infrastructure. The submitted result report is the
source of truth for the chatbot comparison; measured repository evidence is the
source of truth for code, release, and project-management claims.

## Scope

### README and evidence alignment

- Replace the current three-model/single-chatbot comparison with the result
  report's same-condition Qwen3-4B comparison:
  - FiTuna: Q4_K_M, ngl=33, 32.68+/-1.71 tok/s, 1.75%, 3/3 passes.
  - Claude Opus 5: Q5_K_M, ngl=36, 30.49+/-0.88 tok/s, 1.53%, 2/3 passes.
  - ChatGPT 5.6 Sol: Q4_K_M, ngl=28, 28.92+/-1.37 tok/s, 1.75%, 1/3 passes.
  - Gemini 3.1 Pro: declined the query because the requested capability was
    unsupported; do not fabricate a benchmark value.
- Regenerate one repository-owned SVG chart from those values and use it in
  Korean and English README sections.
- Keep the interpretation narrow: FiTuna alone met both targets in all three
  runs and used less offload than Claude's proposal; this does not rank general
  chatbot quality.
- Remove the awkward "copy 1)-3), about a minute" paragraph and sweep both
  READMEs for broken Markdown, stale values, spacing, and claims that differ
  from the report.
- Add the official demonstration video (`https://youtu.be/ejNnWFm9V6I`) near
  the reviewer guide in both README hero blocks and link it once from the demo
  section; avoid repeating the URL elsewhere.
- Update or replace `docs/CHATBOT_COMPARISON.md` so linked evidence describes
  the same experiment as the README and report.

### Repository and documentation hygiene

- Correct the supported release in `SECURITY.md` from 0.1.0 to 0.2.0.
- Remove stale README links to closed "good first issue" and roadmap items;
  describe implemented limits without presenting closed issues as active work.
- Remove the tracked `.github/.DS_Store` and fix whitespace reported by
  `git diff --check`.
- Preserve the user's existing demo-script and MCP changes; integrate rather
  than overwrite them.
- Do not add governance or automation files unless an observed failure requires
  them; the existing templates and CI already cover the current project shape.

### MCP robustness

- Reproduce and fix the root cause at the JSON-RPC boundary: decoded JSON,
  `params`, and tool `arguments` are assumed to be mappings before `.get()` is
  called.
- Write failing tests first for non-object top-level requests and non-object
  tool arguments.
- Return JSON-RPC invalid-request/tool errors instead of terminating the server.
- Keep the server dependency-free and sequential.

## Validation

- Run the focused MCP tests red, implement the minimum validation, then run
  them green.
- Install no runtime dependencies. Use the existing development extra or a
  disposable environment only if pytest is missing.
- Run the full pytest suite, all module self-checks, `compileall`,
  `git diff --check`, package build/install smoke checks, and local Markdown
  link checks.
- Inspect the generated SVG and README rendering source for readable labels,
  accessible alt text, and consistency with the result report.
- Re-query public GitHub state after the local work is complete and report any
  settings that require repository-owner action rather than silently mutating
  remote settings.

## Non-goals

- Do not edit the submitted DOCX.
- Do not invent new benchmark runs or change measured values.
- Do not add a formatter, type checker, coverage service, or dependency bot
  configuration solely for appearance; recommend remote settings separately
  when they are useful.
- Do not push, merge, close issues, or alter GitHub settings without a separate
  explicit authorization.
