import json
from pathlib import Path

from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore
from qmt_ai_trading.console_api.routes import portfolio


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_order_preview_uses_account_market_intent_and_never_submits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_json(Path("artifacts/reports/console/account_readonly/account_readonly_report.json"), {
        "status": "SUCCESS",
        "report": {
            "status": "SUCCESS",
            "enabled": True,
            "account_query_enabled": True,
            "position_query_enabled": True,
            "mock_data": False,
            "asset": {"cash": 52001.92, "total_asset": 52001.92, "market_value": 0},
            "positions": {"position_count": 0, "positions": []},
        },
    })
    _write_json(Path("artifacts/reports/console/datahub/market_latest.json"), {
        "status": "READY",
        "latest": [{"symbol": "510300.SH", "period": "1d", "close": 4.898, "real_market_data": True}],
    })
    _write_json(Path("artifacts/reports/console/strategy/trade_intents.json"), {
        "status": "READY",
        "trade_intents": [{"intent_id": "intent-1", "symbol": "510300.SH", "side": "BUY", "target_weight": 0.02}],
    })
    _write_json(Path("artifacts/reports/console/risk/risk_decisions.json"), {
        "status": "READY",
        "decisions": [{"intent_id": "intent-1", "symbol": "510300.SH", "decision": "PASS_DRY_RUN"}],
    })

    run = run_task("order_preview_dry_run", {"max_single_order_amount": 1000, "min_lot": 100}, TaskStore())

    assert run.status == "SUCCESS"
    assert run.output["real_order_submitted"] is False
    assert run.output["no_order_submitted"] is True
    preview = run.output["previews"][0]
    assert preview["status"] == "PREVIEW_BUY_READY_NOT_SUBMITTED"
    assert preview["preview_quantity"] == 100
    assert preview["estimated_amount"] == 489.8
    assert preview["can_submit_order"] is False
    assert portfolio.status()["preview_count"] == 1
    assert portfolio.preview()["previews"][0]["symbol"] == "510300.SH"
