from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ArtifactMapping:
    logical_name: str
    stage: str
    canonical: str
    legacy: tuple[str, ...]
    category: str

class ArtifactPathRegistry:
    def __init__(self, repo_root: str | Path = '.'):
        self.repo_root = Path(repo_root)
        self._mappings = _default_mappings()

    def canonical_path(self, logical_name: str, stage: int | str = '') -> Path:
        key = _key(logical_name, stage)
        rel = self._mappings.get(key, _generic_mapping(logical_name, stage)).canonical
        return self.repo_root / rel

    def legacy_paths(self, logical_name: str, stage: int | str = '') -> list[Path]:
        key = _key(logical_name, stage)
        mapping = self._mappings.get(key, _generic_mapping(logical_name, stage))
        return [self.repo_root / p for p in mapping.legacy]

    def resolve(self, logical_name: str, stage: int | str = '') -> Path:
        canonical = self.canonical_path(logical_name, stage)
        if canonical.exists():
            return canonical
        for path in self.legacy_paths(logical_name, stage):
            if path.exists():
                return path
        return canonical

    def as_dict(self) -> dict:
        return {'version':'stage87','read_strategy':['canonical_first','legacy_fallback'],'write_strategy':'stage87_writes_canonical_and_legacy_copy_when_needed','mappings':[m.__dict__ | {'legacy':list(m.legacy)} for m in self._mappings.values()]}

def _stage(stage: int | str) -> str:
    s=str(stage).lower().replace('stage','')
    return f'stage{s}' if s else ''

def _key(logical_name: str, stage: int | str) -> tuple[str,str]:
    return (logical_name, _stage(stage))

def _default_mappings() -> dict[tuple[str,str], ArtifactMapping]:
    items = [
        ArtifactMapping('local_console_app','stage86','artifacts/console_apps/stage86',('local_console_app_stage86',),'console_apps'),
        ArtifactMapping('local_console_app','stage87','artifacts/console_apps/stage87',('local_console_app_stage87',),'console_apps'),
        ArtifactMapping('xtdata_enable','stage86','artifacts/reports/stage86/xtdata_enable',('local_console_xtdata_enable_stage86',),'reports'),
        ArtifactMapping('market_gateway','stage84','artifacts/reports/stage84/market_gateway',('local_console_market_stage84',),'reports'),
        ArtifactMapping('xtdata_live','stage87','artifacts/reports/stage87/xtdata_live',('local_console_xtdata_live_stage87',),'reports'),
        ArtifactMapping('artifact_migration','stage87','artifacts/reports/stage87/artifact_migration',('local_console_artifact_migration_stage87',),'reports'),
        ArtifactMapping('validation_logs','','artifacts/validation/logs',('validation_logs',),'validation'),
    ]
    return {(m.logical_name,m.stage):m for m in items}

def _generic_mapping(logical_name: str, stage: int | str) -> ArtifactMapping:
    st=_stage(stage); suffix=f'/{st}' if st else ''
    return ArtifactMapping(logical_name, st, f'artifacts/reports{suffix}/{logical_name}', (f'{logical_name}_{st}' if st else logical_name,), 'reports')
