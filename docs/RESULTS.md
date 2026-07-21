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

Base model: `Qwen3-4B-Instruct-2507-F16.gguf` (F16, 7.5 GB).

```bash
fituna run --model Qwen3-4B-Instruct-2507-F16.gguf \
  --target-tps 30 --max-quality-loss 5 --ctx 4096 \
  --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M --ppl-chunks 32 \
  --wikitext wikitext-2-raw-test.txt --out ./out --resume
```

| Candidate | File size | Measured quality loss vs F16 | Measured gen tok/s (full offload, ctx 4096) | Verdict at target 30 |
|---|---|---|---|---|
| Q6_K | 3.1 GB | **−0.30 %** (better PPL than F16) | 28.48 | miss — early-exit B |
| Q8_0 | 4.0 GB | +0.07 % | 24.22 | miss — early-exit B |
| Q5_K_M | 2.7 GB | +1.53 % | 29.59 | miss by 0.41 tok/s |
| **Q4_K_M** | 2.3 GB | **+1.73 %** | 36.50 | **PASS — minimal ngl=33 → 30.81 tok/s** |

Three things this run demonstrates that a lookup table can't:

- **The assumed quality order was wrong.** Measured on wikitext-2 (32
  chunks), Q6_K scored *better* perplexity than the F16 baseline
  (8.8688 → lower) while Q8_0 lost 0.07 % — so the measured-quality walk
  order became Q6_K → Q8_0 → Q5_K_M → Q4_K_M, not the conventional
  Q8_0-first ranking. FiTuna sorts by measurement, so this is handled, not
  assumed away.
- **The near-miss is invisible without measuring.** Q5_K_M missed the
  target by 0.41 tok/s. Any heuristic that says "Q5 is enough for 30 tok/s
  on this class of hardware" ships a config that misses its target.
- **The answer is not just a quant — it's a config.** The winner is
  Q4_K_M at `-ngl 33` (not full offload 36): the binary search found the
  *minimal* GPU offload meeting the target, 30.81 tok/s, with measured
  quality loss 1.73 % (PPL 8.8688 → 9.0225), well inside the 5 % budget.

Robustness notes from the same session:

- During the minimal-ngl binary search, the `ngl=0` (CPU-only) probe of a
  4B model cannot finish a bench within the 300 s timeout. FiTuna records
  it as a below-target measurement and continues (`[Q4_K_M] ngl=0 bench
  timed out -- treating as 0 tok/s`) instead of aborting the search — this
  exact scenario is what motivated the `BenchTimeoutError` handling, found
  by hitting it on real hardware.
- Immediate re-run with `--resume`: **0.88 s** to the identical answer.
- Disk: 12.1 GB for the four quantized files (plus the 7.5 GB F16 base).
- Stage timings, measured: quality stage cold (baseline PPL + 4×
  quantize + 4× PPL) **5 m 01 s**; speed-search stage **12 m 53 s** (of
  which 5 m was the one deliberate ngl=0 timeout); full-cache `--resume`
  **0.88 s**.

## Run 3 — English vs Korean quality corpus (same model, same quants)

Motivation: quality loss is measured as perplexity increase on a corpus —
so which corpus? We measured Qwen3-4B-Instruct-2507 with the identical
quantized files against both the English default (wikitext-2 test split)
and Korean Wikipedia (`wikimedia/wikipedia` `20231101.ko`, first 500
articles, CC BY-SA), `--ppl-chunks 32`:

| Quant | Quality loss (EN wikitext) | Quality loss (KO kowiki) |
|---|---|---|
| Q6_K | −0.30 % | −0.06 % |
| Q8_0 | +0.07 % | −0.01 % |
| Q5_K_M | +1.53 % | +0.48 % |
| Q4_K_M | +1.73 % | +0.77 % |

Two honest observations:

- **The ranking happened to stay the same** (Q6_K best → Q4_K_M worst on
  both corpora). We do not claim the order always flips.
- **The magnitudes differ by >2×** — and that changes real verdicts. With
  `--max-quality-loss 1`, the English corpus kills Q5_K_M/Q4_K_M at the
  quality gate (early-exit A), the surviving quants are too slow, and the
  search honestly reports **BEST EFFORT (target not met)**. The Korean
  corpus passes all four, and Q4_K_M meets the target at ngl=34
  (30.06 tok/s, 0.77 % loss). Same model, same machine, same target, same
  budget — **the corpus alone flips feasibility.** If your users speak
  Korean, gate on Korean text (`--quality-corpus kowiki-corpus.txt`; export
  snippet in the README).

Incidentally, designing this experiment caught a real cache bug: quality
results were keyed by (model, quant, chunks) but not by corpus, so the
second corpus would silently reuse the first corpus's numbers. The cache
key now includes a corpus fingerprint — the tool's honesty is itself
regression-tested.

### Run-to-run variance (measured, not hidden)

Benchmark numbers on a laptop are thermally sensitive. A second fully-cold
session (fresh `--out`, machine already hot from an hour of continuous
benching) reproduced Q6_K/Q8_0/Q5_K_M within ±0.5 tok/s — but measured
Q4_K_M full-offload at 22.73 tok/s, vs 36.50 in the original session.
Three immediate direct `llama-bench` repeats of that exact config:

```
37.53 tok/s ± 0.20      31.97 tok/s ± 6.74      35.35 tok/s ± 3.26
```

So ~36 tok/s is the sustained figure and 22.73 was a thermal-throttle
outlier (note the internal std-dev exploding to ±6.7 while the machine was
loaded). Two practical consequences, both by design:

- FiTuna reports what it measured *in your session, under your thermal
  conditions* — which is exactly what you'll get when you run the resulting
  command right after.
- If a target sits within a few tok/s of a candidate's sustained speed
  (like 30 vs Q5_K_M's 29.6–29.7 here), treat the verdict as marginal and
  re-run the search when the machine is at its normal operating state. A
  roadmap item is to surface llama-bench's per-run std-dev in the report so
  marginal verdicts are flagged automatically.

