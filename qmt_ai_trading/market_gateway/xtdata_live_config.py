from __future__ import annotations
from dataclasses import asdict, dataclass, field

@dataclass(frozen=True)
class XtDataLiveReadOnlyConfig:
    enabled: bool = False
    allow_import_xtdata: bool = False
    allow_real_market_data: bool = False
    allow_connect_miniqmt: bool = False
    read_only: bool = True
    allow_xttrader: bool = False
    allow_account_query: bool = False
    allow_order_submit: bool = False
    sandbox_fallback: bool = True
    symbols: list[str] = field(default_factory=lambda: ["510300.SH", "510500.SH", "588000.SH"])
    period: str = "1d"
    limit: int = 100

    def to_dict(self) -> dict:
        return asdict(self)
