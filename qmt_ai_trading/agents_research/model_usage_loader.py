from __future__ import annotations
import json
from pathlib import Path
def load_model_usage(repo_root:Path)->dict:
    path=repo_root/'local_console_ai_stage78/model_usage_draft.json'
    fallback={'technical_agent':'mock-local-agent','factor_agent':'mock-local-agent','risk_agent':'mock-local-agent','bull_agent':'mock-local-agent','bear_agent':'mock-local-agent','portfolio_manager_agent':'mock-local-agent','final_summary_agent':'mock-local-agent'}
    if not path.exists(): return {'path':str(path),'fallback_used':True,'mock_data':True,'mappings':fallback}
    try:
        data=json.loads(path.read_text(encoding='utf-8')); mappings=data.get('mappings') or data.get('usage_mapping') or data or {}
        return {'path':str(path),'fallback_used':False,'mock_data':False,'mappings':{**fallback, **{k:v for k,v in mappings.items() if v}}}
    except Exception as e:
        return {'path':str(path),'fallback_used':True,'mock_data':True,'error':str(e),'mappings':fallback}
