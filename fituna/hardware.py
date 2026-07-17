"""fituna.hardware
==================

Detects the local :class:`~fituna.config.HardwareProfile` by shelling out to
vendor CLIs (``nvidia-smi``, ``rocm-smi``, ``system_profiler``) with a
``platform``-module CPU-only fallback, and merges it with any user-supplied
overrides from the CLI.
"""

from __future__ import annotations

from typing import Optional

from fituna.config import GPUVendor, HardwareProfile


def detect_hardware() -> HardwareProfile:
    """Auto-detect GPU vendor/VRAM (nvidia-smi / rocm-smi / system_profiler)
    and CPU core count / RAM (platform, os) with a CPU-only fallback.

    TODO: implement subprocess probing, in priority order:
      1. nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
      2. rocm-smi --showproductname --showmeminfo vram
      3. system_profiler SPDisplaysDataType (Apple Silicon unified memory)
      4. fallback: GPUVendor.NONE, gpu_name=None, vram_mb=None
    """
    raise NotImplementedError


def parse_manual_hardware(
    gpu_vendor: Optional[str], vram_mb: Optional[int]
) -> HardwareProfile:
    """Build a HardwareProfile from user-supplied --gpu/--vram-mb, merged
    with detect_hardware() results. gpu_vendor=None -> pure auto-detect;
    otherwise the manual value(s) override the corresponding detected field(s).

    TODO: implement merge logic.
    """
    raise NotImplementedError
