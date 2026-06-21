from __future__ import annotations
import ast
from pathlib import Path
from .xtdata_config import XtDataAdapterConfig

DANGEROUS_TERMS = [
    "XtQuantTrader", "place_order", "execute_order", "buy_now", "sell_now",
    "query_account", "query_position", "query_order", "query_trade",
]
DANGEROUS_CONFIG_TRUE = [
    "enabled", "allow_real_market_data", "allow_import_xtdata", "allow_connect_miniqmt", "allow_xttrader",
]

def scan_import_guard(paths: list[str | Path]) -> dict:
    violations = []
    scanned = []
    for item in paths:
        p = Path(item)
        files = [p] if p.is_file() else sorted(p.rglob("*.py")) if p.exists() else []
        for f in files:
            scanned.append(str(f))
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            except SyntaxError as exc:
                violations.append({"path": str(f), "line": exc.lineno or 0, "type": "syntax_error", "message": str(exc)})
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "xtquant" or alias.name.startswith("xtquant."):
                            violations.append({"path": str(f), "line": node.lineno, "type": "forbidden_import", "name": alias.name})
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if mod == "xtquant" or mod.startswith("xtquant."):
                        violations.append({"path": str(f), "line": node.lineno, "type": "forbidden_import", "name": mod})
    return {
        "status": "PASS" if not violations else "BLOCKED",
        "xtdata_imported": False,
        "import_attempted": False,
        "scanned_file_count": len(scanned),
        "violations": violations,
        "dry_run": True,
        "read_only": True,
    }

def evaluate_xtdata_safety(config: XtDataAdapterConfig | None = None, text: str = "") -> dict:
    cfg = config or XtDataAdapterConfig()
    issues = []
    for name in DANGEROUS_CONFIG_TRUE:
        if bool(getattr(cfg, name, False)):
            issues.append({"type": "dangerous_config", "name": name, "value": True})
    lowered = text.lower()
    if "xttrader" in lowered:
        issues.append({"type": "dangerous_term", "name": "xttrader"})
    for term in DANGEROUS_TERMS:
        if term.lower() in lowered:
            issues.append({"type": "dangerous_term", "name": term})
    return {
        "safety_status": "PASS" if not issues else "BLOCKED",
        "requires_human_review": bool(issues),
        "issues": issues,
        "dry_run": True,
        "read_only": True,
        "enabled": cfg.enabled,
        "allow_real_market_data": cfg.allow_real_market_data,
        "allow_import_xtdata": cfg.allow_import_xtdata,
        "allow_connect_miniqmt": cfg.allow_connect_miniqmt,
        "allow_xttrader": cfg.allow_xttrader,
        "no_order_submitted": True,
        "no_qmt_trader_api": True,
    }
