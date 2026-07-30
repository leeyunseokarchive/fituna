# Measured end-to-end results

Real-hardware runs of `fituna run` against real llama.cpp binaries and real
open-weight models. Numbers below are what the tool actually printed —
reproduce them with the exact commands shown (absolute numbers vary by
machine and llama.cpp build; the *shape* of the outcome is the point).

**Environment (Runs 1–3 and 5)**

| | |
|---|---|
| Hardware | Apple M3 Pro, 18 GB unified memory (macOS, Apple Silicon) |
| llama.cpp | Homebrew build 9960 (`a935fbffe`) |
| Quality corpus | wikitext-2-raw-v1 test split (`--ppl-chunks 32`); Runs 3 and 5 additionally measure Korean Wikipedia |
| FiTuna | this repository — Runs 1–4 via `pip install -e .`, Run 5 invoked in-tree as `python3.13 -m fituna` (same package, no behavioural difference) |

Run 4 is the same experiment on **NVIDIA Tesla T4 (Linux, Google Colab)** —
see below.

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
  Korean, gate on Korean text (`--quality-corpus kowiki-corpus.txt`, fetched
  via `fituna fetch-corpus --lang ko --out kowiki-corpus.txt`).

**One qualification, added after Run 5.** These are `--ppl-chunks 32`
estimates, and Run 5 went back and measured the error bar FiTuna was
discarding at that chunk count — roughly ±3 percentage points of loss (see
"How big is a perplexity gap?"). That was measured on Run 5's model and files;
we no longer hold Run 3's quantized Qwen3-4B files to re-measure it here, so
for this run treat ±3 pp as inferred rather than measured. The flip above is
a fact about what the tool did — a user running those two commands gets those
two verdicts, and that remains the point of the experiment. What is **not**
established is that the underlying quality difference is larger than the
estimator can resolve: EN 1.73 % vs KO 0.77 % is a 0.96 pp cross-corpus gap,
unpaired, of the same order as that bar, with both figures straddling the 1 %
gate. So read it as "the corpus you gate on decides the verdict at this
budget", not as "Korean text provably degrades less" — Run 5 measured the
same comparison on a Korean model and could not establish the latter.

Incidentally, designing this experiment caught a real cache bug: quality
results were keyed by (model, quant, chunks) but not by corpus, so the
second corpus would silently reuse the first corpus's numbers. The cache
key now includes a corpus fingerprint — the tool's honesty is itself
regression-tested.

## Run 4 — NVIDIA Tesla T4, Linux (Google Colab)

Same model, same command, same target as Run 1 — different hardware.
Reproduced via
[notebooks/colab_nvidia_verification.ipynb](../notebooks/colab_nvidia_verification.ipynb)
(free T4 tier; llama.cpp built from source with CUDA). `fituna detect-hw`
correctly auto-detected `nvidia / Tesla T4 / 15360 MB VRAM / linux` via the
`nvidia-smi` parsing path.

| Candidate | Measured quality loss (T4/CUDA) | vs macOS/Metal | Measured gen tok/s (T4) | vs macOS | Verdict at target 240 |
|---|---|---|---|---|---|
| Q8_0 | — | — | 202.70 | 205.91 | miss |
| Q6_K | 0.83 % | 0.53 % | **205.50** | 249.50 | miss → **best effort** |
| Q5_K_M | — | — | 172.03 | 233.26 | miss |
| Q4_K_M | **5.22 % → killed by 5 % gate (early-exit A)** | 4.74 % → passed | never benched | 244.34 | — |

Cold search: **61 s**. `--resume` re-run: **1.45 s**, identical output.
Result: BEST EFFORT (Q6_K, 205.50 tok/s, 0.83 % loss) — the 240 tok/s
target that the M3 Pro meets is honestly reported as infeasible on the T4.

Three cross-platform facts a lookup table cannot know:

- **The quality gate verdict flipped between platforms.** Q4_K_M measured
  4.74 % loss under Metal (passes the 5 % budget) but 5.22 % under CUDA
  (killed at the gate). Same file, same corpus — different backend
  numerics, different feasible set. Same qualification as Run 3: 0.48 pp
  between two 32-chunk estimates is the same order as the ±3 pp bar Run 5
  measured on its own files, so what is established is that the two backends
  produced different verdicts here, not that a 0.48 pp gap would reproduce.
  This comparison is at least partly paired — identical corpus, identical
  file, only the backend differs — which the cross-corpus one in Run 3 is not.
- **The speed ranking is platform-specific.** On the T4, Q6_K outruns
  Q8_0 *and* Q5_K_M (which is slowest of the three); the M3 Pro ordering
  is different again.
- **Feasibility itself is hardware-relative** — the identical command
  passes on one machine and best-efforts on the other, which is precisely
  the answer a user needs before picking hardware or lowering a target.

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

## Run 5 — Midm-2.0-Mini-Instruct, a Korean open-weight model (MIT)

Runs 1–4 all used models trained primarily on English. Run 5 repeats the
Run 3 experiment — English vs Korean quality corpus, same model, same
quantized files — on a **Korean** open-weight model, to see whether the
corpus-sensitivity story holds up when the model itself is Korean.

The measured answer, stated up front: the loss *magnitudes* differ by corpus,
the final verdict does not, and the mid-table ranking difference we initially
reported as a finding **did not survive a stability check against our own
logs**. Details in "How big is a perplexity gap?" below.

Base model: `K-intelligence/Midm-2.0-Mini-Instruct` — 2,305,517,312
parameters, 48 layers. Its HuggingFace `license` field is `mit`, and
`LICENSE.txt` in the repository is the verbatim MIT text
("Copyright (c) 2025 KT Corporation"); the repo is not gated. We used the
ready-made BF16 GGUF from `mykor/Midm-2.0-Mini-Instruct-gguf`
(`Midm-2.0-Mini-Instruct-BF16.gguf`, 4,617,053,184 bytes = 4.30 GB), so no
`convert_hf_to_gguf.py`, torch or transformers was involved.

The redistributor gets its own licence check, because it is the party that
actually shipped us the bytes. `mykor/Midm-2.0-Mini-Instruct-gguf` declares
`license: mit` in its model-card front-matter, carries its own `LICENSE.txt`
that is the verbatim MIT text with the same "Copyright (c) 2025 KT
Corporation" notice as upstream, and declares
`base_model: K-intelligence/Midm-2.0-Mini-Instruct`. The HuggingFace API
reports `gated: false`, `private: false` for it. Both the upstream weights
and the GGUF conversion we actually ran are therefore MIT.

Corpora were fetched with the built-in stdlib downloader — no
`pip install datasets`:

```bash
fituna fetch-corpus --lang ko --out kowiki-corpus.txt   # 500 rows, 5.9 MB
fituna fetch-corpus --lang en --out wikitext-2-raw-test.txt  # 1000 rows, 316 KB
```

### How the target was chosen

A target must be able to fail. To pick one honestly we first ran the search
with a deliberately unreachable target (`--target-tps 9999`), which forces
every candidate through the quality gate *and* a full-offload bench instead
of early-exiting at the first winner. That probe cost **4 m 59.81 s** cold,
exited 3 (`BEST EFFORT`), and produced the measured full-offload band:

| Quant | measured gen tok/s @ ngl=48 |
|---|---|
| Q8_0 | 34.26 |
| Q5_K_M | 38.76 |
| Q6_K | 38.96 |
| Q4_K_M | 44.62 |

**40 tok/s** sits inside that band — above three candidates and below
exactly one. So it cannot be trivially passed (Q8_0, Q6_K and Q5_K_M all
genuinely miss) nor trivially failed (Q4_K_M genuinely clears it), and it is
a figure that splits the measured band rather than sitting outside it. Every
number below is from `--target-tps 40`.

### The two runs

```bash
# Korean quality corpus
fituna run --model Midm-2.0-Mini-Instruct-BF16.gguf \
  --target-tps 40 --max-quality-loss 5 --ctx 4096 \
  --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M --ppl-chunks 32 \
  --quality-corpus kowiki-corpus.txt --out ./out --resume

# English quality corpus — identical except the corpus
fituna run --model Midm-2.0-Mini-Instruct-BF16.gguf \
  --target-tps 40 --max-quality-loss 5 --ctx 4096 \
  --quant Q8_0,Q6_K,Q5_K_M,Q4_K_M --ppl-chunks 32 \
  --quality-corpus wikitext-2-raw-test.txt --out ./out --resume
```

| Candidate | File size | Quality loss (KO kowiki) | Quality loss (EN wikitext) | Measured gen tok/s (ngl=48, ctx 4096) | Verdict at target 40 |
|---|---|---|---|---|---|
| Q8_0 | 2.29 GB | **−0.02 %** | +0.15 % | 34.26 | miss — early-exit B |
| Q6_K | 1.77 GB | +0.59 % | +0.46 % | 38.96 | miss — early-exit B |
| Q5_K_M | 1.54 GB | +0.53 % | +1.00 % | 38.76 | miss — early-exit B |
| **Q4_K_M** | **1.33 GB** | **+2.58 %** | **+3.78 %** | **44.62** | **PASS (ngl=48)** |

Baseline perplexity of the BF16 base: **9.9511** on Korean, **8.7900** on
English. Every quality figure in that table is a `--ppl-chunks 32` estimate
carrying an error bar that `llama-perplexity` reports and FiTuna does not
store. We went back and measured it for every Korean row at this chunk count
rather than quoting one and assuming the rest: **±0.29318** (BF16 baseline),
**±0.29307** (Q8_0), **±0.29529** (Q6_K), **±0.29372** (Q5_K_M), **±0.30055**
(Q4_K_M) — about ±3 percentage points once expressed as loss, in every row.
Read "How big is a perplexity gap?" below before drawing conclusions from the
gaps between adjacent rows. Both runs end identically:

```
FiTuna result: MEETS TARGET

  quant           : Q4_K_M
  ngl             : 48
  ctx             : 4096

  prompt tok/s (pp): 305.88
  gen tok/s    (tg): 44.62

  perplexity      : 10.2082 (baseline 9.9511)   # Korean
  quality loss    : 2.58%
```

### How big is a perplexity gap? (the error bar we had been discarding)

Every quality figure above is a 32-chunk estimate, and `llama-perplexity`
prints an error bar next to each one that FiTuna never stored — its output
line is `Final estimate: PPL = 10.0099 +/- 0.29529`, and `quality.py`'s regex
captures the PPL and drops the `+/-`. Re-reading this run we could not say
whether the ranking difference below was signal, so we measured it: called the
binary directly on the same four files and both corpora, and extended the
sweep to **128 chunks** — 4× what the runs used, and the largest power of two
the English corpus supports (wikitext-2 test holds 143 chunks at `n_ctx=512`;
kowiki holds 2368). Extended, not repeated: as the second bullet below shows,
a 128-chunk run *contains* the 32-chunk one, so these two columns are not
independent replicates of each other.

```bash
llama-perplexity -m out/...-3e6680866409-Q6_K.gguf -f kowiki-corpus.txt --chunks 128
```

Invoked at `--chunks 32` it reproduces every cached Korean number exactly
(`9.9511`, `9.9488`, `10.0099`, `10.0037`, `10.2082`), so this is the same
measurement the tool makes, just with the error bar kept. That agreement is
a check on our plumbing, not a replication — the computation is deterministic
and, per the second bullet below, is the same one.

| Korean (kowiki) | PPL @128 chunks | loss @32 | loss @128 |
|---|---|---|---|
| BF16 baseline | 10.6238 ± 0.16350 | — | — |
| Q8_0 | 10.6187 ± 0.16335 | −0.02 % | −0.05 % |
| **Q5_K_M** | **10.7413 ± 0.16504** | **+0.53 %** | **+1.11 %** |
| **Q6_K** | **10.7470 ± 0.16569** | **+0.59 %** | **+1.16 %** |
| Q4_K_M | 11.0577 ± 0.17044 | +2.58 % | +4.08 % |

| English (wikitext-2) | PPL @128 chunks | loss @32 | loss @128 |
|---|---|---|---|
| BF16 baseline | 9.9155 ± 0.14863 | — | — |
| Q8_0 | 9.9217 ± 0.14873 | +0.15 % | +0.06 % |
| **Q6_K** | **9.9778 ± 0.14975** | **+0.46 %** | **+0.63 %** |
| **Q5_K_M** | **10.0197 ± 0.15035** | **+1.00 %** | **+1.05 %** |
| Q4_K_M | 10.2945 ± 0.15471 | +3.78 % | +3.82 % |

Five things follow, in order of how much they change the story:

- **The English ordering is stable across the whole run. The Korean ordering
  is not — it oscillates.** `llama-perplexity` prints a running perplexity
  after every chunk, so each of these runs is also 128 nested estimates, and
  reading them is a free stability test. On English, the margin between the
  two contested quants turns positive at n=4 and stays positive for all 125
  remaining points: Q6_K ranks above Q5_K_M at **every** chunk count we can
  read, zero sign changes. On Korean the same margin changes sign **nine
  times** after n=16, alternating between the two orderings in ten runs:

  | Korean, n = | 5–16 | 17–22 | 23–24 | 25–66 | 67 | 68–76 | 77–99 | 100–106 | 107–108 | 109–128 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | ahead | Q6_K | Q5_K_M | Q6_K | Q5_K_M | Q6_K | Q5_K_M | **Q6_K** | Q5_K_M | Q6_K | **Q5_K_M** |

  This is not a near-tie quietly settling down. Over n=77–99 — 23 consecutive
  points holding the *opposite* order to the one we publish — the mean absolute
  Korean margin is **0.0545 pp**, slightly *larger* than the **0.0537 pp** at
  n=128. The opposite ordering is held with equal or greater strength. At n=96
  the two corpora agree (both put Q6_K ahead) and there is no corpus reorder at
  all. Which order the Korean column reports is a function of where the run
  happens to stop.
- **Our 32- and 128-chunk numbers are one measurement, not two.**
  `llama-perplexity` always walks the corpus from the start, so a 128-chunk run
  *contains* its own 32-chunk run. Chunk `[32]` of the Korean Q8_0 trace is
  `9.9488` — exactly the value FiTuna cached at `--ppl-chunks 32` — and the
  same identity holds for Q6_K (`10.0099`), Q5_K_M (`10.0037`) and both
  baselines (`9.9511` Korean, `8.7900` English). "Reproduced at 32 chunks and
  again at 128" would be one nested measurement quoted twice; an earlier
  version of this section presented it as two independent confirmations. It
  is not evidence of stability. The per-chunk trace above is.
- **Neither margin clears the error bar, and the two are nowhere near equal.**
  At 128 chunks each perplexity carries ±0.15–0.17, which is ±1.5 percentage
  points once expressed as loss. The English margin (0.423 pp) is about a
  quarter of that; the Korean margin at n=128 (0.054 pp) is about a
  twenty-ninth. So the English half of the ordering difference is ~8× stronger
  than the Korean half — and, unlike it, holds its sign everywhere.
- **The `+/-` we can quote is not quite the one we want.** It is the
  corpus-sampling error on an absolute perplexity — how much this number would
  move on a *different* sample of Korean text. Comparing two quants scored on
  *identical* chunks is a paired comparison whose error is much smaller, which
  is how the English margin can sit at a quarter of an error bar and still hold
  its sign over 125 consecutive chunk counts. `llama-perplexity` does not report
  that paired error, so we cannot attach a confidence level to either margin.
  What the per-chunk traces give us instead is a direct stability test that
  needs no error model at all — and the Korean margin fails it.
- **Absolute loss is strongly chunk-count dependent — always quote the chunk
  count.** Q4_K_M's Korean loss is 2.58 % at 32 chunks and 4.08 % at 128;
  Q6_K's goes 0.59 % → 1.16 %. The 32-chunk figures in the table above are
  exactly what the documented commands produced and what the cache holds, but
  they are estimates over 32×512 tokens, not properties of the quant. Of the
  four, only Q4_K_M's degradation is big enough to clear its own error bar
  (Δppl 0.434 against ±0.17 at 128 chunks).

### What a lookup table cannot know

- **A corpus-driven reorder was not demonstrated.** Sorted by measured loss
  the two runs do report different mid-table orders — Q8_0 → **Q5_K_M → Q6_K**
  → Q4_K_M on Korean, Q8_0 → **Q6_K → Q5_K_M** → Q4_K_M on English — and that
  is genuinely what a user gets from these commands. But a reorder needs both
  halves to be real, and only the English half survives measurement. English
  puts Q6_K ahead of Q5_K_M at every chunk count from 4 to 128, without a
  single sign change. The Korean order between those same two quants changes
  sign nine times over the same trace, and holds the *English* order over
  n=77–99 at least as strongly as it holds the opposite one at n=128; at n=96
  the two corpora agree outright and there is no reorder to report. So we
  cannot say the corpus reordered the ranking — we can only say the Korean
  column is not stable enough to be ordered. Run 3 measured this same
  comparison on an English-trained model and reported plainly that "the ranking
  happened to stay the same — we do not claim the order always flips"; Run 5
  does not get to claim it either. Earlier versions of this section led with
  "the corpus flipped the measured quality ranking" and then called the flip
  reproducible; the per-chunk trace in "How big is a perplexity gap?" above
  refutes both — and it is our own log that does it. That is the tool working
  as intended: a plausible assumption of ours failed under our own measurement.
- **Q8_0 changed sign — and this one *is* stable across the trace.** It
  scored −0.02 % (32 chunks) and −0.05 % (128) on Korean — very slightly
  *better* perplexity than the BF16 base it was quantized from — against
  +0.15 % and +0.06 % on English. Unlike the Q6_K/Q5_K_M ordering above, this
  holds up when read chunk by chunk: Korean Q8_0 is below its baseline at
  117 of the 125 points from n=4 to n=128 (one sign change, early), and
  English Q8_0 is above its baseline at all 125. A table that stores "Q8_0 ≈
  lossless" hides which side of zero you land on. On a Δppl of 0.005–0.013
  against a ±0.16 error bar we still will not call it a resolved result — but
  it is a consistent observation, which is more than the ranking difference
  managed.
- **Run 3's "Korean losses are smaller" pattern does not generalize.** In
  Run 3 the Korean figure was smaller than its English counterpart in three
  of four rows — Q6_K is already the exception there (−0.06 % Korean vs
  −0.30 % English). In the 32-chunk table above the pattern holds for Q8_0
  (−0.02 vs +0.15), Q5_K_M (0.53 vs 1.00) and Q4_K_M (2.58 vs 3.78), and is
  **reversed for Q6_K** alone (0.59 Korean vs 0.46 English, a 0.14 pp
  difference well inside the ±1.5 pp error bars). Read chunk by chunk it is
  weaker still: across n=4–128 the Korean figure is the smaller one at 125 of
  125 points for Q8_0, but only 73/125 for Q4_K_M, 50/125 for Q5_K_M and
  4/125 for Q6_K. So it was never a clean rule, and only Q8_0 obeys it
  robustly here: the direction of the corpus effect is per-quant and has to be
  measured.
- **The verdict did *not* flip this time — and we say so.** Unlike Run 3,
  where a 1 % budget let the corpus alone decide feasibility, here at
  `--max-quality-loss 5` all four candidates clear the gate on *both*
  corpora, and both runs pick the identical winning config. The corpus moved
  the numbers, not the final answer — and, per the bullet above, not
  demonstrably the ranking either. That is what we measured; we are not going
  to dress it up as a flip.
- **The "minimal ngl" answer was `all of them`, and the margin is one
  layer.** FiTuna's binary search over `-ngl` returned the full 48 because
  nothing smaller works. The measured offload curve for Q4_K_M:

  | ngl | 0 | 24 | 36 | 42 | 45 | 47 | 48 |
  |---|---|---|---|---|---|---|---|
  | gen tok/s | timed out | 10.86 | 17.56 | 23.53 ⚠ | 32.43 | **39.32** | **44.62** |
  | llama-bench std-dev | — | ±0.05 | ±0.37 | **±4.94** ⚠ | ±0.26 | ±0.15 | ±1.25 |

  Moving a **single** layer of 48 off the GPU costs 5.30 ± 1.26 tok/s — call
  it 4.0 to 6.6, or 11.9 % ± 2.8 pp of throughput — and lands at 39.32,
  missing the 40 target by 0.68 (that one *is* sharp: 4.5σ against ngl=47's
  ±0.15). The curve is nowhere near linear in layer count either: half the
  layers on GPU (ngl=24) buys 10.86 tok/s, which is 24 % of full-offload
  speed, not 50 %. No static rule of thumb reproduces that shape.

  ⚠ **The ngl=42 point is thermally contaminated and we are not going to
  publish it as clean.** Its five llama-bench samples were
  `[25.81, 25.69, 25.59, 25.84, 14.69]` — four tightly clustered at 25.73
  ±0.12 plus one collapsed run, which drags the reported mean down 8.6 % to
  23.53 and blows the std-dev out to ±4.94, roughly 4× the worst of any other
  point in the curve. This is the same signature Run 4's "Run-to-run variance"
  section documents. Three direct re-runs of the identical command
  (`llama-bench -m ...-Q4_K_M.gguf -ngl 42 -d 3456 -p 512 -n 128`) reproduced
  the instability rather than resolving it, but they were taken with the
  machine already hot from an hour of continuous perplexity work, so they
  establish only that the config is genuinely thermally marginal — not the
  cool-machine value:

  ```
  19.84 ± 3.96      18.64 ± 3.57      19.32 ± 4.44
  ```

  Every one of the three collapsed the same way inside its own five samples
  (e.g. `[21.97, 22.40, 23.13, 15.55, 13.53]`).

  Prompt processing at the same setting fell from 100.55 tok/s in the
  original session to ~80 in all three repeats, i.e. the whole machine was
  throttled ~20 %, which is why we flag the point rather than substituting a
  new number for it. Treat 23.53 as a lower bound with a bad error bar; the
  binary search's decision (ngl=42 is below target 40) is unaffected either
  way, since even the four clean samples average 25.73.
- **One speed inversion, honestly qualified.** Q6_K (1.77 GB) measured
  *faster* than the smaller Q5_K_M (1.54 GB), 38.96 vs 38.76 — the
  size-implies-speed heuristic pointing the wrong way again. But llama-bench's
  own per-run std-devs here are ±0.53 and ±0.11 tok/s, so unlike Run 1's
  clear-cut inversion this 0.20 tok/s gap is **within run-to-run noise**. We
  report it as "indistinguishable", not as a win for Q6_K. Either way the
  practical point stands: paying 15 % more disk for Q6_K bought no measurable
  speed and no better Korean quality.

### Timings and disk (measured)

| | |
|---|---|
| Target-selection probe (cold: baseline PPL + 4× quantize + 4× PPL + 4× bench) | **4 m 59.81 s** |
| Korean run at target 40 (cold `-ngl` binary search, 6 new benches — the 7th curve point, ngl=48, was a cache hit from the probe) | **12 m 54.93 s** |
| ↳ of which the deliberate `ngl=0` bench timeout | 5 m 00 s |
| English run at target 40 (cold quality stage, all benches cached) | **1 m 53.19 s** |
| Korean re-run with `--resume` | **1.47 s** |
| English re-run with `--resume` | **1.42 s** |

Both `--resume` re-runs reproduce their full reports byte-for-byte from
`out/.fituna_cache.sqlite3`, and this time we kept the artifact: the report
block from each resumed run was `diff -u`'d against the report block captured
in the original cold-run logs (`run5-ko.log`, `run5-en.log`) and came back
identical — 434 bytes Korean, 433 bytes English, both exit 0. The two
`--resume` timings above are from that verification run, on a machine hot from
an hour of continuous benching; an earlier session recorded 0.955 s / 0.908 s
but left no artifact on disk, so we quote the numbers we can show. Disk:
**6.9 GB** for the four quantized files plus the 4.30 GB BF16 base (11 GB
total working set).

The `ngl=0` CPU-only probe of this 2.3B model could not finish a bench inside
the 300 s timeout, and FiTuna logged
`[Q4_K_M] ngl=0 bench timed out -- treating as 0 tok/s (below target)` and
carried on — the same `BenchTimeoutError` path Run 2 hit on a 4B model,
reproduced here on a second model class.

