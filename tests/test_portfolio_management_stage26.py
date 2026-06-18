from __future__ import annotations
import subprocess, sys
from pathlib import Path
from qmt_ai_trading.portfolio.models import PortfolioPlan, PortfolioSnapshot
from qmt_ai_trading.portfolio.allocator import PortfolioAllocationConfig, build_portfolio_targets
from qmt_ai_trading.portfolio.rebalance import PortfolioRebalanceConfig, adjustment_to_trade_intent, build_portfolio_snapshot, compute_rebalance_adjustments
from qmt_ai_trading.portfolio.service import build_portfolio_plan_from_candidates, validate_portfolio_plan
from qmt_ai_trading.portfolio.formatters import format_portfolio_plan_markdown

class C:
    def __init__(self, symbol, score, vol=0.1):
        self.symbol=symbol; self.score=score; self.eligible=True; self.metrics={'volatility':vol, 'last_price':1.0}

def test_models_instantiable():
    assert PortfolioSnapshot('s').dry_run is True
    assert PortfolioPlan('p').success is True

def test_allocation_caps_cash_and_score():
    c=[C('510300.SH',100), C('510500.SH',50)]
    eq,_=build_portfolio_targets(c,'equal_weight',PortfolioAllocationConfig(method='equal_weight',top_n=2,max_symbol_weight=.3,max_portfolio_weight=.8,cash_reserve_ratio=.2))
    assert all(t.target_weight<=.3 for t in eq)
    sc,_=build_portfolio_targets(c,'score_weight',PortfolioAllocationConfig(method='score_weight',top_n=2,max_symbol_weight=.8,max_portfolio_weight=.8,cash_reserve_ratio=.2))
    assert sc[0].target_weight>sc[1].target_weight
    assert sum(t.target_weight for t in sc)<=.8

def test_rebalance_threshold_and_trade_intent_lot():
    snap=build_portfolio_snapshot(cash=100000,total_asset=100000,positions=[])
    targets,_=build_portfolio_targets([C('510300.SH',100)],'equal_weight',PortfolioAllocationConfig(method='equal_weight',top_n=1,max_symbol_weight=.3,max_portfolio_weight=.8,cash_reserve_ratio=.2))
    targets[0].target_value=targets[0].target_weight*snap.total_asset
    small=compute_rebalance_adjustments(snap,targets,PortfolioRebalanceConfig(rebalance_threshold=.5,default_price=3.0))
    assert small[0].quantity==0 and small[0].side=='HOLD'
    big=compute_rebalance_adjustments(snap,targets,PortfolioRebalanceConfig(rebalance_threshold=.01,default_price=3.0))
    intent=adjustment_to_trade_intent(big[0],'run')
    assert intent and intent.dry_run and intent.quantity%100==0 and intent.side=='BUY'

def test_plan_validate_format():
    plan=build_portfolio_plan_from_candidates([C('510300.SH',100),C('510500.SH',50)], total_asset=1000000, current_cash=1000000, allocation_config=PortfolioAllocationConfig(top_n=2,max_symbol_weight=.3,max_portfolio_weight=.8,cash_reserve_ratio=.2), rebalance_config=PortfolioRebalanceConfig(default_price=2.0))
    assert plan.targets and plan.adjustments
    plan.targets[0].target_weight=.9
    assert validate_portfolio_plan(plan)
    assert 'dry-run/paper only' in format_portfolio_plan_markdown(plan)

def test_cli_and_docs_and_gitignore():
    root=Path(__file__).resolve().parents[1]
    out=subprocess.run([sys.executable,'scripts/run_portfolio_plan.py','--cache-root','market_data_missing_stage26','--research-start','2026-05-09','--research-end','2026-06-18','--method','score_weight','--top-n','2'],cwd=root,text=True,capture_output=True,timeout=60)
    assert out.returncode==0, out.stderr
    assert 'Portfolio Plan' in out.stdout
    daily=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--data-source-mode','legacy','--enable-portfolio-plan','--portfolio-method','score_weight','--portfolio-top-n','2'],cwd=root,text=True,capture_output=True,timeout=60)
    assert daily.returncode==0, daily.stderr
    assert 'Portfolio Plan' in daily.stdout
    sched=subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--data-source-mode','legacy','--enable-portfolio-plan'],cwd=root,text=True,capture_output=True,timeout=60)
    assert sched.returncode==0, sched.stderr
    reg=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-portfolio-plan'],cwd=root,text=True,capture_output=True,timeout=60)
    assert reg.returncode==0 and '--enable-portfolio-plan' in reg.stdout
    gi=(root/'.gitignore').read_text(encoding='utf-8')
    assert 'portfolio_plans/' in gi and 'portfolio_snapshots/' in gi
    roadmap=(root/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '阶段二十六' in roadmap and '组合与资金管理层' in roadmap and '阶段二十七' in roadmap and '长期回测与绩效归因' in roadmap
    assert 'sync_all.ps1' not in subprocess.run(['git','diff','--name-only'],cwd=root,text=True,capture_output=True).stdout.splitlines()
