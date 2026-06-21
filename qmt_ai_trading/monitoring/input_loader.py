from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


STAGE83_CREATED_AT = "2026-01-01T00:00:00+00:00"

STAGE83_INPUT_FILES: list[tuple[str, str]] = [
    ("Stage82", "local_console_backtest_stage82/backtest_dashboard_report.json"),
    ("Stage82", "local_console_backtest_stage82/performance_metrics.json"),
    ("Stage82", "local_console_backtest_stage82/performance_attribution.json"),
    ("Stage82", "local_console_backtest_stage82/agent_backtest_comparison.json"),
    ("Stage82", "local_console_backtest_stage82/frontend_backtest_contract.json"),
    ("Stage81", "local_console_agent_stage81/agent_research_report.json"),
    ("Stage81", "local_console_agent_stage81/agent_risk_review.json"),
    ("Stage81", "local_console_agent_stage81/agent_debate.json"),
    ("Stage80", "local_console_strategy_stage80/factor_trade_intents.json"),
    ("Stage80", "local_console_strategy_stage80/factor_risk_decisions.json"),
    ("Stage80", "local_console_strategy_stage80/factor_strategy_report.json"),
]


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    for encoding in ("utf-8", "utf-8-sig"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except UnicodeDecodeError:
            continue
        except Exception:
            return {}
    return {}


def _safe_get(value: Any, key: str, default: Any = None) -> Any:
    """Safely read a field from dict/list/scalar JSON data."""

    if isinstance(value, dict):
        return value.get(key, default)

    if isinstance(value, list):
        bool_seen = False
        bool_value = False
        collected: list[Any] = []

        for item in value:
            if not isinstance(item, dict) or key not in item:
                continue

            item_value = item.get(key)
            if isinstance(item_value, bool):
                bool_seen = True
                bool_value = bool_value or item_value
            elif item_value not in (None, "", [], {}):
                collected.append(item_value)

        if collected:
            return collected[0] if len(collected) == 1 else collected
        if bool_seen:
            return bool_value

    return default


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _collect_symbols(value: Any) -> list[str]:
    symbols: set[str] = set()

    for obj in _walk(value):
        if not isinstance(obj, dict):
            continue

        for key in ("symbol", "linked_symbols"):
            if key not in obj:
                continue

            val = obj.get(key)
            if isinstance(val, str):
                symbols.add(val)
            elif isinstance(val, list):
                symbols.update(item for item in val if isinstance(item, str))

    return sorted(symbol for symbol in symbols if symbol)


def _collect_forbidden_terms(value: Any) -> list[str]:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    terms = [
        "execute_order",
        "live_trade",
        "auto_approve",
        "bypass_risk",
        "xttrader",
        "xtquanttrader",
        "place_order",
        "buy_now",
        "sell_now",
        "query_account",
        "query_position",
        "query_order",
        "query_trade",
        "send_email",
        "send_sms",
        "telegram_send",
        "wechat_send",
        "dingding_send",
    ]
    return sorted({term for term in terms if term in text})


def _repo_dirty(repo: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def _validation_nul_logs(repo: Path) -> list[str]:
    log_dir = repo / "validation_logs"
    if not log_dir.exists():
        return []

    bad: list[str] = []
    for path in sorted(log_dir.glob("stage*_validation_*.log"))[-20:]:
        try:
            data = path.read_bytes()
        except Exception:
            continue
        if b"\x00" in data:
            bad.append(str(path.relative_to(repo)).replace("\\", "/"))
    return bad


def load_context(repo_root: str | Path = ".") -> dict[str, Any]:
    repo = Path(repo_root)
    input_sources: list[dict[str, Any]] = []
    payloads: dict[str, Any] = {}
    linked_symbols: set[str] = set()
    forbidden_terms: set[str] = set()

    for stage, rel in STAGE83_INPUT_FILES:
        path = repo / rel
        exists = path.exists()
        data = _load_json(path) if exists else {}
        payloads[rel] = data

        source_symbols = _collect_symbols(data)
        source_forbidden_terms = _collect_forbidden_terms(data)
        linked_symbols.update(source_symbols)
        forbidden_terms.update(source_forbidden_terms)

        fallback_used = bool(_safe_get(data, "fallback_used", False) or _safe_get(data, "mock_data", False) or not exists)
        mock_data = bool(_safe_get(data, "mock_data", False) or not exists)

        input_sources.append(
            {
                "stage": stage,
                "path": rel,
                "exists": exists,
                "data_type": type(data).__name__,
                "fallback_used": fallback_used,
                "mock_data": mock_data,
                "dry_run": bool(_safe_get(data, "dry_run", True)),
                "not_live_trading": bool(_safe_get(data, "not_live_trading", True)),
                "research_only": bool(_safe_get(data, "research_only", True)),
                "no_real_notification": bool(_safe_get(data, "no_real_notification", True)),
                "no_order_submitted": bool(_safe_get(data, "no_order_submitted", True)),
                "no_qmt_trader_api": bool(_safe_get(data, "no_qmt_trader_api", True)),
                "requires_risk_gate": bool(_safe_get(data, "requires_risk_gate", True)),
                "requires_human_review": bool(
                    _safe_get(data, "requires_human_review", _safe_get(data, "requires_human_approval", True))
                ),
                "linked_symbols": source_symbols,
                "forbidden_terms": source_forbidden_terms,
                "unsafe": bool(_safe_get(data, "unsafe", False) or source_forbidden_terms),
            }
        )

    missing_files = [source["path"] for source in input_sources if not source["exists"]]
    fallback_sources = [source["path"] for source in input_sources if source["fallback_used"]]
    mock_sources = [source["path"] for source in input_sources if source["mock_data"]]
    unsafe_sources = [source["path"] for source in input_sources if source["unsafe"]]

    context = {
        "stage": "Stage83",
        "created_at": STAGE83_CREATED_AT,
        "input_source": "stage82",
        "input_files": {Path(source["path"]).stem: source["path"] for source in input_sources},

        # Keys required by anomaly_detector.py and report.py
        "input_sources": input_sources,
        "missing_files": missing_files,
        "payloads": payloads,
        "repo_dirty": _repo_dirty(repo),
        "validation_nul_logs": _validation_nul_logs(repo),

        # Backward-compatible aliases for future code.
        "sources": input_sources,
        "loaded_data": payloads,
        "missing_inputs": missing_files,

        "fallback_sources": fallback_sources,
        "mock_sources": mock_sources,
        "unsafe_sources": unsafe_sources,
        "warnings": [f"missing input fallback used: {path}" for path in missing_files],
        "fallback_used": bool(fallback_sources),
        "mock_data": bool(mock_sources),
        "data_quality": "fallback" if missing_files else "loaded",
        "linked_symbols": sorted(linked_symbols),
        "dry_run": True,
        "not_live_trading": True,
        "research_only": True,
        "no_real_notification": True,
        "no_order_submitted": True,
        "no_qmt_trader_api": True,
        "requires_risk_gate": True,
        "requires_human_review": True,
        "requires_human_approval": True,
        "forbidden_terms": sorted(forbidden_terms),
        "unsafe": bool(forbidden_terms or unsafe_sources),
        "disclaimer": "Stage83 监控告警仅为 dry-run，不真实发送通知，不作为实盘执行依据。",
    }

    return context
