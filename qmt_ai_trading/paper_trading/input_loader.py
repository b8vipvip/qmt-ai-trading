from __future__ import annotations
import json
from pathlib import Path
from .models import SAFETY_FLAGS

REQUIRED=[("local_console_datahub_stage88","datahub_real_cache.json"),("local_console_datahub_stage88","datahub_quality_gate.json"),("local_console_datahub_stage88","datahub_status.json"),("local_console_datahub_stage88","datahub_report.json"),("local_console_research_stage88","factor_values.json"),("local_console_research_stage88","factor_candidates.json"),("local_console_research_stage88","factor_report.json"),("local_console_strategy_stage88","strategy_signals.json"),("local_console_strategy_stage88","trade_intents.json"),("local_console_strategy_stage88","strategy_report.json"),("local_console_risk_stage88","risk_decisions.json"),("local_console_risk_stage88","risk_report.json")]
def read_json(path:Path, default):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default
def load_stage88_context(repo_root:str|Path="."):
    root=Path(repo_root); files={}; missing=[]
    for d,n in REQUIRED:
        p=root/d/n
        if p.exists(): files[n]=read_json(p,{})
        else: missing.append(str(p)); files[n]={}
    ctx={"stage":"Stage89","input_stage":"Stage88","files":files,"missing_files":missing,"fallback_used":bool(missing),"mock_data":bool(missing),**SAFETY_FLAGS}
    return ctx
def latest_price(cache:dict, symbol:str)->float:
    bars=cache.get("symbols",{}).get(symbol,{}).get("bars",[])
    if bars: return float(bars[-1].get("close") or bars[-1].get("price") or 1.0)
    return 1.0
