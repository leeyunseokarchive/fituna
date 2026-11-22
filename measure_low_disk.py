# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FiTuna contributors

import argparse
import contextlib
import json
import time
from pathlib import Path

from fituna import cli, search


parser = argparse.ArgumentParser(description="저용량 모드 비교 측정")
parser.add_argument("mode", choices=["default", "low-disk"])
parser.add_argument("--out", type=Path, help="새로운 결과 폴더")
args = parser.parse_args()

# 이 스크립트는 프로젝트 최상위에 둔다.
project = Path(__file__).resolve().parent
data = project.parent / "fituna-measurement"
binaries = project.parent / "llama-bin"

model = data / "SmolLM2-135M-Instruct-f16.gguf"
corpus = data / "wiki.txt"
out = args.out.resolve() if args.out else data / args.mode

for path in (model, corpus):
    if not path.is_file():
        raise SystemExit(f"입력 파일을 찾을 수 없습니다: {path}")

# 이전 파일이나 캐시가 측정에 섞이지 않도록 새 폴더만 사용한다.
if out.exists():
    raise SystemExit(
        f"결과 폴더가 이미 있습니다: {out}\n"
        "--out 옵션으로 새로운 폴더를 지정하세요."
    )

out.mkdir(parents=True)

base_size = model.stat().st_size
stats = {
    "peak_gguf_bytes": base_size,
    "quantization_seconds": 0.0,
}

original_quantize = search.quantize


def measured_quantize(*call_args, **call_kwargs):
    """실제 양자화를 실행하고 시간과 완료된 GGUF 용량을 기록한다."""
    started = time.perf_counter()

    try:
        return original_quantize(*call_args, **call_kwargs)
    finally:
        stats["quantization_seconds"] += time.perf_counter() - started

        candidate_size = sum(
            path.stat().st_size for path in out.glob("*.gguf")
        )
        stats["peak_gguf_bytes"] = max(
            stats["peak_gguf_bytes"],
            base_size + candidate_size,
        )


# 두 모드는 동일한 입력과 설정을 사용한다.
command = [
    "run",
    "--model", str(model),
    "--quality-corpus", str(corpus),
    "--llama-bin-dir", str(binaries),
    "--out", str(out),
    "--gpu", "none",
    "--quant", "Q8_0,Q6_K,Q4_K_M",
    "--target-tps", "1",
    "--max-quality-loss", "20",
    "--ppl-chunks", "1",
    "--ctx", "512",
    "--resume",
    "--json",
]

if args.mode == "low-disk":
    command.append("--low-disk")

search.quantize = measured_quantize
started = time.perf_counter()

try:
    with (out / "report.json").open("w", encoding="utf-8") as report:
        with contextlib.redirect_stdout(report):
            exit_code = cli.main(command)
finally:
    elapsed = time.perf_counter() - started
    search.quantize = original_quantize

summary = {
    "mode": args.mode,
    "command": command,
    "exit_code": exit_code,
    "wall_seconds": elapsed,
    **stats,
    "remaining_candidates": [
        path.name for path in out.glob("*.gguf")
    ],
}

(out / "summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"측정 모드: {args.mode}")
print(f"종료 코드: {exit_code}")
print(f"전체 실행 시간: {elapsed:.2f}초")
print(f"양자화 함수 소요 시간: {stats['quantization_seconds']:.2f}초")
print(f"최대 GGUF 합계: {stats['peak_gguf_bytes'] / 1_000_000:.2f} MB")
print(f"남은 후보 파일 수: {len(summary['remaining_candidates'])}")
print(f"결과 저장 위치: {out}")

raise SystemExit(exit_code)