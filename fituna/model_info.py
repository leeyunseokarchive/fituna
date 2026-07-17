"""fituna.model_info
====================

Ensures a base F16/F32 GGUF exists for the input model (converting from a HF
directory via llama.cpp's convert script if needed) and reads back model
metadata (architecture, layer count, param count) plus a cheap fingerprint
used as a cache key.
"""

from __future__ import annotations

from pathlib import Path

from fituna.config import BinaryPaths, ModelInfo


def ensure_base_gguf(model_path: Path, work_dir: Path, binaries: BinaryPaths) -> Path:
    """If model_path is already a .gguf file, return it unchanged. If it's an
    HF-format directory, invoke binaries.convert_script via subprocess to
    produce work_dir/base-f16.gguf and return that path.

    Raises ModelConversionError on subprocess failure or missing convert_script.

    TODO: implement.
    """
    raise NotImplementedError


def read_model_info(gguf_path: Path, binaries: BinaryPaths) -> ModelInfo:
    """Read architecture / n_layers / n_params from the GGUF header (e.g. via
    a llama.cpp helper binary or by parsing the GGUF metadata directly with
    `struct`).

    TODO: implement.
    """
    raise NotImplementedError


def model_fingerprint(path: Path) -> str:
    """sha256(f'{path.name}:{size}:{mtime}') -- a low-cost identity fingerprint
    used as a cache key, deliberately NOT a full-file hash (large GGUFs can be
    tens of GB).

    TODO: implement with hashlib + Path.stat().
    """
    raise NotImplementedError
