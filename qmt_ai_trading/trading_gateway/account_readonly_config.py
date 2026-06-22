from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class AccountReadonlyConfig:
    enabled: bool = False
    dry_run: bool = True
    read_only: bool = True
    allow_import_xttrader: bool = False
    allow_create_xtquant_trader: bool = False
    allow_connect_trade_session: bool = False
    allow_account_query: bool = False
    allow_position_query: bool = False
    allow_order_query: bool = False
    allow_trade_query: bool = False
    allow_order_submit: bool = False
    allow_order_cancel: bool = False
    requires_human_approval: bool = True
    manual_confirmation_completed: bool = False
    mask_account_required: bool = True
    rate_limit_required: bool = True
    max_queries_per_minute: int = 3
    allow_auto_refresh: bool = False
    notes: str = "Stage91 account readonly boundary; order submit disabled"
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def default_account_readonly_config() -> AccountReadonlyConfig:
    return AccountReadonlyConfig()
