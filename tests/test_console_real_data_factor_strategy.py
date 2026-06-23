import json
from pathlib import Path

from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore
from qmt_ai_trading.console_api.routes import research, strategy, risk


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


def test_factor_scan_consumes_real_datahub_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_real_market_artifact()

    run = run_task("factor_scan", {"limit": 3}, TaskStore())
    assert run.status == "SUCCESS"
    assert run.output["data_source"] == "xtdata_live_readonly"
    assert run.output["real_market_data"] is True
    assert run.output["sandbox_fallback"] is False
    assert run.output["factor_candidates"][0]["symbol"] == "510300.SH"
    assert "real_xtdata_readonly" in run.output["factor_candidates"][0]["risk_flags"]
    assert research.candidates()["candidates"]["status"] == "READY"


def test_strategy_dry_run_uses_real_factor_candidates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_real_market_artifact()

    run = run_task("strategy_dry_run_signals", {"limit": 3, "max_positions": 1}, TaskStore())
    assert run.status == "SUCCESS"
    assert run.output["real_market_data"] is True
    assert run.output["trade_intents"]
    assert run.output["trade_intents"][0]["dry_run"] is True
    assert run.output["trade_intents"][0]["no_order_submitted"] is True
    assert run.output["trade_intents"][0]["requires_risk_gate"] is True
    assert strategy.intents()["trade_intents"]["status"] == "READY"


def test_risk_gate_reviews_latest_real_trade_intents(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_real_market_artifact()
    strategy_run = run_task("strategy_dry_run_signals", {"limit": 3, "max_positions": 1}, TaskStore())
    risk_run = run_task("risk_gate_dry_run", {}, TaskStore())

    assert strategy_run.status == "SUCCESS"
    assert risk_run.status == "SUCCESS"
    assert risk_run.output["source"] == "artifacts/reports/console/strategy/trade_intents.json"
    assert risk_run.output["trade_intent_count"] == 1
    assert risk_run.output["decision_count"] == 1
    decision = risk_run.output["decisions"][0]
    assert decision["symbol"] == "510300.SH"
    assert decision["dry_run"] is True
    assert decision["approved"] is False
    assert decision["no_order_submitted"] is True
    assert decision["no_account_query"] is True
    assert decision["risk_gate"] == "unified_risk_gate_dry_run"
    assert risk.decisions()["decisions"]["status"] == "READY"
