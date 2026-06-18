from __future__ import annotations
import json, subprocess, sys
from datetime import date, timedelta
from pathlib import Path

from qmt_ai_trading.datahub.local_store import LocalBarStore
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.performance.metrics import calculate_max_drawdown, calculate_sharpe
from qmt_ai_trading.performance.models import PortfolioEquityPoint, PortfolioPerformanceSummary
from qmt_ai_trading.performance.report import format_long_backtest_markdown
from qmt_ai_trading.performance.attribution import format_factor_attribution
from qmt_ai_trading.backtest.long_portfolio_backtest import LongPortfolioBacktestConfig, generate_rebalance_dates, run_long_portfolio_backtest, save_long_backtest_result, load_long_backtest_result

SYMS=["510300.SH","510500.SH","159915.SZ"]

def _cache(root: Path, days=45):
    store=LocalBarStore(root)
    start=date(2026,3,20)
    for idx,s in enumerate(SYMS):
        bars=[]
        for i in range(days):
            d=start+timedelta(days=i)
            p=1.0+idx*0.1+i*0.01
            bars.append(MarketBar(s,d.isoformat(),p,p+0.01,p-0.01,p,100000+i,"mock"))
        store.save_bars(s,"1d",bars,provider="mock")

def test_summary_model_instantiates():
    assert PortfolioPerformanceSummary("2026-01-01","2026-01-02",100,101).final_equity==101

def test_metrics_empty_and_drawdown():
    curve=[PortfolioEquityPoint("d1",100),PortfolioEquityPoint("d2",80),PortfolioEquityPoint("d3",90)]
    assert calculate_max_drawdown(curve)==-0.2
    assert calculate_sharpe([])==0.0

def test_generate_rebalance_dates_multiple():
    assert len(generate_rebalance_dates("2026-01-01","2026-01-20","5d"))>=4

def test_run_long_backtest_cache_enough_and_report_save_load(tmp_path):
    _cache(tmp_path)
    cfg=LongPortfolioBacktestConfig(symbols=SYMS,start_date="2026-03-20",end_date="2026-05-01",cache_root=str(tmp_path),min_bars=20,lookback_bars=20,max_symbol_weight=0.2)
    res=run_long_portfolio_backtest(cfg)
    assert res.success and res.summary is not None
    assert res.equity_curve
    names={x.factor_name for x in res.factor_attribution}
    assert {"score","momentum","volatility","volume"} <= names
    assert "score" in format_factor_attribution(res.factor_attribution)
    md=format_long_backtest_markdown(res)
    assert "Long backtest is dry-run simulation only" in md
    p=tmp_path/"x.long_backtest.json"
    save_long_backtest_result(res,p)
    assert load_long_backtest_result(p).run_id==res.run_id

def test_run_long_backtest_insufficient_cache_warns(tmp_path):
    _cache(tmp_path, days=5)
    cfg=LongPortfolioBacktestConfig(symbols=SYMS,start_date="2026-03-20",end_date="2026-04-10",cache_root=str(tmp_path),min_bars=20,lookback_bars=20)
    res=run_long_portfolio_backtest(cfg)
    assert res.success
    assert res.warnings

def test_risk_gate_blocked_not_executable(tmp_path):
    _cache(tmp_path)
    cfg=LongPortfolioBacktestConfig(symbols=SYMS,start_date="2026-03-20",end_date="2026-05-01",cache_root=str(tmp_path),min_bars=20,lookback_bars=20,max_symbol_weight=0.8,portfolio_top_n=1)
    res=run_long_portfolio_backtest(cfg)
    assert any(not t.allowed_by_risk for t in res.trades)
    assert res.summary.risk_blocked_count >= 1
    assert res.summary.trade_count == sum(1 for t in res.trades if t.allowed_by_risk)

def test_cli_json_markdown_and_docs(tmp_path):
    _cache(tmp_path/"cache")
    md=tmp_path/"out.md"; js=tmp_path/"out.json"
    cp=subprocess.run([sys.executable,"scripts/run_long_portfolio_backtest.py","--cache-root",str(tmp_path/"cache"),"--symbols",",".join(SYMS),"--start","2026-03-20","--end","2026-05-01","--output",str(md),"--json-output",str(js)],cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True,timeout=60)
    assert cp.returncode==0, cp.stderr+cp.stdout
    assert md.exists() and "Long backtest is dry-run simulation only" in md.read_text(encoding="utf-8")
    assert js.exists() and json.loads(js.read_text(encoding="utf-8"))["run_id"]
    road=Path("docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段二十七" in road and "长期回测与绩效归因" in road
    assert "阶段二十八" in road and "异常监控、告警、熔断" in road
    assert Path("scripts/sync_all.ps1").exists()
