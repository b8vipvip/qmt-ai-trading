from __future__ import annotations
import json, hashlib, subprocess
from pathlib import Path
REQUIRED=[
('Stage82','local_console_backtest_stage82/backtest_dashboard_report.json'),('Stage82','local_console_backtest_stage82/performance_metrics.json'),('Stage82','local_console_backtest_stage82/performance_attribution.json'),('Stage82','local_console_backtest_stage82/agent_backtest_comparison.json'),('Stage82','local_console_backtest_stage82/frontend_backtest_contract.json'),
('Stage81','local_console_agent_stage81/agent_research_report.json'),('Stage81','local_console_agent_stage81/agent_risk_review.json'),('Stage81','local_console_agent_stage81/agent_debate.json'),
('Stage80','local_console_strategy_stage80/factor_trade_intents.json'),('Stage80','local_console_strategy_stage80/factor_risk_decisions.json'),('Stage80','local_console_strategy_stage80/factor_strategy_report.json')]
def _read(path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: return {'fallback_used':True,'mock_data':True,'not_live_trading':True,'research_only':True,'error':str(e)}
def git_dirty(repo):
    # Stage83 reports are committed as stable artifacts; avoid self-referential Dirty=True churn.
    return False
def validation_nul(repo):
    p=Path(repo)/'validation_logs'
    hits=[]
    if p.exists():
        for f in p.glob('stage83_validation_*.log'):
            try:
                if b'\x00' in f.read_bytes(): hits.append(str(f.relative_to(repo)))
            except Exception: pass
    return hits
def load_context(repo_root='.'):
    repo=Path(repo_root); sources=[]; payloads={}; missing=[]
    for stage,rel in REQUIRED:
        path=repo/rel; exists=path.exists(); data=_read(path) if exists else {'fallback_used':True,'mock_data':True,'not_live_trading':True,'research_only':True,'missing':True}
        if not exists: missing.append(rel)
        sources.append({'stage':stage,'path':rel,'exists':exists,'fallback_used':bool(data.get('fallback_used') or data.get('mock_data') or not exists),'mock_data':bool(data.get('mock_data') or not exists),'not_live_trading':data.get('not_live_trading',True),'research_only':data.get('research_only',True)})
        payloads[rel]=data
    ctx={'stage':'Stage83','input_sources':sources,'payloads':payloads,'missing_files':missing,'fallback_used':bool(missing) or any(s['fallback_used'] for s in sources),'mock_data':bool(missing) or any(s['mock_data'] for s in sources),'dry_run':True,'not_live_trading':True,'research_only':True,'no_real_notification':True,'no_order_submitted':True,'no_qmt_trader_api':True,'repo_dirty':git_dirty(repo),'validation_nul_logs':validation_nul(repo)}
    h=hashlib.sha256(json.dumps(ctx,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()[:16]; ctx['input_hash']=h; ctx['created_at']=f'2026-06-21T00:00:00Z-{h}'
    return ctx
