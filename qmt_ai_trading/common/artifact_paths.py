from __future__ import annotations
from pathlib import Path
from .artifact_registry import ArtifactPathRegistry

def resolve_artifact_path(logical_name: str, stage: int | str = '', repo_root: str | Path = '.') -> Path:
    return ArtifactPathRegistry(repo_root).resolve(logical_name, stage)
