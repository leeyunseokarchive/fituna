"""fituna.report
================

Turns a :class:`~fituna.config.SearchResult` into a ready-to-run
``llama-cli`` command and a JSON / human-readable report.
"""

from __future__ import annotations

from pathlib import Path

from fituna.config import BinaryPaths, CandidateConfig, SearchResult


def build_run_command(
    gguf_path: Path, config: CandidateConfig, binaries: BinaryPaths
) -> list[str]:
    """e.g. ["llama-cli", "-m", str(gguf_path), "-ngl", str(config.ngl),
    "-c", str(config.ctx)]

    TODO: implement (locate llama-cli alongside binaries, or leave as bare
    command name if not resolvable).
    """
    raise NotImplementedError


def to_json(result: SearchResult) -> str:
    """Serialize SearchResult (and nested dataclasses) to a JSON string.

    TODO: implement (dataclasses.asdict + json.dumps, Path -> str).
    """
    raise NotImplementedError


def to_human(result: SearchResult) -> str:
    """Render a short human-readable summary: config, throughput, quality
    loss, meets_target, and the run command.

    TODO: implement.
    """
    raise NotImplementedError
