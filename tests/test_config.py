"""Dataclass immutability / defaults sanity checks for fituna.config."""

import dataclasses
from pathlib import Path

import pytest

from fituna.config import CandidateConfig, GPUVendor, HardwareProfile, TargetSpec


def test_hardware_profile_is_frozen():
    hw = HardwareProfile(
        gpu_vendor=GPUVendor.NONE,
        gpu_name=None,
        vram_mb=None,
        cpu_cores=8,
        ram_mb=16384,
        os_name="darwin",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        hw.cpu_cores = 4  # type: ignore[misc]


def test_target_spec_defaults():
    spec = TargetSpec(
        model_path=Path("model.gguf"),
        target_tokens_per_sec=20.0,
        max_quality_loss_pct=3.0,
    )
    assert spec.ctx == 4096
    assert spec.ctx_candidates == (4096,)
    assert spec.quant_candidates[0] == "Q8_0"


def test_candidate_config_is_hashable():
    c = CandidateConfig(quant="Q4_K_M", ngl=32, ctx=4096)
    assert hash(c) is not None
