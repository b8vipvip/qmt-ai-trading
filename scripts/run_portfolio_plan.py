#!/usr/bin/env python
"""Build a dry-run/paper portfolio plan from cached ETF research."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.research.cache_scoring import score_etf_universe_from_cache
from qmt_ai_trading.strategies.cached_etf_rotation import CachedETFSignalConfig, build_cached_etf_candidates
from qmt_ai_trading.portfolio.allocator import PortfolioAllocationConfig
from qmt_ai_trading.portfolio.rebalance import PortfolioRebalanceConfig
from qmt_ai_trading.portfolio.service import build_portfolio_plan_from_candidates, save_portfolio_plan
from qmt_ai_trading.portfolio.formatters import format_portfolio_plan_markdown
from qmt_ai_trading.portfolio.models import to_jsonable
import json

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate dry-run/paper PortfolioPlan from cached ETF candidates; no QMT/xttrader/order calls.')
    p.add_argument('--cache-root', default='market_data'); p.add_argument('--research-start', required=True); p.add_argument('--research-end', required=True)
    p.add_argument('--research-frequency', default='1d'); p.add_argument('--min-bars', type=int, default=20)
    p.add_argument('--method', default='score_weight', choices=['equal_weight','score_weight','risk_adjusted_weight']); p.add_argument('--top-n', type=int, default=2)
    p.add_argument('--total-asset', type=float, default=1000000.0); p.add_argument('--current-cash', type=float, default=None)
    p.add_argument('--cash-reserve-ratio', type=float, default=0.2); p.add_argument('--max-symbol-weight', type=float, default=0.3); p.add_argument('--max-portfolio-weight', type=float, default=0.8)
    p.add_argument('--rebalance-threshold', type=float, default=0.05); p.add_argument('--snapshot-path', default=None); p.add_argument('--output', default=None); p.add_argument('--json-output', default=None)
    a=p.parse_args(argv)
    scores,dataset=score_etf_universe_from_cache(start_date=a.research_start,end_date=a.research_end,frequency=a.research_frequency,cache_root=a.cache_root,min_bars=a.min_bars,allow_partial=True)
    cands,_=build_cached_etf_candidates(scores, CachedETFSignalConfig(top_n=a.top_n,min_bars=a.min_bars))
    plan=build_portfolio_plan_from_candidates(cands, run_id='run_portfolio_plan', total_asset=a.total_asset, current_cash=a.current_cash if a.current_cash is not None else a.total_asset, snapshot_path=a.snapshot_path, allocation_config=PortfolioAllocationConfig(method=a.method,top_n=a.top_n,cash_reserve_ratio=a.cash_reserve_ratio,max_symbol_weight=a.max_symbol_weight,max_portfolio_weight=a.max_portfolio_weight), rebalance_config=PortfolioRebalanceConfig(rebalance_threshold=a.rebalance_threshold))
    plan.metadata['cached_research']={'message':dataset.message,'loaded_symbols':dataset.loaded_symbols,'failed_symbols':dataset.failed_symbols}
    md=format_portfolio_plan_markdown(plan)
    print(md)
    if a.output:
        Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(md,encoding='utf-8')
    if a.json_output:
        Path(a.json_output).parent.mkdir(parents=True,exist_ok=True); Path(a.json_output).write_text(json.dumps(to_jsonable(plan),ensure_ascii=False,indent=2),encoding='utf-8')
    return 0
if __name__=='__main__': raise SystemExit(main())
