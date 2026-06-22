from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class XtDataEnableRequest:
    request_id: str = "stage86-sandbox-enable-dry-run"
    requested_mode: str = "SANDBOX_ENABLE_DRY_RUN"
    requested_by: str = "local_operator"
    created_at: str = "2026-01-01T00:00:00+00:00#Stage86-default"
    enable_xtdata: bool = False
    enable_real_market_data: bool = False
    enable_realtime_subscribe: bool = False
    connect_miniqmt: bool = False
    allow_download_history: bool = False
    allow_query_instrument_detail: bool = False
    allow_query_financial_data: bool = False
    allow_xttrader: bool = False
    dry_run: bool = True
    read_only: bool = True
    requires_human_confirmation: bool = True
    manual_confirmation_completed: bool = False
    def to_dict(self): return asdict(self)
