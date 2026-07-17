"""Hardware detection tests -- subprocess calls will be monkeypatched once
detect_hardware()/parse_manual_hardware() are implemented.

Skeleton only: fituna.hardware functions currently raise NotImplementedError.
Un-skip as each function is implemented (see fituna/hardware.py TODOs).
"""

import pytest

from fituna.config import GPUVendor
from fituna.hardware import detect_hardware, parse_manual_hardware


@pytest.mark.xfail(reason="hardware.detect_hardware not yet implemented", strict=False)
def test_detect_hardware_returns_profile(monkeypatch):
    # TODO: monkeypatch subprocess.run for nvidia-smi/rocm-smi/system_profiler
    # and assert the parsed HardwareProfile fields.
    hw = detect_hardware()
    assert hw.os_name in {"linux", "darwin", "windows"}


@pytest.mark.xfail(
    reason="hardware.parse_manual_hardware not yet implemented", strict=False
)
def test_manual_gpu_overrides_detection():
    hw = parse_manual_hardware(gpu_vendor="nvidia", vram_mb=12000)
    assert hw.gpu_vendor == GPUVendor.NVIDIA
    assert hw.vram_mb == 12000
