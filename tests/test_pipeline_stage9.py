from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.gateway import qmt_order
from qmt_ai_trading.pipeline import PipelineResult, build_pipeline_context, run_daily_signal_pipeline, run_etf_daily_pipeline
from qmt_ai_trading.pipeline.report import format_pipeline_report
from qmt_ai_trading.risk.trade_validator import validate_trade_intent
from qmt_ai_trading.strategies.etf_rotation import ETFCandidate
from scripts.run_daily_pipeline import main


def test_build_pipeline_context_creates_context():
    context = build_pipeline_context("2026-06-17", symbols=["510300"])
    assert context.run_id
    assert str(context.trade_date) == "2026-06-17"
    assert context.dry_run is True
    assert context.symbols == ["510300.SH"]


def test_run_daily_signal_pipeline_empty_data_does_not_crash():
    result = run_daily_signal_pipeline(candidates=[])
    assert isinstance(result, PipelineResult)
    assert result.steps
    assert result.trade_intents == []
    assert result.metadata.get("no_intent_reason")


def test_run_etf_daily_pipeline_returns_pipeline_result_with_steps_and_reason_or_intents():
    result = run_etf_daily_pipeline(min_score=60)
    assert isinstance(result, PipelineResult)
    assert result.steps
    assert result.trade_intents or result.metadata.get("no_intent_reason")


def test_all_trade_intents_are_dry_run_and_risk_validatable():
    result = run_daily_signal_pipeline(candidates=[ETFCandidate("510300.SH", score=90, last_price=4.0)])
    assert result.trade_intents
    for intent in result.trade_intents:
        assert isinstance(intent, TradeIntent)
        assert intent.dry_run is True
        assert validate_trade_intent(intent)
    assert result.risk_decisions


def test_pipeline_does_not_call_qmt_place_order(monkeypatch):
    called = {"value": False}

    def fake_place_order(*args, **kwargs):
        called["value"] = True
        raise AssertionError("place_order must not be called by pipeline")

    monkeypatch.setattr(qmt_order, "place_order", fake_place_order)
    result = run_daily_signal_pipeline(candidates=[ETFCandidate("510300.SH", score=90, last_price=4.0)])
    assert result.success
    assert called["value"] is False


def test_format_pipeline_report_returns_string_with_dry_run_or_shadow():
    result = run_etf_daily_pipeline(min_score=60)
    report = format_pipeline_report(result)
    assert isinstance(report, str)
    assert "dry-run" in report or "shadow" in report
    assert "Run ID" in report


def test_run_daily_pipeline_script_main_importable_and_runs(capsys):
    exit_code = main(["--date", "2026-06-17", "--symbols", "510300.SH"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Daily Signal Report" in captured.out
    assert "dry-run" in captured.out or "shadow" in captured.out
