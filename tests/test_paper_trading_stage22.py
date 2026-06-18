from __future__ import annotations
import subprocess, sys
from pathlib import Path

from qmt_ai_trading.approval.models import ApprovalRequest, ApprovalStatus
from qmt_ai_trading.approval.store import ApprovalStore
from qmt_ai_trading.paper.broker import PaperBroker
from qmt_ai_trading.paper.formatters import format_paper_submit_result
from qmt_ai_trading.paper.models import PaperOrder, PaperOrderSide, PaperOrderStatus, PaperSubmitResult
from qmt_ai_trading.paper.service import check_approval_for_paper, submit_approved_request_to_paper
from qmt_ai_trading.paper.store import PaperOrderStore


def req(status='APPROVED', allowed=True, aid='a1'):
    return ApprovalRequest(aid,'run1','2026-06-18T00:00:00Z','2099-01-01T00:00:00Z',status,[{'symbol':'510300.SH','side':'BUY','quantity':100,'target_percent':0.1,'source':'test'}],[{'allowed':allowed,'reasons':[]}])

def test_paper_order_store_and_list(tmp_path):
    o=PaperOrder('o1','a1','r1','510300.SH',PaperOrderSide.BUY,100)
    assert o.dry_run is True
    st=PaperOrderStore(tmp_path); st.save_order(o)
    assert st.load_order('o1').symbol=='510300.SH'
    assert len(st.list_orders(approval_id='a1', symbol='510300.SH'))==1

def test_broker_statuses_and_rejections(tmp_path):
    st=PaperOrderStore(tmp_path)
    filled=PaperBroker(st, auto_fill=True, default_fill_price=1.2).submit_order(PaperOrder('o1','a','r','510300.SH','BUY',100))
    assert filled.status == 'FILLED'
    submitted=PaperBroker(st, auto_fill=False).submit_order(PaperOrder('o2','a','r','510300.SH','SELL',100))
    assert submitted.status == 'SUBMITTED'
    assert PaperBroker(st).submit_order(PaperOrder('o3','a','r','510300.SH','SELL',0)).status == 'REJECTED'
    assert PaperBroker(st).submit_order(PaperOrder('o4','a','r','510300.SH','BUY',99)).status == 'REJECTED'

def test_approval_checks_and_submit(tmp_path):
    assert check_approval_for_paper(req('APPROVED')).allowed is True
    assert check_approval_for_paper(req('PENDING')).allowed is False
    astore=ApprovalStore(tmp_path/'approvals'); pstore=PaperOrderStore(tmp_path/'paper')
    astore.save_request(req('PENDING', aid='pending'))
    assert submit_approved_request_to_paper('pending', astore, pstore).allowed is False
    astore.save_request(req('APPROVED', aid='bad', allowed=False))
    assert submit_approved_request_to_paper('bad', astore, pstore).success is False
    astore.save_request(req('APPROVED', aid='ok', allowed=True))
    res=submit_approved_request_to_paper('ok', astore, pstore)
    assert res.allowed is True and res.orders and res.report
    assert 'No QMT order has been submitted' in format_paper_submit_result(res)

def test_scripts_and_docs(tmp_path):
    paper=tmp_path/'paper'; approvals=tmp_path/'approvals'; astore=ApprovalStore(approvals)
    astore.save_request(req('PENDING', aid='p'))
    cp=subprocess.run([sys.executable,'scripts/paper_trading_cli.py','list','--paper-root',str(paper)], text=True, capture_output=True)
    assert cp.returncode == 0 and 'No QMT order has been submitted' in cp.stdout
    cp=subprocess.run([sys.executable,'scripts/paper_trading_cli.py','submit-approved','--approval-id','p','--approval-root',str(approvals),'--paper-root',str(paper)], text=True, capture_output=True)
    assert cp.returncode != 0 and 'blocked' in cp.stdout
    astore.save_request(req('APPROVED', aid='ok2'))
    cp=subprocess.run([sys.executable,'scripts/paper_trading_cli.py','submit-approved','--approval-id','ok2','--approval-root',str(approvals),'--paper-root',str(paper)], text=True, capture_output=True)
    assert cp.returncode == 0 and 'Orders: 1' in cp.stdout
    cp=subprocess.run([sys.executable,'scripts/run_paper_from_latest_approval.py','--approval-root',str(approvals),'--paper-root',str(paper)], text=True, capture_output=True)
    assert cp.returncode == 0 and 'No QMT order has been submitted' in cp.stdout
    assert 'paper_orders/' in Path('.gitignore').read_text(encoding='utf-8')
    roadmap=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '阶段二十二：Paper Trading / QMT dry-run 适配' in roadmap
    assert '阶段二十三：实盘前安全审计' in roadmap
    assert Path('scripts/sync_all.ps1').exists()
