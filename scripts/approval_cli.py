#!/usr/bin/env python
"""Local human approval CLI.

This CLI only edits approval JSON files. It never submits QMT orders and never
calls xttrader.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.approval.formatters import format_approval_decision, format_approval_list, format_approval_request
from qmt_ai_trading.approval.models import ApprovalStatus
from qmt_ai_trading.approval.service import approve_request, cancel_request, reject_request
from qmt_ai_trading.approval.store import ApprovalStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review local human approval requests. No order is submitted.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_list = sub.add_parser("list")
    p_list.add_argument("--root", default="approvals")
    p_list.add_argument("--status", default=None, choices=[s.value for s in ApprovalStatus])
    p_show = sub.add_parser("show")
    p_show.add_argument("--approval-id", required=True)
    p_show.add_argument("--root", default="approvals")
    for name in ("approve", "reject", "cancel"):
        p = sub.add_parser(name)
        p.add_argument("--approval-id", required=True)
        p.add_argument("--decided-by", required=True)
        p.add_argument("--comment", default="")
        p.add_argument("--root", default="approvals")
    args = parser.parse_args(argv)
    store = ApprovalStore(args.root)
    if args.command == "list":
        print(format_approval_list(store.list_requests(args.status)))
        return 0
    if args.command == "show":
        print(format_approval_request(store.load_request(args.approval_id)))
        return 0
    if args.command == "approve":
        decision = approve_request(store, args.approval_id, decided_by=args.decided_by, comment=args.comment)
    elif args.command == "reject":
        decision = reject_request(store, args.approval_id, decided_by=args.decided_by, comment=args.comment)
    else:
        decision = cancel_request(store, args.approval_id, decided_by=args.decided_by, comment=args.comment)
    print(format_approval_decision(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
