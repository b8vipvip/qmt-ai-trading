from __future__ import annotations
import json
from pathlib import Path
from .safety import with_safety
INPUTS={
 'agent_research_report':'local_console_agent_stage81/agent_research_report.json',
 'agent_debate':'local_console_agent_stage81/agent_debate.json',
 'agent_risk_review':'local_console_agent_stage81/agent_risk_review.json',
 'agent_portfolio_review':'local_console_agent_stage81/agent_portfolio_review.json',
 'frontend_agent_contract':'local_console_agent_stage81/frontend_agent_contract.json',
 'factor_strategy_report':'local_console_strategy_stage80/factor_strategy_report.json',
 'factor_trade_intents':'local_console_strategy_stage80/factor_trade_intents.json',
 'factor_risk_decisions':'local_console_strategy_stage80/factor_risk_decisions.json',
 'factor_candidates':'local_console_factor_stage79/factor_candidates.json',
}

def _read(root:Path, rel:str):
    p=root/rel
    if not p.exists(): return None, f'missing input fallback used: {rel}'
    try: return json.loads(p.read_text(encoding='utf-8')), None
    except Exception as e: return None, f'input parse fallback used: {rel}: {e}'

def build_context(repo_root='.'):
    root=Path(repo_root)
    data={}; warnings=[]
    for k,rel in INPUTS.items():
        v,w=_read(root,rel); data[k]=v if v is not None else _fallback(k)
        if w: warnings.append(w)
    symbols=_symbols(data)
    return with_safety({'stage':'Stage82','input_source':'stage81','input_files':INPUTS,'warnings':warnings,
        'fallback_used':bool(warnings),'mock_data':bool(warnings),'data_quality':'fallback_safe' if warnings else 'loaded',
        'linked_symbols':symbols})

def _fallback(k):
    if k=='factor_candidates': return [{'symbol':'510300.SH','rank':1,'score':82,'reasons':['mock fallback candidate'],'risk_flags':['fallback_used','mock_data']}]
    if k=='factor_trade_intents': return [{'intent_id':'mock-intent-1','symbol':'510300.SH','side':'WATCH','quantity':0,'dry_run':True,'research_only':True}]
    if k=='factor_risk_decisions': return [{'intent_id':'mock-intent-1','symbol':'510300.SH','allowed':False,'reasons':['fallback mock: requires risk gate and human approval']}]
    return {'fallback_used':True,'mock_data':True,'dry_run':True,'not_live_trading':True,'research_only':True}

def _symbols(data):
    vals=[]
    for item in data.get('factor_candidates') or []:
        if isinstance(item,dict) and item.get('symbol'): vals.append(item['symbol'])
    for item in data.get('factor_trade_intents') or []:
        if isinstance(item,dict) and item.get('symbol'): vals.append(item['symbol'])
    return sorted(set(vals)) or ['510300.SH']
