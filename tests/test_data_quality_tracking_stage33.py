from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.data_quality.models import DataQualityLedgerEntry, DataQualityTrackingReport
from qmt_ai_trading.data_quality.safety import contains_forbidden_trading_access
from qmt_ai_trading.data_quality.ledger import load_quality_reports_from_dir, build_ledger_entries_from_quality_reports
from qmt_ai_trading.data_quality.trend import build_quality_trends
from qmt_ai_trading.data_quality.incidents import detect_coverage_incidents, detect_missing_bar_incidents
from qmt_ai_trading.data_quality.service import run_data_quality_tracking
from qmt_ai_trading.data_quality.formatters import format_data_quality_tracking_markdown
from qmt_ai_trading.monitoring.models import MonitoringConfig
from qmt_ai_trading.monitoring.rules import detect_data_quality_tracking_events
from qmt_ai_trading.dashboard.models import DashboardConfig
from qmt_ai_trading.dashboard.collector import collect_data_quality_tracking_section


def test_models_instantiable():
    e=DataQualityLedgerEntry("e1", symbol="510300.SH", trade_date="2026-06-18")
    r=DataQualityTrackingReport("r1", ledger_entries=[e])
    assert r.to_dict()["safety_note"]

def test_safety_forbids_xttrader():
    assert contains_forbidden_trading_access("import xttrader")

def test_missing_report_dir_empty(tmp_path):
    assert load_quality_reports_from_dir(tmp_path/"missing") == []

def test_build_ledger_from_simple_qmt_quality():
    reports=[{"symbol":"510300.SH","end_date":"2026-06-18","decision":"PASS","normalized_bar_count":20,"duplicate_datetime_count":0,"missing_ohlc_count":0,"zero_volume_count":0}]
    entries=build_ledger_entries_from_quality_reports(reports)
    assert entries and entries[0].symbol=="510300.SH" and entries[0].quality_level=="PASS"

def test_trends_counts_levels():
    entries=[DataQualityLedgerEntry("1",symbol="A",trade_date="2026-06-15",quality_level="PASS",coverage_ratio=1),DataQualityLedgerEntry("2",symbol="A",trade_date="2026-06-16",quality_level="WARN",coverage_ratio=.7),DataQualityLedgerEntry("3",symbol="B",trade_date="2026-06-16",quality_level="FAIL",coverage_ratio=.3),DataQualityLedgerEntry("4",symbol="C",trade_date="2026-06-16",quality_level="UNKNOWN",coverage_ratio=0)]
    trends=build_quality_trends(entries)
    assert sum(t.pass_count for t in trends)==1 and sum(t.warn_count for t in trends)==1 and sum(t.fail_count for t in trends)==1 and sum(t.unknown_count for t in trends)==1

def test_incidents_detected():
    e=DataQualityLedgerEntry("e",symbol="A",trade_date="2026-06-18",coverage_ratio=.2,missing_bars=2)
    assert detect_coverage_incidents([e])
    assert detect_missing_bar_incidents([e])

def test_empty_tracking_and_markdown():
    r=run_data_quality_tracking()
    md=format_data_quality_tracking_markdown(r)
    assert "Data quality tracking is read-only" in md

def test_cli_generates_outputs(tmp_path):
    md=tmp_path/"dq.md"; js=tmp_path/"dq.json"
    cp=subprocess.run([sys.executable,"scripts/run_data_quality_tracking.py","--output",str(md),"--json-output",str(js)],cwd=Path.cwd(),text=True,capture_output=True)
    assert cp.returncode==0 and md.exists() and js.exists()

def test_monitoring_events_handles_report():
    r=run_data_quality_tracking()
    r.trends=[]
    assert detect_data_quality_tracking_events(r, MonitoringConfig()) == []

def test_dashboard_section_empty(tmp_path):
    cfg=DashboardConfig(include_data_quality_tracking=True, data_quality_dir=str(tmp_path/"missing"))
    sec=collect_data_quality_tracking_section(cfg)
    assert str(sec.status).endswith("EMPTY")

def test_cli_args_acceptance_for_pipeline_scripts(tmp_path):
    cp=subprocess.run([sys.executable,"scripts/run_daily_pipeline.py","--data-source-mode","legacy","--enable-data-quality-tracking","--data-quality-tracking-output-dir",str(tmp_path/"dq")],text=True,capture_output=True)
    assert cp.returncode==0
    cp2=subprocess.run([sys.executable,"scripts/run_scheduled_daily_pipeline.py","--data-source-mode","legacy","--enable-data-quality-tracking","--data-quality-tracking-output-dir",str(tmp_path/"dq2")],text=True,capture_output=True)
    assert cp2.returncode==0
    cp3=subprocess.run([sys.executable,"scripts/register_daily_pipeline_task.py","--enable-data-quality-tracking","--data-quality-tracking-output-dir","data_quality_tracking","--data-quality-tracking-report-dir","qmt_data_quality_reports"],text=True,capture_output=True)
    assert cp3.returncode==0 and "--enable-data-quality-tracking" in cp3.stdout

def test_gitignore_and_roadmap_and_sync_unchanged_text():
    assert "data_quality_tracking/" in Path(".gitignore").read_text(encoding="utf-8")
    road=Path("docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段三十三：真实 QMT 数据质量长期追踪" in road
    assert "阶段三十四：真实通知 dry-run 接入准备" in road
    assert Path("scripts/sync_all.ps1").exists()
