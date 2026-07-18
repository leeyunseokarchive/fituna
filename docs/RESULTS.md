# Measured end-to-end results

Real-hardware runs of `fituna run` against real llama.cpp binaries and real
open-weight models. Numbers below are what the tool actually printed —
reproduce them with the exact commands shown (absolute numbers vary by
machine and llama.cpp build; the *shape* of the outcome is the point).

**Environment (all runs)**

| | |
|---|---|
| Hardware | Apple M3 Pro, 18 GB unified memory (macOS, Apple Silicon) |
| llama.cpp | Homebrew build 9960 |
| Quality corpus | wikitext-2-raw-v1 test split (`--ppl-chunks 32`) |
| FiTuna | this repository, `pip install -e .` |

---

## Run 1 — SmolLM2-135M-Instruct (Apache 2.0)

Base model: `SmolLM2-135M-Instruct-f16.gguf` (F16, 258 MB).

```bash
fituna run --model SmolLM2-135M-Instruct-f16.gguf \
  --target-tps 240 --max-quality-loss 5 --ctx 4096 \
  --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M --ppl-chunks 32 \
  --wikitext wikitext-2-raw-test.txt --out ./out --resume
```

| Candidate | File size | Measured gen tok/s (full offload, ctx 4096) | Measured quality loss vs F16 | Verdict at target 240 |
|---|---|---|---|---|
| Q8_0 | 138 MB | 205.91 | 0.29 % | **miss** — early-exit B |
| **Q6_K** | 132 MB | **249.50** | **0.53 %** | **PASS (ngl=30)** |
| Q5_K_M | 107 MB | 233.26 | 3.32 % | never reached (early exit) |
| Q4_K_M | 101 MB | 244.34 | 4.74 % | never reached (early exit) |

*(the Q5_K_M/Q4_K_M tok/s columns come from the target-300 run below, where
every candidate was probed; at target 240 the search stops at Q6_K and never
spends benches on them — that's the early exit working)*

- Quality loss = relative perplexity increase vs the F16 baseline
  (baseline PPL 18.2407 → Q6_K 18.3377 = **+0.53 %**).
- **The "obvious" ranking is wrong twice here**: the highest-quality quant
  (Q8_0) is the *slowest*, and Q4_K_M (244.34) is measurably *slower* than
  the larger Q6_K (249.50) on this hardware. A size-based heuristic picks
  wrong in both directions; measurement doesn't.
- At a higher target (300 tok/s) every candidate misses: FiTuna exits with
  code 3 and reports the closest best-effort config (Q6_K, 249.50 tok/s)
  instead of failing silently. That run completed in **33.6 s** end-to-end
  (quality stage + 4 benches, cold cache).
- Search wall-clock at target 240: **75.7 s** (cold bench cache for the
  binary-search calls). Immediate re-run with `--resume`: **0.75 s**, same
  answer — the whole result set is reproducible from
  `out/.fituna_cache.sqlite3`.
- Disk: 478 MB for all four quantized files (each is reused across runs).

## Run 2 — Qwen3-4B-Instruct-2507 (Apache 2.0)

(pending — being re-measured on the same environment; this section is
filled from the actual tool output)
