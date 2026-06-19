import json, subprocess, sys
from pathlib import Path

from qmt_ai_trading.live_gray_ledger.formatters import format_live_gray_ledger_report_markdown
from qmt_ai_trading.live_gray_ledger.models import LiveGrayLedgerConfig, LiveGrayLedgerDecision, LiveGrayLedgerReport, LiveGrayLedgerSeverity, LiveGrayLedgerStatus
from qmt_ai_trading.live_gray_ledger.safety import classify_ledger_marker, scan_ledger_text_for_forbidden_markers
from qmt_ai_trading.live_gray_ledger.service import build_default_live_gray_ledger_config, run_live_gray_ledger


def test_config_and_report_defaults():
    assert LiveGrayLedgerConfig().repo_root == "."
    assert LiveGrayLedgerReport().decision == LiveGrayLedgerDecision.NEED_MORE_EVIDENCE


def test_missing_evidence_does_not_crash(tmp_path):
    report = run_live_gray_ledger(build_default_live_gray_ledger_config(repo_root=tmp_path))
    assert report.decision in {LiveGrayLedgerDecision.NEED_MORE_EVIDENCE, LiveGrayLedgerDecision.BLOCKED}


def test_redline_ready_pass(tmp_path):
    d = tmp_path / "redline_review_stage40"; d.mkdir()
    (d / "redline_review.json").write_text(json.dumps({"decision":"READY_FOR_REDLINE_REVIEW","summary":{"critical":0}}), encoding="utf-8")
    report = run_live_gray_ledger(build_default_live_gray_ledger_config(repo_root=tmp_path))
    ev = [e for e in report.evidence if e.path.endswith("redline_review.json")][0]
    assert ev.status == LiveGrayLedgerStatus.PASS
    assert report.decision != LiveGrayLedgerDecision.BLOCKED


def test_redline_blocked_blocks(tmp_path):
    d = tmp_path / "redline_review_stage40"; d.mkdir()
    (d / "redline_review.json").write_text(json.dumps({"decision":"BLOCKED","summary":{"critical":1}}), encoding="utf-8")
    report = run_live_gray_ledger(build_default_live_gray_ledger_config(repo_root=tmp_path))
    assert report.decision == LiveGrayLedgerDecision.BLOCKED


def test_marker_context_classification():
    doc = scan_ledger_text_for_forbidden_markers("禁止 xttrader marker", "docs/stage41.md")
    assert doc and doc[0].severity == LiveGrayLedgerSeverity.WARN
    critical = scan_ledger_text_for_forbidden_markers("xttrader place_order query_stock_asset", "scripts/live_exec.py")
    assert any(x.severity == LiveGrayLedgerSeverity.CRITICAL for x in critical)
    assert classify_ledger_marker("place_order", "tests/test_x.py", "marker place_order")[1] == LiveGrayLedgerSeverity.WARN


def test_formatter_contains_safety_note():
    text = format_live_gray_ledger_report_markdown(LiveGrayLedgerReport())
    assert "## Safety Note" in text
    assert "不是实盘授权" in text


def test_cli_generates_markdown_json(tmp_path):
    out = tmp_path / "ledger" / "live_gray_ledger.md"; jout = tmp_path / "ledger" / "live_gray_ledger.json"
    cp = subprocess.run([sys.executable, "scripts/run_live_gray_ledger.py", "--repo-root", str(tmp_path), "--output", str(out), "--json-output", str(jout)], text=True, capture_output=True)
    assert cp.returncode == 0
    assert out.exists() and jout.exists()
    assert "xttrader" in out.read_text(encoding="utf-8")


def test_daily_pipeline_ledger_option(tmp_path):
    out = tmp_path / "daily_ledger"
    cp = subprocess.run([sys.executable, "scripts/run_daily_pipeline.py", "--symbols", "159915.SZ", "--data-source-mode", "mock", "--enable-live-gray-ledger", "--live-gray-ledger-output-dir", str(out)], text=True, capture_output=True)
    assert cp.returncode == 0, cp.stderr + cp.stdout
    assert (out / "live_gray_ledger.md").exists()


def test_scheduled_pipeline_ledger_option(tmp_path):
    out = tmp_path / "scheduled_ledger"
    cp = subprocess.run([sys.executable, "scripts/run_scheduled_daily_pipeline.py", "--data-source-mode", "mock", "--enable-live-gray-ledger", "--live-gray-ledger-output-dir", str(out)], text=True, capture_output=True)
    assert cp.returncode == 0, cp.stderr + cp.stdout
    assert (out / "live_gray_ledger.md").exists()


def test_register_preview_ledger_no_registration(tmp_path):
    cp = subprocess.run([sys.executable, "scripts/register_daily_pipeline_task.py", "--enable-live-gray-ledger", "--live-gray-ledger-output-dir", str(tmp_path / "ledger"), "--time", "15:30"], text=True, capture_output=True)
    assert cp.returncode == 0
    assert "--enable-live-gray-ledger" in cp.stdout
    assert "dry-run only; no task registered" in cp.stdout


def test_runtime_ignores_and_sync_untouched():
    assert "validation_logs/" in Path(".gitignore").read_text(encoding="utf-8")
    assert "live_gray_ledger_stage41/" in Path(".gitignore").read_text(encoding="utf-8")
    assert not subprocess.run(["git", "diff", "--quiet", "--", "scripts/sync_all.ps1"]).returncode
