"""fituna.quantize
==================

Thin, idempotent wrapper around the ``llama-quantize`` subprocess.
"""

from __future__ import annotations

from pathlib import Path

from fituna.config import BinaryPaths


def quantize(base_gguf: Path, quant: str, out_dir: Path, binaries: BinaryPaths) -> Path:
    """Run `llama-quantize <base_gguf> <out_dir>/<model>-<quant>.gguf <quant>`.

    If the target file already exists in out_dir, skip the subprocess call
    and return its path directly (idempotent / cache-friendly).

    TODO: implement subprocess.run + existence check.
    """
    raise NotImplementedError
