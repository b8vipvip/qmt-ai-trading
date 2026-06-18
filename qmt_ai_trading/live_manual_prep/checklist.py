from __future__ import annotations

def default_live_manual_prep_checklist_items():
    return ["Confirm this package is preparation-only.","Confirm live trading remains disabled.","Confirm no live order will be submitted by this package.","Confirm Risk Gate evidence is present and no bypass exists.","Confirm Human Approval evidence is present and explicit.","Confirm Paper Trading evidence is dry-run/local only.","Confirm Live Readiness Audit has no critical failures.","Confirm Monitoring has no CRITICAL alerts and Circuit Breaker is not OPEN.","Confirm Data Quality Tracking is acceptable for manual review.","Confirm Agent Research is read-only.","Confirm Live Gray Readiness does not auto-GO.","Confirm Notification Dry Run did not send real messages.","Confirm Dashboard is read-only and has no order entry.","Confirm Gray Rehearsal was completed.","Confirm Gray Decision Package was reviewed.","Confirm max total capital is extremely small and explicit.","Confirm max single order value is extremely small and explicit.","Confirm allowed symbols are whitelisted.","Confirm no xttrader or QMT trading API was called.","Confirm no account/fund/position/order/trade query was called.","Confirm no order was submitted.","Confirm operator/reviewer/risk owner manually sign before any future separate stage."]
def default_forbidden_items():
    return ["No automatic live enable.","No automatic approval.","No automatic paper submit.","No automatic live submit.","No real notification send.","No xttrader.","No QMT trading API.","No account/fund/position/order/trade query.","No order submission.","No bypassing Risk Gate or Human Approval."]
def default_residual_risks():
    return ["Data quality may still be incomplete.","Paper trading may differ from real execution.","Slippage and liquidity risks remain.","Operational mistakes remain possible.","QMT environment differences remain possible.","Manual approval mistakes remain possible."]
def build_live_manual_prep_checklist(package): return default_live_manual_prep_checklist_items()
def build_live_manual_signoff_placeholders(package):
    return ["Operator signature: ____________________","Reviewer signature: ____________________","Risk owner signature: ____________________","Date: ____________________","Final manual decision: ____________________","Explicit statement: This signature still does not submit orders."]
def format_live_manual_prep_checklist(package):
    return "\n".join(f"- [ ] {x}" for x in build_live_manual_prep_checklist(package))
