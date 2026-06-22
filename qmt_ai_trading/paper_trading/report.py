from __future__ import annotations
import json, shutil
from pathlib import Path
from .input_loader import load_stage88_context, latest_price
from .models import SAFETY_FLAGS, PaperTradingReport
from .paper_broker import PaperBroker, is_allowed
from .position_book import ShadowPositionBook
from .pnl_tracker import compute_pnl
from .risk_replay import replay

INITIAL_CASH=100000.0

def _dump(path:Path, data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding='utf-8')
def _md(path:Path, title:str, data):
    lines=[f"# {title}","", "```json", json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True), "```", ""]
    path.write_text("\n".join(lines),encoding='utf-8')
def _copy_outputs(out:Path, canon:Path):
    canon.mkdir(parents=True,exist_ok=True)
    for p in out.iterdir():
        if p.is_file(): shutil.copy2(p, canon/p.name)

def _risk_text(decision:dict)->str:
    d=str(decision.get('decision','')).upper()
    if decision.get('requires_review') or 'REVIEW' in d or 'MANUAL' in d: return '需人工确认'
    return '通过' if is_allowed(decision) else '拒绝'

def _side_text(side:str)->str:
    s=str(side).lower()
    return {'buy':'买入模拟持仓','sell':'卖出模拟持仓','hold':'保持观望'}.get(s, side)

def _status_text(status:str)->str:
    return {'FILLED':'模拟成交','REJECTED':'风控拒绝','SKIPPED':'不操作','NO_ACTION':'不操作','PENDING_REVIEW':'待人工确认','NO_FILL':'未成交','PENDING':'待处理'}.get(str(status).upper(), status)

def _reason(order)->str:
    if str(order.side).lower()=='hold': return '策略建议 HOLD'
    if order.reject_reason: return order.reject_reason
    reasons=order.risk_decision.get('reasons') or order.risk_decision.get('reject_reasons') or []
    return '; '.join(reasons)

def _order_summary(order):
    return {'order_id':order.order_id,'symbol':order.symbol,'side':order.side,'operation':_side_text(order.side),'quantity':order.quantity,'intent_price':order.intent_price,'simulated_fill_price':getattr(order,'simulated_fill_price',None),'status':order.fill_status,'status_label':_status_text(order.fill_status),'risk_summary':_risk_text(order.risk_decision),'reason':_reason(order),'raw':order.to_dict(),**SAFETY_FLAGS}

def _fill_summary(order, fill=None):
    if fill is None:
        return {'order_id':order.order_id,'symbol':order.symbol,'operation':_side_text(order.side),'quantity':0,'simulated_fill_price':None,'fill_status':'NO_FILL','status_label':'不操作','reason':_reason(order),'raw':order.to_dict(),**SAFETY_FLAGS}
    return {'fill_id':fill.fill_id,'order_id':fill.order_id,'symbol':fill.symbol,'operation':_side_text(fill.side),'quantity':fill.quantity,'simulated_fill_price':fill.simulated_fill_price,'fill_status':fill.fill_status,'status_label':_status_text(fill.fill_status),'reason':fill.reject_reason or _reason(order),'raw':fill.to_dict(),**SAFETY_FLAGS}

def _position_summary(pos):
    qty=pos.get('quantity',0); status='已清仓' if qty==0 else '持仓中'
    return {'symbol':pos.get('symbol',''),'direction':'买入模拟持仓' if qty>=0 else '卖出模拟持仓','quantity':qty,'average_price':pos.get('average_price',0),'last_price':pos.get('last_price',0),'position_value':pos.get('position_value',0),'unrealized_pnl':pos.get('unrealized_pnl',0),'return_rate':(pos.get('unrealized_pnl',0)/(abs(qty)*pos.get('average_price',0))) if qty and pos.get('average_price',0) else 0,'status':status,'raw':pos,**SAFETY_FLAGS}

def _pnl_summary(portfolio, pnl):
    d=pnl.to_dict()
    return {'initial_cash':INITIAL_CASH,'current_cash':portfolio.paper_cash,'position_value':portfolio.paper_position_value,'total_value':portfolio.paper_total_value,'daily_pnl':pnl.daily_pnl,'cumulative_pnl':pnl.realized_pnl+pnl.unrealized_pnl,'portfolio_return':pnl.portfolio_return,'max_drawdown':-abs(pnl.max_drawdown),'warnings':pnl.warnings,'raw':d,**SAFETY_FLAGS}

def _risk_summary(result, order_by_id):
    o=order_by_id.get(result.order_id)
    return {'order_id':result.order_id,'symbol':getattr(o,'symbol',''),'operation':_side_text(getattr(o,'side','')),'risk_summary':'通过' if result.allowed else '拒绝','reject_reason':'' if result.allowed else '; '.join(result.reasons),'requires_human_review':bool(getattr(o,'risk_decision',{}).get('requires_human_approval',True)),'safety_violation':result.safety_violation,'raw':result.to_dict(),**SAFETY_FLAGS}

def run_paper_trading_stage89(repo_root='.', input_stage=88, output_dir='local_console_paper_stage89', dry_run=True, read_only=True):
    root=Path(repo_root); out=root/output_dir; out.mkdir(parents=True,exist_ok=True)
    ctx=load_stage88_context(root)
    cache=ctx['files'].get('datahub_real_cache.json',{})
    intents=ctx['files'].get('trade_intents.json',{}).get('trade_intents',[])
    decisions=ctx['files'].get('risk_decisions.json',{}).get('decisions',[])
    by_id={d.get('intent_id'):d for d in decisions}
    broker=PaperBroker(); fills=[]; fills_by_order={}
    for intent in intents:
        dec=by_id.get(intent.get('intent_id'), {'decision':'REJECTED','reasons':['missing Stage88 RiskDecision'], **SAFETY_FLAGS})
        order=broker.submit_paper_order(intent, dec)
        fill=broker.simulate_fill(order, cache)
        if fill is not None:
            fills.append(fill); fills_by_order[order.order_id]=fill
    prices={s:latest_price(cache,s) for s in cache.get('symbols',{})}
    book=ShadowPositionBook(INITIAL_CASH, whitelist=cache.get('symbols',{}).keys())
    target_by_order={f"paper-{i.get('intent_id',i.get('symbol',''))}":float(i.get('target_weight',0) or 0) for i in intents}
    for f in fills: book.apply_fill(f, target_by_order.get(f.order_id,0.0))
    portfolio=book.portfolio(prices); pnl=compute_pnl(portfolio,INITIAL_CASH); risk=replay(broker.list_orders())
    orders=[o.to_dict() for o in broker.list_orders()]; fills_d=[f.to_dict() for f in fills]; positions=portfolio.positions
    replay_d=[r.to_dict() for r in risk]; order_by_id={o.order_id:o for o in broker.list_orders()}
    paper_order_summary=[_order_summary(o) for o in broker.list_orders()]
    paper_fill_summary=[_fill_summary(o, fills_by_order.get(o.order_id)) for o in broker.list_orders()]
    position_summary=[_position_summary(p) for p in positions]
    pnl_summary=_pnl_summary(portfolio,pnl)
    risk_replay_summary=[_risk_summary(r, order_by_id) for r in risk]
    report=PaperTradingReport('Stage89',len(orders),sum(1 for f in fills if f.fill_status=='FILLED'),len(positions),'影子交易开启','SAFE_PAPER_ONLY').to_dict()
    status={**report,'output_dir':output_dir,'real_order_submitted':False}
    contract={'stage':'Stage89','menu':['Paper Trading','影子交易'],'endpoints':['/api/v1/paper-trading/status','/api/v1/paper-trading/orders/latest','/api/v1/paper-trading/fills/latest','/api/v1/paper-trading/positions/latest','/api/v1/paper-trading/portfolio/latest','/api/v1/paper-trading/pnl/latest','/api/v1/paper-trading/risk-replay/latest','/api/v1/paper-trading/report/latest'],**SAFETY_FLAGS}
    boundary={'next_stage':'xttrader remains disabled until explicit human approval','live_trading':'DISABLED_FOR_SAFETY','allow_xttrader':False,'allow_order_submit':False,'allow_account_query':False,**SAFETY_FLAGS}
    artifacts={'paper_input_context':ctx,'paper_orders':{'orders':orders,'paper_order_summary':paper_order_summary,**SAFETY_FLAGS},'paper_fills':{'fills':fills_d,'paper_fill_summary':paper_fill_summary,**SAFETY_FLAGS},'shadow_positions':{'positions':positions,'position_summary':position_summary,**SAFETY_FLAGS},'shadow_portfolio':{**portfolio.to_dict(),'pnl_summary':pnl_summary},'shadow_pnl':{**pnl.to_dict(),'pnl_summary':pnl_summary},'risk_replay':{'results':replay_d,'risk_replay_summary':risk_replay_summary,'safety_violation_count':sum(1 for r in risk if r.safety_violation),**SAFETY_FLAGS},'paper_trading_report':report,'frontend_paper_contract':contract,'next_xttrader_boundary_plan':boundary}
    for name,data in artifacts.items(): _dump(out/f'{name}.json',data); _md(out/f'{name}.md',name,data)
    _copy_outputs(out, root/'artifacts/reports/stage89/paper_trading')
    return status
