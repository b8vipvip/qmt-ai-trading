"""Deprecated compatibility map for old stage console artifacts.

The unified local console serves only `/api/v1/...` routes and the
`local_console_app` frontend. These legacy directories are read-only fallback
sources for report migration/lookup and must not be used by frontend code.
"""
from __future__ import annotations
LEGACY_STAGE_ARTIFACT_DIRS = {
    'datahub': ['local_console_datahub_stage88'],
    'research': ['local_console_research_stage88', 'local_console_factor_stage79'],
    'strategy': ['local_console_strategy_stage88'],
    'risk': ['local_console_risk_stage88'],
    'paper': ['local_console_paper_stage89'],
    'account_readonly': ['local_console_account_stage91'],
    'market': ['local_console_xtdata_live_stage87', 'local_console_xtdata_stage85', 'local_console_market_stage84'],
}
