from __future__ import annotations
import platform, sys
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(frozen=True)
class XtDataEnvironmentCheck:
    python_version: str
    platform: str
    repo_root: str
    qmt_config_placeholder_exists: bool
    sandbox_fallback_exists: bool
    sandbox_gateway_exists: bool
    stage85_config_exists: bool
    xtdata_import_attempted: bool = False
    mini_qmt_connection_attempted: bool = False
    real_market_data_attempted: bool = False
    environment_status: str = "PASS"
    warnings: tuple = ()
    def to_dict(self):
        d=asdict(self); d['warnings']=list(self.warnings); return d

def run_environment_check(repo_root='.'):
    root=Path(repo_root).resolve()
    warnings=[]
    sandbox_gateway=(root/'qmt_ai_trading/market_gateway/sandbox_gateway.py').exists()
    stage85=(root/'local_console_xtdata_stage85/xtdata_adapter_config.json').exists()
    if not stage85: warnings.append('Stage85 boundary config missing; fallback remains enabled')
    return XtDataEnvironmentCheck(
        python_version=sys.version.split()[0], platform=platform.platform(), repo_root=str(root),
        qmt_config_placeholder_exists=(root/'config/qmt_config.example.json').exists() or (root/'config').exists(),
        sandbox_fallback_exists=sandbox_gateway or (root/'local_console_market_stage84').exists(),
        sandbox_gateway_exists=sandbox_gateway, stage85_config_exists=stage85,
        environment_status='PASS' if sandbox_gateway else 'WARN', warnings=tuple(warnings))
