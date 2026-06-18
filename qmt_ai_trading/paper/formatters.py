"""CLI formatting helpers for local paper trading."""
from __future__ import annotations
from .models import PaperExecutionReport, PaperOrder, PaperSubmitResult
NOTICE = 'Paper trading only. No QMT order has been submitted.'
def _v(x): return getattr(x, 'value', str(x))
def format_paper_order(order: PaperOrder) -> str:
    lines=[NOTICE, f'PaperOrder ID: {order.paper_order_id}', f'Approval ID: {order.approval_id}', f'Run ID: {order.run_id}', f'Symbol: {order.symbol}', f'Side: {_v(order.side)}', f'Quantity: {order.quantity}', f'Status: {_v(order.status)}', f'Filled: {order.filled_quantity} @ {order.filled_price}', f'Dry run: {order.dry_run}']
    if _v(order.status)=='REJECTED' or order.reason: lines.append(f'Reason: {order.reason}')
    return '\n'.join(lines)
def format_paper_execution_report(report: PaperExecutionReport) -> str:
    return '\n'.join([NOTICE, f'Report ID: {report.report_id}', f'Approval ID: {report.approval_id}', f'Run ID: {report.run_id}', f'Total orders: {report.total_orders}', f'Filled: {report.filled_count}', f'Rejected: {report.rejected_count}', f'Cancelled: {report.cancelled_count}', f'Success: {report.success}', f'Message: {report.message}'])
def format_paper_submit_result(result: PaperSubmitResult) -> str:
    lines=[NOTICE, f'Approval ID: {result.approval_id}', f'Allowed: {result.allowed}', f'Success: {result.success}', f'Message: {result.message}', f'Orders: {len(result.orders)}']
    for o in result.orders: lines.append(f'- {o.paper_order_id} {o.symbol} {_v(o.side)} qty={o.quantity} status={_v(o.status)} reason={o.reason}')
    if result.report: lines.append(f'Report ID: {result.report.report_id}')
    return '\n'.join(lines)
def format_paper_order_list(orders: list[PaperOrder]) -> str:
    lines=[NOTICE, f'Paper orders: {len(orders)}']
    for o in orders: lines.append(f'- {o.paper_order_id} approval={o.approval_id} symbol={o.symbol} side={_v(o.side)} qty={o.quantity} status={_v(o.status)} reason={o.reason}')
    return '\n'.join(lines)
