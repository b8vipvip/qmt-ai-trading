from __future__ import annotations
import json, shutil
from pathlib import Path
from .input_loader import load_stage88_context, latest_price
from .models import SAFETY_FLAGS, PaperTradingReport
from .paper_broker import PaperBroker
from .position_book import ShadowPositionBook
from .pnl_tracker import compute_pnl
from .risk_replay import replay

def _dump(path:Path, data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding='utf-8')
def _md(path:Path, title:str, data):
    lines=[f"# {title}","", "```json", json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True), "```", ""]
    path.write_text("\n".join(lines),encoding='utf-8')
def _copy_outputs(out:Path, canon:Path):
    canon.mkdir(parents=True,exist_ok=True)
    for p in out.iterdir():
        if p.is_file(): shutil.copy2(p, canon/p.name)

def run_paper_trading_stage89(repo_root='.', input_stage=88, output_dir='local_console_paper_stage89', dry_run=True, read_only=True):
    root=Path(repo_root); out=root/output_dir; out.mkdir(parents=True,exist_ok=True)
    ctx=load_stage88_context(root)
    cache=ctx['files'].get('datahub_real_cache.json',{})
    intents=ctx['files'].get('trade_intents.json',{}).get('trade_intents',[])
    decisions=ctx['files'].get('risk_decisions.json',{}).get('decisions',[])
    by_id={d.get('intent_id'):d for d in decisions}
    broker=PaperBroker(); fills=[]
    for intent in intents:
        dec=by_id.get(intent.get('intent_id'), {'decision':'REJECTED','reasons':['missing Stage88 RiskDecision'], **SAFETY_FLAGS})
        order=broker.submit_paper_order(intent, dec)
        fills.append(broker.simulate_fill(order, cache))
    prices={s:latest_price(cache,s) for s in cache.get('symbols',{})}
    book=ShadowPositionBook(100000.0, whitelist=cache.get('symbols',{}).keys())
    target_by_order={f"paper-{i.get('intent_id',i.get('symbol',''))}":float(i.get('target_weight',0) or 0) for i in intents}
    for f in fills: book.apply_fill(f, target_by_order.get(f.order_id,0.0))
    portfolio=book.portfolio(prices); pnl=compute_pnl(portfolio,100000.0); risk=replay(broker.list_orders())
    orders=[o.to_dict() for o in broker.list_orders()]; fills_d=[f.to_dict() for f in fills]; positions=portfolio.positions
    replay_d=[r.to_dict() for r in risk]
    report=PaperTradingReport('Stage89',len(orders),sum(1 for f in fills if f.fill_status=='FILLED'),len(positions),'影子交易开启','SAFE_PAPER_ONLY').to_dict()
    status={**report,'output_dir':output_dir,'real_order_submitted':False}
    contract={'stage':'Stage89','menu':['Paper Trading','影子交易'],'endpoints':['/api/v1/paper-trading/status','/api/v1/paper-trading/orders/latest','/api/v1/paper-trading/fills/latest','/api/v1/paper-trading/positions/latest','/api/v1/paper-trading/portfolio/latest','/api/v1/paper-trading/pnl/latest','/api/v1/paper-trading/risk-replay/latest','/api/v1/paper-trading/report/latest'],**SAFETY_FLAGS}
    boundary={'next_stage':'xttrader remains disabled until explicit human approval','live_trading':'DISABLED_FOR_SAFETY','allow_xttrader':False,'allow_order_submit':False,'allow_account_query':False,**SAFETY_FLAGS}
    artifacts={'paper_input_context':ctx,'paper_orders':{'orders':orders,**SAFETY_FLAGS},'paper_fills':{'fills':fills_d,**SAFETY_FLAGS},'shadow_positions':{'positions':positions,**SAFETY_FLAGS},'shadow_portfolio':portfolio.to_dict(),'shadow_pnl':pnl.to_dict(),'risk_replay':{'results':replay_d,'safety_violation_count':sum(1 for r in risk if r.safety_violation),**SAFETY_FLAGS},'paper_trading_report':report,'frontend_paper_contract':contract,'next_xttrader_boundary_plan':boundary}
    for name,data in artifacts.items(): _dump(out/f'{name}.json',data); _md(out/f'{name}.md',name,data)
    _copy_outputs(out, root/'artifacts/reports/stage89/paper_trading')
    return status
