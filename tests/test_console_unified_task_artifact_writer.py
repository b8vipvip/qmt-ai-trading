import json
from pathlib import Path

from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore
from qmt_ai_trading.console_api.artifact_writer import write_task_output_to_console_artifacts
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


def test_xtdata_live_task_normalizes_real_market_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = Path("local_console_xtdata_live_stage87")
    out.mkdir()
    (out / "xtdata_live_bars.json").write_text(json.dumps({
        "status": "REAL_MARKET_DATA",
        "symbol": "510300.SH",
        "period": "1d",
        "real_market_data": True,
        "sandbox_fallback": False,
        "bars": [
            {"time": "20260623", "open": 3.91, "high": 3.96, "low": 3.88, "close": 3.94, "volume": 1200000},
        ],
    }), encoding="utf-8")
    (out / "xtdata_live_snapshots.json").write_text(json.dumps({"snapshots": []}), encoding="utf-8")

    written = write_task_output_to_console_artifacts("xtdata_live_readonly_smoke", {
        "task_id": "xtdata_live_readonly_smoke",
        "output_dir": "local_console_xtdata_live_stage87",
        "provider": "xtdata_live_readonly",
        "real_market_data": True,
        "sandbox_fallback": False,
        "period": "1d",
        "read_only": True,
        "no_order_submitted": True,
    })

    assert any("datahub/market_latest.json" in p for p in written)
    latest = _read("artifacts/reports/console/datahub/market_latest.json")
    row = latest["latest"][0]
    assert row["symbol"] == "510300.SH"
    assert row["period"] == "1d"
    assert row["time"] == "20260623"
    assert row["open"] == 3.91
    assert row["high"] == 3.96
    assert row["low"] == 3.88
    assert row["close"] == 3.94
    assert row["volume"] == 1200000
    assert row["source"] == "xtdata_live_readonly"
    assert row["real_market_data"] is True
    assert row["sandbox_fallback"] is False


def test_candidate_and_strategy_tasks_update_visible_console_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run = run_task("etf_rotation_candidates", {"limit": 3}, TaskStore())

    assert run.status == "SUCCESS"
    assert any("research/factor_candidates.json" in p for p in run.output_artifacts)
    assert any("strategy/trade_intents.json" in p for p in run.output_artifacts)

    assert research.candidates()["candidates"]["status"] == "READY"
    assert strategy.signals()["signals"]["status"] == "READY"
    assert strategy.intents()["trade_intents"]["status"] == "READY"


def test_risk_and_paper_tasks_update_visible_console_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    risk_run = run_task("risk_gate_dry_run", {}, TaskStore())
    paper_run = run_task("paper_trading_dry_run", {}, TaskStore())

    assert risk_run.status == "SUCCESS"
    assert paper_run.status == "SUCCESS"
    assert risk.decisions()["decisions"]["status"] == "READY"
    assert paper.status()["report"]["status"] == "READY"
    assert paper.orders()["orders"] is not None
