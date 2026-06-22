"""Legacy stage artifact migration helpers only.

Formal console API routes must not import or read local_console_*_stageXX paths at runtime.
This module is intentionally reserved for migration scripts.
"""
from pathlib import Path
LEGACY_STAGE_PATTERNS=("local_console_*_stage*","market_data_test_stage*","agent_reports_stage*","monitoring_reports_stage*","dashboard_stage*")
def iter_legacy_stage_items(root='.'):
    base=Path(root)
    for pat in LEGACY_STAGE_PATTERNS:
        yield from base.glob(pat)
