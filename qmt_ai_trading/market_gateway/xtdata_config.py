from __future__ import annotations
from dataclasses import dataclass, asdict, field

@dataclass(frozen=True)
class XtDataAdapterConfig:
    enabled: bool = False
    dry_run: bool = True
    read_only: bool = True
    sandbox_fallback: bool = True
    allow_import_xtdata: bool = False
    allow_connect_miniqmt: bool = False
    allow_real_market_data: bool = False
    allow_realtime_subscribe: bool = False
    allow_download_history: bool = False
    allow_query_instrument_detail: bool = False
    allow_query_financial_data: bool = False
    allow_xttrader: bool = False
    qmt_path: str = ""
    mini_qmt_required: bool = False
    python_version_supported: bool = True
    notes: list[str] = field(default_factory=lambda: [
        "Stage85 boundary is disabled by default.",
        "No xtdata import, MiniQMT connection, real quote query, account query, or order submission is allowed.",
    ])

    def to_dict(self) -> dict:
        return asdict(self)
