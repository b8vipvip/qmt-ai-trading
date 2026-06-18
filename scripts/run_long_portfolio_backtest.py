#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.backtest.long_portfolio_backtest import LongPortfolioBacktestConfig, run_long_portfolio_backtest, save_long_backtest_result
from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.performance.report import format_long_backtest_markdown

def main(argv=None):
    ap=argparse.ArgumentParser(description='Run long dry-run portfolio backtest from LocalBarStore cache only.')
    ap.add_argument('--cache-root', required=True); ap.add_argument('--symbols','--symbol', default=''); ap.add_argument('--universe-name', default='')
    ap.add_argument('--start', required=True); ap.add_argument('--end', required=True); ap.add_argument('--frequency', default='1d'); ap.add_argument('--rebalance-frequency', default='5d')
    ap.add_argument('--lookback-bars', type=int, default=20); ap.add_argument('--min-bars', type=int, default=20); ap.add_argument('--initial-cash', type=float, default=1000000)
    ap.add_argument('--portfolio-method', default='score_weight'); ap.add_argument('--portfolio-top-n', type=int, default=2); ap.add_argument('--cash-reserve-ratio', type=float, default=0.2)
    ap.add_argument('--max-symbol-weight', type=float, default=0.2); ap.add_argument('--max-portfolio-weight', type=float, default=0.8); ap.add_argument('--rebalance-threshold', type=float, default=0.05)
    ap.add_argument('--quality-report-dir', default=''); ap.add_argument('--output', default=''); ap.add_argument('--json-output', default='')
    ns=ap.parse_args(argv)
    symbols=[x.strip() for x in ns.symbols.split(',') if x.strip()]
    if not symbols and ns.universe_name: symbols=[x.symbol for x in get_default_etf_universe()]
    cfg=LongPortfolioBacktestConfig(symbols=symbols,start_date=ns.start,end_date=ns.end,frequency=ns.frequency,rebalance_frequency=ns.rebalance_frequency,cache_root=ns.cache_root,min_bars=ns.min_bars,lookback_bars=ns.lookback_bars,initial_cash=ns.initial_cash,portfolio_method=ns.portfolio_method,portfolio_top_n=ns.portfolio_top_n,cash_reserve_ratio=ns.cash_reserve_ratio,max_symbol_weight=ns.max_symbol_weight,max_portfolio_weight=ns.max_portfolio_weight,rebalance_threshold=ns.rebalance_threshold,quality_report_dir=ns.quality_report_dir)
    result=run_long_portfolio_backtest(cfg)
    md=format_long_backtest_markdown(result)
    if ns.output: save_long_backtest_result(result, ns.output)
    else: print(md)
    if ns.json_output: save_long_backtest_result(result, ns.json_output)
    print(f"Long backtest completed: {result.message}; warnings={len(result.warnings)}")
    return 0
if __name__=='__main__': raise SystemExit(main())
