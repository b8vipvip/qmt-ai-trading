from __future__ import annotations
import json
from pathlib import Path
INPUT_FILES=[
'local_console_ai_stage78/model_usage_draft.json','local_console_ai_stage78/ai_benchmark_report.json','local_console_factor_stage79/factor_candidates.json','local_console_factor_stage79/factor_report.json','local_console_strategy_stage80/factor_strategy_signals.json','local_console_strategy_stage80/factor_trade_intents.json','local_console_strategy_stage80/factor_risk_decisions.json','local_console_strategy_stage80/factor_strategy_report.json']
def _read(path:Path):
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return {'raw_text':path.read_text(encoding='utf-8')[:2000]}
def build_context(repo_root:Path)->dict:
    sources=[]; data={}; warnings=[]; fallback=False
    for rel in INPUT_FILES:
        val=_read(repo_root/rel); ok=val is not None
        sources.append({'path':rel,'exists':ok,'mock_data':not ok})
        if ok: data[Path(rel).stem]=val
        else: fallback=True; warnings.append(f'missing input fallback used: {rel}')
    if fallback:
        data.setdefault('factor_candidates',[{'symbol':'MOCK.SH','rank':1,'score':0,'risk_flags':['mock_data','fallback_used'],'reasons':['缺少上游文件，仅用于 dry-run validation']}])
        data.setdefault('factor_risk_decisions',[{'status':'REJECTED_DRY_RUN','risk_flags':['mock_data','not_live_trading']}])
    return {'stage':'Stage81','input_source':'stage80','input_sources':sources,'data':data,'warnings':warnings,'fallback_used':fallback,'mock_data':fallback,'dry_run':True,'not_live_trading':True,'research_only':True}
