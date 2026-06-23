import json
from pathlib import Path

from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore
from qmt_ai_trading.console_api.routes import datahub, research, strategy, risk, paper


def _read(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_market_snapshot_task_updates_datahub_and_market_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run = run_task("market_snapshot_readonly", {"symbol": "510300.SH"}, TaskStore())

    assert run.status == "SUCCESS"
    assert any("artifacts/reports/console/datahub/market_latest.json" in p for p in run.output_artifacts)

    latest = _read("artifacts/reports/console/datahub/market_latest.json")
    assert latest["status"] == "READY"
    assert latest["read_only"] is True
    assert latest["dry_run"] is True
    assert latest["no_order_submitted"] is True
    assert latest["latest"][0]["symbol"] == "510300.SH"
    assert datahub.market_latest()["market"]["status"] == "READY"


def test_factor_strategy_task_updates_research_strategy_and_risk_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run = run_task("factor_strategy_dry_run", {"limit": 3, "max_positions": 2}, TaskStore())

    assert run.status == "SUCCESS"
    assert any("research/factor_candidates.json" in p for p in run.output_artifacts)
    assert any("strategy/trade_intents.json" in p for p in run.output_artifacts)
    assert any("risk/risk_decisions.json" in p for p in run.output_artifacts)

    assert research.candidates()["candidates"]["status"] == "READY"
    assert strategy.intents()["trade_intents"]["status"] == "READY"
    assert risk.decisions()["decisions"]["status"] == "READY"


def test_risk_and_paper_tasks_update_visible_console_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    risk_run = run_task("risk_gate_dry_run", {}, TaskStore())
    paper_run = run_task("paper_trading_dry_run", {}, TaskStore())

    assert risk_run.status == "SUCCESS"
    assert paper_run.status == "SUCCESS"
    assert risk.decisions()["decisions"]["status"] == "READY"
    assert paper.status()["report"]["status"] == "READY"
    assert paper.orders()["orders"] is not None
