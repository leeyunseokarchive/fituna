"""fituna.config
================

Shared types for every FiTuna module: :class:`Enum`/``frozen`` ``dataclass``
value objects and the :class:`FiTunaError` exception hierarchy.

This module is the interface contract. No module outside ``config.py``
defines its own cross-module type -- everyone imports from here. Keep every
dataclass ``frozen=True`` (immutable, hashable-friendly) so passing them
between modules can never produce spooky action-at-a-distance bugs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class GPUVendor(str, Enum):
    NONE = "none"
    NVIDIA = "nvidia"
    AMD = "amd"
    APPLE = "apple"


@dataclass(frozen=True)
class HardwareProfile:
    gpu_vendor: GPUVendor
    gpu_name: Optional[str]  # 없으면 None
    vram_mb: Optional[int]  # 없으면 None
    cpu_cores: int
    ram_mb: int
    os_name: str  # "linux" | "darwin" | "windows"


@dataclass(frozen=True)
class TargetSpec:
    model_path: Path  # .gguf 파일 또는 HF 포맷 디렉토리
    target_tokens_per_sec: float  # generation(tg) 기준 목표 속도
    max_quality_loss_pct: float  # baseline 대비 perplexity 증가 허용 상한(%)
    prompt_tokens: int = 512  # bench용 pp 길이
    gen_tokens: int = 128  # bench용 tg 길이
    ctx: int = 4096  # 필요 컨텍스트 길이(주 탐색 기준값)
    ctx_candidates: tuple[int, ...] = (4096,)  # 다중 지정 시 각각 검증, ctx가 그중 하나로 강제 포함
    quant_candidates: tuple[str, ...] = (
        "Q8_0",
        "Q6_K",
        "Q5_K_M",
        "Q4_K_M",
        "Q3_K_M",
        "Q2_K",
    )  # 품질 내림차순 고정 순서
    ngl_max_calls: int = 6  # ngl 이진탐색 상한 호출 수(안전장치)
    max_bench_seconds: Optional[int] = None  # 전체 탐색 시간 예산, 초과 시 best-effort 반환


@dataclass(frozen=True)
class BinaryPaths:
    llama_quantize: Path
    llama_bench: Path
    llama_perplexity: Path
    llama_imatrix: Optional[Path] = None
    convert_script: Optional[Path] = None  # HF->GGUF 변환용 (llama.cpp 저장소 내 스크립트)


@dataclass(frozen=True)
class ModelInfo:
    architecture: str
    n_layers: int
    n_params: int
    base_gguf_path: Path  # 양자화 기준 원본(F16/F32) GGUF


@dataclass(frozen=True)
class CandidateConfig:
    quant: str
    ngl: int
    ctx: int


@dataclass(frozen=True)
class BenchResult:
    candidate: CandidateConfig
    prompt_tok_per_sec: float
    gen_tok_per_sec: float
    vram_used_mb: Optional[int]
    raw_stdout: str


@dataclass(frozen=True)
class QualityResult:
    candidate_quant: str  # quality는 quant에만 의존(ngl/ctx 무관)
    perplexity: float
    baseline_perplexity: float
    quality_loss_pct: float  # (perplexity-baseline)/baseline*100


@dataclass(frozen=True)
class SearchResult:
    config: CandidateConfig
    bench: BenchResult
    quality: QualityResult
    gguf_path: Path
    run_command: list[str]  # 사용자가 그대로 실행 가능한 llama-cli 커맨드
    meets_target: bool  # False면 best-effort(목표 미달) 결과


class FiTunaError(Exception):
    """Base class for all FiTuna errors."""


class BinaryNotFoundError(FiTunaError):
    """Raised when a required llama.cpp binary could not be located."""


class ModelConversionError(FiTunaError):
    """Raised when HF -> GGUF conversion fails."""


class NoFeasibleConfigError(FiTunaError):
    """Raised when no candidate configuration could satisfy the target at all."""

    def __init__(self, message: str, closest: Optional["SearchResult"] = None) -> None:
        super().__init__(message)
        self.closest = closest
