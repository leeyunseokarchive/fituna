"""fituna.binaries
==================

Locates required llama.cpp executables (on PATH or under a user-supplied
``--llama-bin-dir``), and introspects them (``--help``/``--version``) so
FiTuna never hardcodes a quant-type list that may drift from the user's
llama.cpp build.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fituna.config import BinaryPaths


def locate_binaries(bin_dir: Optional[Path] = None) -> BinaryPaths:
    """Find llama-quantize / llama-bench / llama-perplexity (required) and
    llama-imatrix / convert_hf_to_gguf.py (optional) in bin_dir if given,
    else on PATH (shutil.which).

    Raises BinaryNotFoundError with an install-guide message if any of the
    three required binaries is missing.

    TODO: implement.
    """
    raise NotImplementedError


def list_supported_quant_types(paths: BinaryPaths) -> list[str]:
    """Run `llama-quantize --help`, parse the listed quant type tokens
    (e.g. Q4_K_M, Q8_0, ...) out of its usage text.

    TODO: implement subprocess call + regex parse.
    """
    raise NotImplementedError


def get_llama_cpp_version(paths: BinaryPaths) -> Optional[str]:
    """Best-effort version string from `llama-bench --version` or similar.
    Returns None if the binary doesn't expose one.

    TODO: implement.
    """
    raise NotImplementedError
