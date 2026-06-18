#!/usr/bin/env python
"""Submit the latest APPROVED approval request to local paper trading."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.approval.models import ApprovalStatus
from qmt_ai_trading.approval.store import ApprovalStore
from qmt_ai_trading.paper.formatters import NOTICE, format_paper_submit_result
from qmt_ai_trading.paper.service import submit_approved_request_to_paper
from qmt_ai_trading.paper.store import PaperOrderStore

def main(argv=None):
    p=argparse.ArgumentParser(description='Run latest approved approval through local paper trading only.')
    p.add_argument('--approval-root', default='approvals'); p.add_argument('--paper-root', default='paper_orders')
    a=p.parse_args(argv); astore=ApprovalStore(a.approval_root)
    approved=astore.list_requests(ApprovalStatus.APPROVED)
    if not approved:
        print(NOTICE); print('WARNING: no APPROVED approval request found; nothing submitted.'); return 0
    latest=sorted(approved, key=lambda r: str(r.created_at))[-1]
    print(format_paper_submit_result(submit_approved_request_to_paper(latest.approval_id, astore, PaperOrderStore(a.paper_root))))
    return 0
if __name__=='__main__': raise SystemExit(main())
