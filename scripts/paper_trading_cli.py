#!/usr/bin/env python
"""Local paper trading CLI. It never calls QMT or xttrader."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.approval.store import ApprovalStore
from qmt_ai_trading.paper.formatters import format_paper_order, format_paper_order_list, format_paper_submit_result
from qmt_ai_trading.paper.service import cancel_paper_order, submit_approved_request_to_paper
from qmt_ai_trading.paper.store import PaperOrderStore

def main(argv=None)->int:
    p=argparse.ArgumentParser(description='Local paper trading only. No QMT order is submitted.')
    sub=p.add_subparsers(dest='command', required=True)
    s=sub.add_parser('submit-approved'); s.add_argument('--approval-id', required=True); s.add_argument('--approval-root', default='approvals'); s.add_argument('--paper-root', default='paper_orders')
    l=sub.add_parser('list'); l.add_argument('--paper-root', default='paper_orders'); l.add_argument('--status'); l.add_argument('--approval-id'); l.add_argument('--symbol')
    sh=sub.add_parser('show'); sh.add_argument('--paper-order-id', required=True); sh.add_argument('--paper-root', default='paper_orders')
    c=sub.add_parser('cancel'); c.add_argument('--paper-order-id', required=True); c.add_argument('--paper-root', default='paper_orders'); c.add_argument('--reason', default='manual cancel')
    a=p.parse_args(argv)
    store=PaperOrderStore(a.paper_root)
    if a.command=='submit-approved':
        res=submit_approved_request_to_paper(a.approval_id, ApprovalStore(a.approval_root), store)
        print(format_paper_submit_result(res)); return 0 if res.success else 2
    if a.command=='list': print(format_paper_order_list(store.list_orders(a.status, a.approval_id, a.symbol))); return 0
    if a.command=='show': print(format_paper_order(store.load_order(a.paper_order_id))); return 0
    if a.command=='cancel': print(format_paper_order(cancel_paper_order(a.paper_order_id, store, a.reason))); return 0
    return 1
if __name__=='__main__': raise SystemExit(main())
