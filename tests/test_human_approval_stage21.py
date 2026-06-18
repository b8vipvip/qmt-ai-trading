from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from qmt_ai_trading.approval.formatters import format_approval_request
from qmt_ai_trading.approval.models import ApprovalRequest, ApprovalStatus
from qmt_ai_trading.approval.service import (
    approve_request,
    cancel_request,
    check_approval,
    create_approval_request,
    reject_request,
    require_approval_for_intents,
)
from qmt_ai_trading.approval.store import ApprovalStore
from qmt_ai_trading.common.types import RiskDecision, TradeIntent
from qmt_ai_trading.datahub.local_store import LocalBarStore
from qmt_ai_trading.datahub.models import MarketBar


def _intent() -> TradeIntent:
    return TradeIntent(symbol="510300.SH", side="BUY", quantity=100, target_percent=0.1, source="test", dry_run=True)


def _decision() -> RiskDecision:
    return RiskDecision(allowed=True, reasons=[])


def test_request_instantiates_and_store_roundtrip(tmp_path: Path) -> None:
    req = create_approval_request(run_id="run-1", trade_intents=[_intent()], risk_decisions=[_decision()])
    assert isinstance(req, ApprovalRequest)
    assert req.status == ApprovalStatus.PENDING
    store = ApprovalStore(tmp_path)
    store.save_request(req)
    loaded = store.load_request(req.approval_id)
    assert loaded.approval_id == req.approval_id
    assert loaded.trade_intents[0]["symbol"] == "510300.SH"


def test_list_pending_requests(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path)
    create_approval_request(run_id="run-1", trade_intents=[_intent()], store=store)
    assert len(store.list_requests(ApprovalStatus.PENDING)) == 1


def test_approve_reject_cancel_and_check(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path)
    req = create_approval_request(run_id="run-1", trade_intents=[_intent()], store=store)
    assert check_approval(store, req.approval_id).allowed is False
    assert approve_request(store, req.approval_id, decided_by="local_user").status_after == ApprovalStatus.APPROVED
    assert check_approval(store, req.approval_id).allowed is True
    req2 = create_approval_request(run_id="run-2", trade_intents=[_intent()], store=store)
    reject_request(store, req2.approval_id, decided_by="local_user")
    assert store.load_request(req2.approval_id).status == "REJECTED"
    req3 = create_approval_request(run_id="run-3", trade_intents=[_intent()], store=store)
    cancel_request(store, req3.approval_id, decided_by="local_user")
    assert store.load_request(req3.approval_id).status == "CANCELLED"


def test_require_approval_blocks_pending(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path)
    req = create_approval_request(run_id="run-1", trade_intents=[_intent()], store=store)
    with pytest.raises(PermissionError):
        require_approval_for_intents(store, req.approval_id)


def test_formatter_contains_no_order_notice() -> None:
    req = create_approval_request(run_id="run-1", trade_intents=[_intent()])
    text = format_approval_request(req)
    assert "Approval is not an order. No QMT order has been submitted." in text
    assert "Pending approval; execution is blocked." in text


def test_cli_list_and_approve(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path)
    req = create_approval_request(run_id="run-1", trade_intents=[_intent()], store=store)
    listed = subprocess.run([sys.executable, "scripts/approval_cli.py", "list", "--root", str(tmp_path)], capture_output=True, text=True, check=False)
    assert listed.returncode == 0
    assert "No QMT order has been submitted" in listed.stdout
    approved = subprocess.run([sys.executable, "scripts/approval_cli.py", "approve", "--approval-id", req.approval_id, "--decided-by", "local_user", "--comment", "approved for paper review only", "--root", str(tmp_path)], capture_output=True, text=True, check=False)
    assert approved.returncode == 0
    assert "No QMT order has been submitted" in approved.stdout


def _bars(symbol: str, count: int = 25) -> list[MarketBar]:
    return [MarketBar(symbol, f"2026-05-{i+1:02d}" if i < 23 else f"2026-06-{i-22:02d}", 10+i, 11+i, 9+i, 10.5+i, 1000+i) for i in range(count)]


def test_run_daily_pipeline_create_approval_and_no_intent(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    approvals = tmp_path / "approvals"
    LocalBarStore(cache).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    ok = subprocess.run([sys.executable, "scripts/run_daily_pipeline.py", "--data-source-mode", "cached", "--symbols", "510300.SH", "--cache-root", str(cache), "--research-start", "2026-05-01", "--research-end", "2026-06-02", "--min-bars", "20", "--cached-strategy-top-n", "1", "--create-approval", "--approval-root", str(approvals)], capture_output=True, text=True, check=False)
    assert ok.returncode == 0, ok.stderr + ok.stdout
    assert "approval_id=" in ok.stdout
    assert list(approvals.glob("approval_*.json"))
    empty = subprocess.run([sys.executable, "scripts/run_daily_pipeline.py", "--data-source-mode", "cached", "--symbols", "510500.SH", "--cache-root", str(cache), "--research-start", "2026-05-01", "--research-end", "2026-06-02", "--min-bars", "20", "--create-approval", "--approval-root", str(tmp_path / "empty")], capture_output=True, text=True, check=False)
    assert empty.returncode == 0
    assert "No approval created" in empty.stdout


def test_scheduled_and_register_create_approval(tmp_path: Path) -> None:
    scheduled = subprocess.run([sys.executable, "scripts/run_scheduled_daily_pipeline.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "25", "--warmup-end", "2026-06-02", "--cache-root", str(tmp_path / "sched_cache"), "--data-source-mode", "cached", "--research-start", "2026-05-01", "--research-end", "2026-06-02", "--min-bars", "20", "--cached-strategy-top-n", "1", "--create-approval", "--approval-root", str(tmp_path / "sched_approvals")], capture_output=True, text=True, check=False)
    assert scheduled.returncode == 0, scheduled.stderr + scheduled.stdout
    registered = subprocess.run([sys.executable, "scripts/register_daily_pipeline_task.py", "--data-source-mode", "cached", "--create-approval", "--approval-root", "approvals", "--approval-expires-hours", "24", "--time", "15:30"], capture_output=True, text=True, check=False)
    assert registered.returncode == 0
    assert "--create-approval" in registered.stdout


def test_gitignore_and_roadmap_and_sync_all_untouched() -> None:
    assert "approvals/" in Path(".gitignore").read_text(encoding="utf-8")
    roadmap = Path("docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段二十一：Human Approval 人工确认层" in roadmap
    assert "阶段二十二：Paper Trading / QMT dry-run 适配" in roadmap
    assert "sync_all.ps1" in Path("scripts/sync_all.ps1").read_text(encoding="utf-8", errors="ignore") or Path("scripts/sync_all.ps1").exists()
