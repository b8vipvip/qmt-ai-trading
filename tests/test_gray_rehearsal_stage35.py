from pathlib import Path
import subprocess, sys

from qmt_ai_trading.gray_rehearsal.models import GrayRehearsalConfig, GrayRehearsalReport, SAFETY_NOTE, GrayRehearsalScenarioType
from qmt_ai_trading.gray_rehearsal.safety import contains_forbidden_gray_rehearsal_action
from qmt_ai_trading.gray_rehearsal.scenarios import build_default_rehearsal_scenarios
from qmt_ai_trading.gray_rehearsal.service import run_gray_rehearsal
from qmt_ai_trading.gray_rehearsal.formatters import format_gray_rehearsal_report_markdown
from qmt_ai_trading.dashboard.collector import collect_gray_rehearsal_section
from qmt_ai_trading.dashboard.models import DashboardConfig, DashboardStatus


def test_config_default_and_report_instantiation():
    assert GrayRehearsalConfig().rehearsal_dry_run is True
    assert GrayRehearsalReport().safety_note == SAFETY_NOTE


def test_safety_forbidden_terms():
    for text in ["--live-enabled", "xttrader", "submit_order", "place_order", "real_send", "requests.post", "smtp", "sendMessage", "webhook", "查询资金", "查询持仓", "查询订单", "查询成交"]:
        assert contains_forbidden_gray_rehearsal_action(text)


def test_default_scenarios_complete():
    scenarios=set(build_default_rehearsal_scenarios(GrayRehearsalConfig()))
    assert {GrayRehearsalScenarioType.NORMAL_DRY_RUN, GrayRehearsalScenarioType.RISK_GATE_BLOCKED, GrayRehearsalScenarioType.DATA_QUALITY_UNKNOWN, GrayRehearsalScenarioType.CIRCUIT_BREAKER_OPEN, GrayRehearsalScenarioType.LIVE_GRAY_NO_GO, GrayRehearsalScenarioType.NOTIFICATION_DRY_RUN, GrayRehearsalScenarioType.DASHBOARD_READ_ONLY} <= scenarios


def test_run_and_format_no_input():
    report=run_gray_rehearsal()
    md=format_gray_rehearsal_report_markdown(report)
    assert SAFETY_NOTE in md
    assert "Gray rehearsal summary" in md


def test_cli_generates_markdown_json(tmp_path):
    md=tmp_path/"gray.md"; js=tmp_path/"gray.json"
    proc=subprocess.run([sys.executable,"scripts/run_gray_rehearsal.py","--output",str(md),"--json-output",str(js),"--allowed-symbols","510300.SH,510500.SH"], cwd=Path.cwd(), text=True, capture_output=True)
    assert proc.returncode == 0, proc.stderr
    assert md.exists() and js.exists()
    assert SAFETY_NOTE in md.read_text(encoding="utf-8")


def test_daily_pipeline_enable_gray_rehearsal_runs(tmp_path):
    proc=subprocess.run([sys.executable,"scripts/run_daily_pipeline.py","--data-source-mode","mock","--enable-gray-rehearsal","--gray-rehearsal-output-dir",str(tmp_path)], cwd=Path.cwd(), text=True, capture_output=True)
    assert proc.returncode == 0, proc.stderr
    assert "## Gray Rehearsal" in proc.stdout


def test_scheduled_and_register_gray_rehearsal(tmp_path):
    proc=subprocess.run([sys.executable,"scripts/run_scheduled_daily_pipeline.py","--data-source-mode","mock","--enable-gray-rehearsal","--gray-rehearsal-output-dir",str(tmp_path)], cwd=Path.cwd(), text=True, capture_output=True)
    assert proc.returncode == 0, proc.stderr
    reg=subprocess.run([sys.executable,"scripts/register_daily_pipeline_task.py","--data-source-mode","mock","--enable-gray-rehearsal","--gray-rehearsal-output-dir","gray_rehearsal","--gray-rehearsal-allowed-symbols","510300.SH,510500.SH"], cwd=Path.cwd(), text=True, capture_output=True)
    assert reg.returncode == 0, reg.stderr
    assert "--enable-gray-rehearsal" in reg.stdout
    assert "--gray-rehearsal-output-dir" in reg.stdout


def test_dashboard_gray_rehearsal_section(tmp_path):
    (tmp_path/"latest.gray_rehearsal.md").write_text("# Gray Rehearsal\n"+SAFETY_NOTE, encoding="utf-8")
    section=collect_gray_rehearsal_section(DashboardConfig(include_gray_rehearsal=True, gray_rehearsal_dir=str(tmp_path), report_dirs={"gray_rehearsal":str(tmp_path)}))
    assert section.status == DashboardStatus.OK
    assert "Gray Rehearsal" in section.html


def test_gitignore_and_docs_stage35():
    gi=Path(".gitignore").read_text(encoding="utf-8")
    assert "gray_rehearsal/" in gi or "gray_rehearsal_stage35/" in gi
    roadmap=Path("docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段三十五" in roadmap and "小资金灰度人工流程演练" in roadmap
    assert "阶段三十六" in roadmap and "小资金灰度准入复核 / 人工决策包" in roadmap
