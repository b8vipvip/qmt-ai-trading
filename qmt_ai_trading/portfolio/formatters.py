from __future__ import annotations
DRY="Portfolio plan is dry-run/paper only and is not an order instruction."
def format_portfolio_snapshot(s): return f"PortfolioSnapshot {s.snapshot_id}: cash={s.cash:.2f} total_asset={s.total_asset:.2f} positions={len(s.positions)} dry_run={s.dry_run}"
def format_portfolio_target(t): return f"- {t.symbol}: target_weight={t.target_weight:.4f} target_value={t.target_value:.2f} score={t.score:.4f} reason={t.reason}"
def format_portfolio_adjustment(a): return f"- {a.symbol}: {a.side} qty={a.quantity} current={a.current_weight:.4f} target={a.target_weight:.4f} delta={a.delta_weight:.4f} reason={a.reason}"
def format_portfolio_plan(p): return format_portfolio_plan_markdown(p)
def format_portfolio_plan_markdown(p):
    lines=["## Portfolio Plan", f"- {DRY}", f"- plan_id: {p.plan_id}", f"- run_id: {p.run_id}", f"- method: {p.method}", f"- total_asset: {p.total_asset:.2f}", f"- investable_asset: {p.investable_asset:.2f}", f"- cash_reserve_ratio: {p.cash_reserve_ratio:.4f}", f"- max_symbol_weight: {p.max_symbol_weight:.4f}", f"- max_portfolio_weight: {p.max_portfolio_weight:.4f}", f"- rebalance_threshold: {p.rebalance_threshold:.4f}", f"- trade_intents count: {len(p.trade_intents)}", "", "### Targets"]
    lines += [format_portfolio_target(t) for t in p.targets] or ['- No targets.']
    lines += ['', '### Adjustments']
    lines += [format_portfolio_adjustment(a) for a in p.adjustments] or ['- No adjustments.']
    lines += ['', '### Warnings']
    lines += [f'- {w}' for w in p.warnings] or ['- No warnings.']
    return '\n'.join(lines)
