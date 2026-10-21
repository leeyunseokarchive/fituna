# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FiTuna contributors
"""GGUF header parser tests for fituna.model_info.

Builds synthetic GGUF bytes in-process (no network, no llama.cpp). Covers the
happy paths (v3 and v1), the untrusted-length guards, missing-metadata errors,
is_already_quantized(), and model_fingerprint(). Does not modify model_info.py.
"""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from fituna.config import BinaryPaths, FiTunaError, ModelInfo
from fituna.model_info import (
    _T_ARRAY,
    _T_STRING,
    _T_UINT32,
    _build_synthetic_gguf,
    is_already_quantized,
    model_fingerprint,
    read_model_info,
)

# GGUF value type ids used only by the local byte builder
_T_UINT8 = 0
_T_FLOAT32 = 6
_T_UINT64 = 10

_GGUF_MAGIC = b"GGUF"


# ---------------------------------------------------------------------------
# helpers: local GGUF byte builder (self-contained variants of the demo builder)
# ---------------------------------------------------------------------------


def _binaries(tmp_path: Path) -> BinaryPaths:
    return BinaryPaths(
        llama_quantize=tmp_path / "llama-quantize",
        llama_bench=tmp_path / "llama-bench",
        llama_perplexity=tmp_path / "llama-perplexity",
    )


def _pack_length(version: int, n: int) -> bytes:
    return struct.pack("<Q", n) if version >= 2 else struct.pack("<I", n)


def _write_string(buf: bytearray, s: str, version: int) -> None:
    encoded = s.encode("utf-8")
    buf += _pack_length(version, len(encoded))
    buf += encoded


def _write_value(buf: bytearray, value_type: int, value, version: int) -> None:
    if value_type == _T_STRING:
        _write_string(buf, value, version)
        return
    if value_type == _T_ARRAY:
        elem_type, elements = value
        buf += struct.pack("<I", elem_type)
        buf += _pack_length(version, len(elements))
        for elem in elements:
            _write_value(buf, elem_type, elem, version)
        return
    formats = {
        _T_UINT8: ("<B",),
        _T_UINT32: ("<I",),
        _T_FLOAT32: ("<f",),
        _T_UINT64: ("<Q",),
    }
    fmt = formats[value_type][0]
    buf += struct.pack(fmt, value)


def _build_gguf(
    *,
    version: int = 3,
    kvs: list[tuple[str, int, object]] | None = None,
    tensors: list[tuple[str, list[int], int, int]] | None = None,
) -> bytes:
    """Build a minimal spec-shaped GGUF.

    kvs: (key, value_type, value) where value is a Python scalar/str, or for
    ARRAY a (elem_type, [elements]) pair.
    tensors: (name, dims, ggml_type, offset).
    """
    if kvs is None:
        kvs = [
            ("general.architecture", _T_STRING, "testarch"),
            ("testarch.block_count", _T_UINT32, 32),
            ("general.file_type", _T_UINT32, 1),  # F16
        ]
    if tensors is None:
        tensors = [("test.weight", [4, 8], 0, 0)]

    buf = bytearray()
    buf += _GGUF_MAGIC
    buf += struct.pack("<I", version)
    if version >= 2:
        buf += struct.pack("<Q", len(tensors))
        buf += struct.pack("<Q", len(kvs))
    else:
        buf += struct.pack("<I", len(tensors))
        buf += struct.pack("<I", len(kvs))

    for key, value_type, value in kvs:
        _write_string(buf, key, version)
        buf += struct.pack("<I", value_type)
        _write_value(buf, value_type, value, version)

    for name, dims, ggml_type, offset in tensors:
        _write_string(buf, name, version)
        buf += struct.pack("<I", len(dims))
        for dim in dims:
            if version >= 2:
                buf += struct.pack("<Q", dim)
            else:
                buf += struct.pack("<I", dim)
        buf += struct.pack("<I", ggml_type)
        buf += struct.pack("<Q", offset)

    return bytes(buf)


def _write_gguf(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------------------
# 1 / 2: valid v3 and v1
# ---------------------------------------------------------------------------


def test_read_model_info_valid_gguf_v3(tmp_path: Path):
    path = _write_gguf(tmp_path, "v3.gguf", _build_gguf(version=3))
    info = read_model_info(path, _binaries(tmp_path))
    assert info.architecture == "testarch"
    assert info.n_layers == 32
    assert info.n_params == 32  # 4 * 8
    assert info.file_type == 1
    assert info.base_gguf_path == path


def test_read_model_info_reuses_synthetic_builder(tmp_path: Path):
    """Plain v3 from model_info._build_synthetic_gguf (no file_type key)."""
    path = _write_gguf(tmp_path, "synthetic.gguf", _build_synthetic_gguf())
    info = read_model_info(path, _binaries(tmp_path))
    assert info.architecture == "testarch"
    assert info.n_layers == 32
    assert info.n_params == 32
    assert info.file_type is None


def test_read_model_info_valid_gguf_v1(tmp_path: Path):
    path = _write_gguf(tmp_path, "v1.gguf", _build_gguf(version=1))
    info = read_model_info(path, _binaries(tmp_path))
    assert info.architecture == "testarch"
    assert info.n_layers == 32
    assert info.n_params == 32
    assert info.file_type == 1


# ---------------------------------------------------------------------------
# 3: bad magic and truncated header
# ---------------------------------------------------------------------------


def test_read_model_info_bad_magic_raises(tmp_path: Path):
    path = _write_gguf(tmp_path, "bad.gguf", b"NOPE" + b"\x00" * 32)
    with pytest.raises(FiTunaError, match="bad magic"):
        read_model_info(path, _binaries(tmp_path))


def test_read_model_info_truncated_header_raises(tmp_path: Path):
    full = _build_gguf(version=3)
    # Cut partway through the KV section (after magic+version+counts).
    truncated = full[:20]
    path = _write_gguf(tmp_path, "trunc.gguf", truncated)
    with pytest.raises(FiTunaError):
        read_model_info(path, _binaries(tmp_path))


# ---------------------------------------------------------------------------
# 4 / 5 / 6: untrusted-length and unknown-type guards
# ---------------------------------------------------------------------------


def test_read_model_info_oversized_string_length_raises(tmp_path: Path):
    """A string length larger than the remaining file must raise before any
    attempt to read that many bytes (the guard in _read_exact)."""
    version = 3
    buf = bytearray()
    buf += _GGUF_MAGIC
    buf += struct.pack("<I", version)
    buf += struct.pack("<Q", 0)  # tensor_count
    buf += struct.pack("<Q", 1)  # kv_count
    _write_string(buf, "general.architecture", version)
    buf += struct.pack("<I", _T_STRING)
    # Claim a multi-GB string while leaving almost no payload bytes.
    buf += struct.pack("<Q", 10**12)
    buf += b"x"  # one byte of "string" data

    path = _write_gguf(tmp_path, "huge_str.gguf", bytes(buf))
    with pytest.raises(FiTunaError, match="length exceeds remaining file size"):
        read_model_info(path, _binaries(tmp_path))


def test_read_model_info_oversized_array_count_raises(tmp_path: Path):
    version = 3
    buf = bytearray()
    buf += _GGUF_MAGIC
    buf += struct.pack("<I", version)
    buf += struct.pack("<Q", 0)
    buf += struct.pack("<Q", 1)
    _write_string(buf, "dummy.array", version)
    buf += struct.pack("<I", _T_ARRAY)
    buf += struct.pack("<I", _T_UINT8)  # elem type
    # count larger than any possible file contents
    buf += struct.pack("<Q", 10**12)

    path = _write_gguf(tmp_path, "huge_arr.gguf", bytes(buf))
    with pytest.raises(FiTunaError, match="array element count exceeds"):
        read_model_info(path, _binaries(tmp_path))


def test_read_model_info_unknown_value_type_raises(tmp_path: Path):
    version = 3
    unknown_type = 99
    buf = bytearray()
    buf += _GGUF_MAGIC
    buf += struct.pack("<I", version)
    buf += struct.pack("<Q", 0)
    buf += struct.pack("<Q", 1)
    _write_string(buf, "dummy.unknown", version)
    buf += struct.pack("<I", unknown_type)
    # no value bytes; parser must reject the type id first

    path = _write_gguf(tmp_path, "unknown_type.gguf", bytes(buf))
    with pytest.raises(FiTunaError, match="unknown GGUF value type id 99"):
        read_model_info(path, _binaries(tmp_path))


# ---------------------------------------------------------------------------
# 7: missing required metadata
# ---------------------------------------------------------------------------


def test_read_model_info_missing_architecture_raises(tmp_path: Path):
    data = _build_gguf(
        version=3,
        kvs=[("testarch.block_count", _T_UINT32, 32)],
        tensors=[],
    )
    path = _write_gguf(tmp_path, "no_arch.gguf", data)
    with pytest.raises(FiTunaError, match="general.architecture"):
        read_model_info(path, _binaries(tmp_path))


def test_read_model_info_missing_block_count_raises(tmp_path: Path):
    data = _build_gguf(
        version=3,
        kvs=[("general.architecture", _T_STRING, "testarch")],
        tensors=[],
    )
    path = _write_gguf(tmp_path, "no_blocks.gguf", data)
    with pytest.raises(FiTunaError, match="testarch.block_count"):
        read_model_info(path, _binaries(tmp_path))


# ---------------------------------------------------------------------------
# 8: is_already_quantized
# ---------------------------------------------------------------------------


def _info_with_file_type(file_type: int | None) -> ModelInfo:
    return ModelInfo(
        architecture="x",
        n_layers=1,
        n_params=1,
        base_gguf_path=Path("x.gguf"),
        file_type=file_type,
    )


@pytest.mark.parametrize(
    "file_type, expected",
    [
        (None, False),
        (0, False),   # F32
        (1, False),   # F16
        (32, False),  # BF16
        (15, True),   # Q4_K_M
    ],
)
def test_is_already_quantized(file_type: int | None, expected: bool):
    assert is_already_quantized(_info_with_file_type(file_type)) is expected


# ---------------------------------------------------------------------------
# 9: model_fingerprint
# ---------------------------------------------------------------------------


def test_model_fingerprint_stable_and_name_sensitive(tmp_path: Path):
    data = _build_gguf(version=3)
    a = _write_gguf(tmp_path, "a.gguf", data)
    b = _write_gguf(tmp_path, "b.gguf", data)

    fp1 = model_fingerprint(a)
    fp2 = model_fingerprint(a)
    assert fp1 == fp2
    assert len(fp1) == 64
    assert model_fingerprint(b) != fp1
