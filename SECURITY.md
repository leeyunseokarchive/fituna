# Security Policy

## Supported versions

FiTuna is pre-1.0. Only the latest release (`0.1.0`) and `main` are supported;
fixes land on `main` and ship in the next release.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting:
[**Security → Report a vulnerability**](https://github.com/leeyunseokarchive/fituna/security/advisories/new).
If that is unavailable to you, email the maintainer at `dbstjr3576@gmail.com`
with `[fituna security]` in the subject.

Please include the FiTuna command you ran, your OS and llama.cpp build
(`fituna doctor --json` covers both), and what an attacker gains. Expect an
acknowledgement within a week — this is a solo, volunteer-maintained project.
Please do not open a public issue for a vulnerability until it has a fix.

## Trust boundary

FiTuna performs no inference or quantization itself: it executes llama.cpp
binaries as subprocesses and parses their output. Those binaries are found at
paths **you** supply — `--llama-bin-dir`, or whatever `llama-quantize`,
`llama-bench`, `llama-perplexity` and `llama-cli` your `PATH` resolves to —
and FiTuna runs them with your privileges. It also reads model files you point
it at and, in `fituna fetch-corpus`, fetches text over HTTPS from a
user-specifiable dataset host. So: pointing FiTuna at an untrusted binary,
directory, or dataset host is executing or ingesting that untrusted thing, and
FiTuna neither sandboxes nor verifies it. Treat `--llama-bin-dir`, `PATH`, the
`--out` directory, and `--dataset` as inputs you control. Bugs *inside* that
boundary — FiTuna mishandling an untrusted path, model file, or downloaded
corpus in a way that grants more than the above — are in scope and worth
reporting.
