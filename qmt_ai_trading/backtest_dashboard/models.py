from __future__ import annotations
from dataclasses import dataclass
@dataclass
class BacktestDashboardRun:
    stage: str='Stage82'
    backtest_mode: str='mock_shadow'
    dry_run: bool=True
    not_live_trading: bool=True
    research_only: bool=True
