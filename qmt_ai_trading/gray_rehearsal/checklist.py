from __future__ import annotations
ITEMS=["Confirm the rehearsal is dry-run only.","Confirm no live trading is enabled.","Confirm Risk Gate is required and cannot be bypassed.","Confirm Human Approval is required and cannot be bypassed.","Confirm Paper Trading remains local/dry-run.","Confirm Monitoring / Circuit Breaker can block progression.","Confirm Data Quality Tracking is read-only.","Confirm Agent Research is read-only.","Confirm Live Gray Readiness does not enable live trading.","Confirm Notification Dry Run does not send real messages.","Confirm Dashboard is read-only and has no order entry.","Confirm no xttrader or QMT trading API was called.","Confirm no order was submitted."]
def default_gray_rehearsal_checklist_items(): return list(ITEMS)
def build_gray_rehearsal_checklist(report): return default_gray_rehearsal_checklist_items()
def format_gray_rehearsal_checklist(report): return "\n".join(f"- [ ] {x}" for x in build_gray_rehearsal_checklist(report))
