import json
from pathlib import Path

from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore
from qmt_ai_trading.console_api.routes import approval


def _seed_real_market_artifact():
    root = Path("artifacts/reports/console/datahub")
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, close in enumerate([4.80, 4.84, 4.88, 4.93, 4.97, 5.02, 5.08]):
        rows.append({
            "symbol": "510300.SH",
            "period": "1d",
            "time": f"202606{10+i:02d}",
            "open": close - 0.02,
            "high": close + 0.03,
            "low": close - 0.04,
            "close": close,
            "volume": 1000000 + i * 10000,
            "amount": 5000000 + i * 10000,
            "source": "xtdata_live_readonly",
            "real_market_data": True,
            "sandbox_fallback": False,
        })
    (root / "market_latest.json").write_text(json.dumps({
        "status": "READY",
        "source": "xtdata_live_readonly",
        "real_market_data": True,
        "sandbox_fallback": False,
        "latest": rows,
    }), encoding="utf-8")


def test_human_approval_review_consumes_paper_shadow_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_real_market_artifact()
    store = TaskStore()
    run_task("strategy_dry_run_signals", {"limit": 3, "max_positions": 1}, store)
    run_task("risk_gate_dry_run", {}, store)
    run_task("paper_trading_dry_run", {}, store)
    approval_run = run_task("human_approval_review_dry_run", {}, store)

    assert approval_run.status == "SUCCESS"
    assert approval_run.output["approval_status"]["status"] == "MANUAL_REVIEW_ONLY"
    assert approval_run.output["approval_status"]["approval_enabled"] is False
    assert approval_run.output["approval_requests"]
    request = approval_run.output["approval_requests"][0]
    assert request["symbol"] == "510300.SH"
    assert request["risk_decision"] == "PASS_DRY_RUN"
    assert request["paper_status"] == "PAPER_ACCEPTED_NO_FILL_QUANTITY_ZERO"
    assert request["can_approve_live"] is False
    assert request["review_only"] is True
    assert request["real_order_submitted"] is False
    assert approval.status()["approval_enabled"] is False
    assert approval.requests()["requests"][0]["approval_status"] == "PENDING_REVIEW_ONLY"
