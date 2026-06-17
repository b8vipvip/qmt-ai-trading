from pathlib import Path

from qmt_ai_trading.reporting.models import NotificationTarget, ReportArtifact
from qmt_ai_trading.reporting.notifier import notify_email, notify_report, notify_telegram, notify_wecom
from qmt_ai_trading.reporting.writer import ensure_report_dir, write_html_report, write_json_report, write_markdown_report, write_pipeline_reports
from qmt_ai_trading.pipeline.daily_runner import run_daily_signal_pipeline
from qmt_ai_trading.strategies.etf_rotation import ETFCandidate
from scripts.run_daily_pipeline import main


def _result():
    return run_daily_signal_pipeline(candidates=[ETFCandidate("510300.SH", score=90, last_price=4.0)])


def test_report_artifact_instantiable(tmp_path):
    artifact = ReportArtifact(path=tmp_path / "daily_report.md", format="markdown", title="Daily")
    assert artifact.format == "markdown"
    assert artifact.created_at


def test_notification_target_instantiable():
    target = NotificationTarget(channel="email", destination="placeholder", dry_run=True)
    assert target.channel == "email"
    assert target.enabled is True
    assert target.dry_run is True


def test_ensure_report_dir_creates_temp_dir(tmp_path):
    path = ensure_report_dir(tmp_path / "reports")
    assert path.exists()
    assert path.is_dir()


def test_write_markdown_report_writes_md(tmp_path):
    artifact = write_markdown_report(_result(), tmp_path)
    assert Path(artifact.path).name == "daily_report.md"
    assert Path(artifact.path).read_text(encoding="utf-8").startswith("# QMT AI Trading")


def test_write_json_report_writes_json(tmp_path):
    artifact = write_json_report(_result(), tmp_path)
    text = Path(artifact.path).read_text(encoding="utf-8")
    assert Path(artifact.path).name == "daily_report.json"
    assert '"context"' in text
    assert '"trade_intents"' in text


def test_write_html_report_writes_html(tmp_path):
    artifact = write_html_report(_result(), tmp_path)
    text = Path(artifact.path).read_text(encoding="utf-8")
    assert Path(artifact.path).name == "daily_report.html"
    assert "<html" in text


def test_write_pipeline_reports_returns_multiple_artifacts(tmp_path):
    artifacts = write_pipeline_reports(_result(), tmp_path)
    assert {item.format for item in artifacts} == {"markdown", "json", "html"}
    assert all(Path(item.path).exists() for item in artifacts)


def test_notify_report_dry_run_does_not_send():
    results = notify_report([], dry_run=True)
    assert results
    assert all(item.success for item in results)
    assert all(item.dry_run for item in results)


def test_notify_email_dry_run_returns_success_message():
    result = notify_email([], dry_run=True)
    assert result.success
    assert "dry-run" in result.message


def test_notify_telegram_dry_run_returns_success_message():
    result = notify_telegram([], dry_run=True)
    assert result.success
    assert "dry-run" in result.message


def test_notify_wecom_dry_run_returns_success_message():
    result = notify_wecom([], dry_run=True)
    assert result.success
    assert "dry-run" in result.message


def test_run_daily_pipeline_default_still_runs(capsys):
    code = main(["--date", "2026-06-17", "--symbols", "510300.SH"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Daily Signal Report" in captured.out


def test_run_daily_pipeline_write_reports_to_temp_dir(tmp_path, capsys):
    code = main(["--date", "2026-06-17", "--symbols", "510300.SH", "--write-reports", "--report-dir", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "Reports written" in captured.out
    assert (tmp_path / "daily_report.md").exists()
    assert (tmp_path / "daily_report.json").exists()
    assert (tmp_path / "daily_report.html").exists()


def test_reports_gitignore_entries_present():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "reports/" in gitignore
    assert "*.report.json" in gitignore
    assert "daily_report.json" in gitignore
    assert "daily_report.html" in gitignore
    assert "daily_report.md" in gitignore


def test_sync_all_ps1_not_modified():
    import subprocess

    result = subprocess.run(["git", "diff", "--", "scripts/sync_all.ps1"], check=True, capture_output=True, text=True)
    assert result.stdout == ""
