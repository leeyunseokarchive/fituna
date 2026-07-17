"""fituna.bench
===============

Runs ``llama-bench`` for a single (quant, ngl, ctx) candidate and parses its
JSON/CSV output into a :class:`~fituna.config.BenchResult`. Generation
throughput (``gen_tok_per_sec``) is the primary metric the search algorithm
optimizes against.
"""

from __future__ import annotations

from pathlib import Path

from fituna.config import BenchResult, BinaryPaths, TargetSpec


def run_bench(
    gguf_path: Path,
    ngl: int,
    ctx: int,
    target: TargetSpec,
    binaries: BinaryPaths,
    timeout_sec: int = 300,
) -> BenchResult:
    """Run:
        llama-bench -m <gguf_path> -ngl <ngl> -c <ctx>
                     -p <target.prompt_tokens> -n <target.gen_tokens> -o json
    and parse stdout into a BenchResult. Raises FiTunaError on timeout or
    non-zero exit / unparsable output.

    TODO: implement subprocess.run(..., timeout=timeout_sec) + json parse.
    """
    raise NotImplementedError
