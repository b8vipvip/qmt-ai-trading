from __future__ import annotations
import json
from pathlib import Path
from uuid import uuid4
from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.risk.trade_validator import validate_trade_intent
from .allocator import PortfolioAllocationConfig, build_portfolio_targets
from .models import PortfolioPlan, PortfolioSnapshot, PortfolioTarget, to_jsonable
from .rebalance import PortfolioRebalanceConfig, adjustments_to_trade_intents, build_portfolio_snapshot, compute_rebalance_adjustments

def build_portfolio_plan(candidates, snapshot, allocation_config=None, rebalance_config=None, run_id='portfolio'):
    ac=allocation_config or PortfolioAllocationConfig(); rc=rebalance_config or PortfolioRebalanceConfig()
    targets,warnings=build_portfolio_targets(candidates, ac.method, ac)
    investable=float(snapshot.total_asset)*min(float(ac.max_portfolio_weight), max(0,1-float(ac.cash_reserve_ratio)))
    for t in targets: t.target_value=t.target_weight*float(snapshot.total_asset)
    adjs=compute_rebalance_adjustments(snapshot, targets, rc)
    intents=adjustments_to_trade_intents(adjs, run_id, dry_run=True)
    for i in intents: i.dry_run=True
    plan=PortfolioPlan(f"portfolio-plan-{uuid4().hex[:12]}", run_id=run_id, method=str(ac.method.value if hasattr(ac.method,'value') else ac.method), cash_reserve_ratio=ac.cash_reserve_ratio, max_symbol_weight=ac.max_symbol_weight, max_portfolio_weight=ac.max_portfolio_weight, rebalance_threshold=rc.rebalance_threshold, total_asset=snapshot.total_asset, investable_asset=investable, targets=targets, adjustments=adjs, trade_intents=intents, warnings=list(warnings), success=True, message='portfolio plan generated', metadata={'dry_run':True,'snapshot_source':snapshot.source})
    plan.warnings.extend(validate_portfolio_plan(plan))
    return plan

def build_portfolio_plan_from_candidates(candidates, *, run_id='portfolio', total_asset=1000000.0, current_cash=1000000.0, snapshot=None, allocation_config=None, rebalance_config=None, snapshot_path=None):
    snap=snapshot or (load_portfolio_snapshot(snapshot_path) if snapshot_path else None) or build_portfolio_snapshot(cash=current_cash,total_asset=total_asset)
    return build_portfolio_plan(candidates, snap, allocation_config, rebalance_config, run_id)

def build_portfolio_plan_from_pipeline_result(result, **kwargs):
    return build_portfolio_plan_from_candidates(getattr(result,'candidates',[]) or [], run_id=getattr(getattr(result,'context',None),'run_id','pipeline'), **kwargs)

def validate_portfolio_plan(plan):
    warnings=[]; total=sum(t.target_weight for t in plan.targets)
    if any(t.target_weight>plan.max_symbol_weight+1e-9 for t in plan.targets): warnings.append('target exceeds max_symbol_weight')
    if total>min(plan.max_portfolio_weight,1-plan.cash_reserve_ratio)+1e-9: warnings.append('target total exceeds portfolio/cash limit')
    if any(not getattr(i,'dry_run',False) for i in plan.trade_intents): warnings.append('non-dry-run trade intent blocked')
    return warnings

def save_portfolio_plan(plan, path=None):
    p=Path(path or 'portfolio_plans')
    if p.suffix.lower()!='.json': p=p/f'{plan.plan_id}.portfolio_plan.json'
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(to_jsonable(plan),ensure_ascii=False,indent=2),encoding='utf-8'); return p

def _position(d):
    from .models import PortfolioPosition
    return PortfolioPosition(**d)
def load_portfolio_snapshot(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    data['positions']=[_position(x) for x in data.get('positions',[])]
    return PortfolioSnapshot(**data)
def load_portfolio_plan(path): return json.loads(Path(path).read_text(encoding='utf-8'))
