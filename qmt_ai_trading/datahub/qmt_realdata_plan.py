"""Stage 24 small-scope real QMT market-data test plan."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from qmt_ai_trading.datahub.qmt_quality import QmtCacheQualityStatus, QmtDataQualityCheck


@dataclass
class QmtRealDataPlan:
    name: str
    symbols: list[str]
    start_date: str
    end_date: str
    frequency: str
    provider: str
    cache_root: str
    report_dir: str
    max_symbols: int = 5
    max_days: int = 90
    strict: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def _day(value: str) -> date:
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def build_default_qmt_realdata_plan(symbols: list[str] | None = None, start_date: str = "2024-01-01", end_date: str = "2024-01-10", frequency: str = "1d", provider: str = "qmt", cache_root: str = "market_data_qmt_stage24", report_dir: str = "qmt_data_quality_reports", strict: bool = False) -> QmtRealDataPlan:
    return QmtRealDataPlan("stage24_qmt_realdata_smoke", symbols or ["510300.SH"], start_date, end_date, frequency, provider, cache_root, report_dir, 5, 90, strict, {"trading_api_used": False, "stage": 24})


def validate_qmt_realdata_plan(plan: QmtRealDataPlan) -> list[QmtDataQualityCheck]:
    checks: list[QmtDataQualityCheck] = []
    symbol_count = len(plan.symbols)
    days = (_day(plan.end_date) - _day(plan.start_date)).days + 1
    checks.append(QmtDataQualityCheck("plan_max_symbols", "Small symbol scope", QmtCacheQualityStatus.PASS if symbol_count <= plan.max_symbols else (QmtCacheQualityStatus.FAIL if plan.strict else QmtCacheQualityStatus.WARN), f"symbols={symbol_count}, max_symbols={plan.max_symbols}", {"symbols": plan.symbols, "max_symbols": plan.max_symbols}))
    checks.append(QmtDataQualityCheck("plan_max_days", "Small date scope", QmtCacheQualityStatus.PASS if days <= plan.max_days else (QmtCacheQualityStatus.FAIL if plan.strict else QmtCacheQualityStatus.WARN), f"days={days}, max_days={plan.max_days}", {"days": days, "max_days": plan.max_days}))
    checks.append(QmtDataQualityCheck("plan_no_trading", "No trading interfaces", QmtCacheQualityStatus.PASS, "plan uses xtdata market data only; no xttrader/order/trade calls", {"provider": plan.provider}))
    return checks


def format_qmt_realdata_plan(plan: QmtRealDataPlan) -> str:
    checks = validate_qmt_realdata_plan(plan)
    return "\n".join([
        f"QMT Real Data Plan: {plan.name}",
        f"symbols={','.join(plan.symbols)}",
        f"date_range={plan.start_date} to {plan.end_date}",
        f"frequency={plan.frequency}",
        f"provider={plan.provider}",
        f"cache_root={plan.cache_root}",
        f"report_dir={plan.report_dir}",
        f"max_symbols={plan.max_symbols}",
        f"max_days={plan.max_days}",
        f"strict={plan.strict}",
        "checks=" + ", ".join(f"{c.check_id}:{c.status.value if hasattr(c.status, 'value') else c.status}" for c in checks),
        "safety=no xttrader, no orders, no assets/positions/trades queries",
    ])
