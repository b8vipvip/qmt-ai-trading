from __future__ import annotations
import ast
from pathlib import Path
from .xtdata_live_config import XtDataLiveReadOnlyConfig

FORBIDDEN_NAMES = {"XtQuantTrader"}
FORBIDDEN_MODULE_PART = "xttrader"

def scan_xtdata_live_safety(paths: list[str | Path]) -> dict:
    violations=[]; scanned=[]
    for item in paths:
        p=Path(item); files=[p] if p.is_file() else sorted(p.rglob('*.py')) if p.exists() else []
        for f in files:
            scanned.append(str(f))
            try: tree=ast.parse(f.read_text(encoding='utf-8'))
            except SyntaxError as exc:
                violations.append({'path':str(f),'line':exc.lineno or 0,'type':'syntax_error'}); continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        if FORBIDDEN_MODULE_PART in a.name: violations.append({'path':str(f),'line':node.lineno,'name':a.name})
                if isinstance(node, ast.ImportFrom):
                    if FORBIDDEN_MODULE_PART in (node.module or ''): violations.append({'path':str(f),'line':node.lineno,'name':node.module})
                    for a in node.names:
                        if a.name in FORBIDDEN_NAMES: violations.append({'path':str(f),'line':node.lineno,'name':a.name})
    return {'safety_status':'PASS' if not violations else 'BLOCKED','violations':violations,'scanned_file_count':len(scanned),'read_only':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'not_live_trading':True}

def evaluate_live_config(config: XtDataLiveReadOnlyConfig) -> dict:
    issues=[]
    if not config.read_only: issues.append({'name':'read_only','status':'BLOCKED'})
    for name in ('allow_xttrader','allow_account_query','allow_order_submit'):
        if getattr(config,name): issues.append({'name':name,'status':'BLOCKED'})
    return {'safety_status':'PASS' if not issues else 'BLOCKED','issues':issues,'read_only':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'not_live_trading':True,'allow_xttrader':False,'allow_order_submit':False}
