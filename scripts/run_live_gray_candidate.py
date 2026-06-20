#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_gray_candidate.models import LiveGrayCandidateDecision
from qmt_ai_trading.live_gray_candidate.service import *

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage57 read-only small-money gray candidate package.')
    p.add_argument('--repo-root', default='.') ; p.add_argument('--output-dir', default='live_gray_candidate_stage57')
    p.add_argument('--real-cache-quality-dir', default='real_cache_quality_stage56'); p.add_argument('--qmt-dryrun-calibration-dir', default='qmt_dryrun_calibration_stage55')
    p.add_argument('--gray-total-capital-limit', type=float, default=1000); p.add_argument('--single-trade-capital-limit', type=float, default=200); p.add_argument('--daily-trade-capital-limit', type=float, default=300)
    p.add_argument('--max-positions', type=int, default=2); p.add_argument('--max-single-symbol-weight', type=float, default=0.20); p.add_argument('--max-portfolio-exposure', type=float, default=0.50); p.add_argument('--cash-reserve-ratio', type=float, default=0.50); p.add_argument('--max-daily-loss-ratio', type=float, default=0.01); p.add_argument('--max-total-drawdown-ratio', type=float, default=0.03); p.add_argument('--max-orders-per-day', type=int, default=2); p.add_argument('--cooldown-days-after-stop', type=int, default=3)
    p.add_argument('--output', default='live_gray_candidate_stage57/live_gray_candidate.md'); p.add_argument('--json-output', default='live_gray_candidate_stage57/live_gray_candidate.json')
    p.add_argument('--risk-output', default='live_gray_candidate_stage57/gray_risk_limits.md'); p.add_argument('--risk-json-output', default='live_gray_candidate_stage57/gray_risk_limits.json')
    p.add_argument('--approval-output', default='live_gray_candidate_stage57/gray_approval_checklist.md'); p.add_argument('--approval-json-output', default='live_gray_candidate_stage57/gray_approval_checklist.json')
    p.add_argument('--rollback-output', default='live_gray_candidate_stage57/gray_rollback_circuit_breaker.md'); p.add_argument('--rollback-json-output', default='live_gray_candidate_stage57/gray_rollback_circuit_breaker.json')
    p.add_argument('--plan-output', default='live_gray_candidate_stage57/next_gray_approval_package_plan.md'); p.add_argument('--plan-json-output', default='live_gray_candidate_stage57/next_gray_approval_package_plan.json')
    a=p.parse_args(argv)
    cfg=build_default_live_gray_candidate_config(repo_root=a.repo_root, output_dir=a.output_dir, real_cache_quality_dir=a.real_cache_quality_dir, qmt_dryrun_calibration_dir=a.qmt_dryrun_calibration_dir, gray_total_capital_limit=a.gray_total_capital_limit, single_trade_capital_limit=a.single_trade_capital_limit, daily_trade_capital_limit=a.daily_trade_capital_limit, max_positions=a.max_positions, max_single_symbol_weight=a.max_single_symbol_weight, max_portfolio_exposure=a.max_portfolio_exposure, cash_reserve_ratio=a.cash_reserve_ratio, max_daily_loss_ratio=a.max_daily_loss_ratio, max_total_drawdown_ratio=a.max_total_drawdown_ratio, max_orders_per_day=a.max_orders_per_day, cooldown_days_after_stop=a.cooldown_days_after_stop)
    r=run_live_gray_candidate(cfg)
    save_live_gray_candidate_report(r,a.output,a.json_output)
    save_gray_risk_limit_report(run_gray_risk_limit_review(r),a.risk_output,a.risk_json_output)
    save_gray_approval_checklist_report(run_gray_approval_checklist(r),a.approval_output,a.approval_json_output)
    save_gray_rollback_circuit_breaker_report(run_gray_rollback_circuit_breaker_plan(r),a.rollback_output,a.rollback_json_output)
    save_next_gray_approval_package_plan_report(run_next_gray_approval_package_plan(r),a.plan_output,a.plan_json_output)
    print(f'Stage57 live gray candidate package written: {a.output} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if r.decision==LiveGrayCandidateDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
