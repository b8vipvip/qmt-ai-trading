from __future__ import annotations
import subprocess, sys
from pathlib import Path
from qmt_ai_trading.dashboard.collector import collect_live_env_check_section
from qmt_ai_trading.dashboard.models import DashboardConfig, DashboardStatus
from qmt_ai_trading.live_env_check.checks import check_allowed_symbols, check_capital_config, check_scheduler_preview_text
from qmt_ai_trading.live_env_check.formatters import format_live_env_check_report_markdown
from qmt_ai_trading.live_env_check.models import LiveEnvCheckConfig, LiveEnvCheckDecision, LiveEnvCheckReport, LiveEnvCheckStatus, SAFETY_NOTE
from qmt_ai_trading.live_env_check.safety import contains_forbidden_live_env_action
from qmt_ai_trading.live_env_check.service import run_live_env_check

ROOT=Path(__file__).resolve().parents[1]

def test_models_instantiable():
    assert LiveEnvCheckConfig().to_dict()["allowed_symbols"] == []
    assert LiveEnvCheckReport().safety_note == SAFETY_NOTE

def test_safety_forbidden_markers():
    for text in ["--live-enabled", "--execute-live", "xttrader", "submit_order", "place_order", "real_send", "requests.post", "smtp", "sendMessage", "webhook", "查询资金", "查询持仓", "查询订单", "查询成交"]:
        assert contains_forbidden_live_env_action(text)

def test_allowed_symbols_empty_fail():
    assert check_allowed_symbols(LiveEnvCheckConfig()).status == LiveEnvCheckStatus.FAIL

def test_capital_config_too_large_warn_or_fail():
    item=check_capital_config(LiveEnvCheckConfig(allowed_symbols=["510300.SH"], max_total_capital=100000, max_single_order_value=50000))
    assert item.status in {LiveEnvCheckStatus.WARN, LiveEnvCheckStatus.FAIL}

def test_scheduler_preview_live_enabled_fail():
    assert check_scheduler_preview_text("py script.py --live-enabled").status == LiveEnvCheckStatus.FAIL

def test_run_live_env_check_no_input_runs():
    cfg=LiveEnvCheckConfig(allowed_symbols=["510300.SH"], max_total_capital=5000, max_single_order_value=1000)
    report=run_live_env_check(repo_root=ROOT, config=cfg)
    assert report.decision in {LiveEnvCheckDecision.NEED_MORE_EVIDENCE, LiveEnvCheckDecision.NOT_READY, LiveEnvCheckDecision.READY_FOR_ENV_REVIEW, LiveEnvCheckDecision.BLOCKED}

def test_markdown_contains_safety_note():
    md=format_live_env_check_report_markdown(LiveEnvCheckReport())
    assert "Live environment check is read-only" in md
    assert "Next separate stage" in md

def test_cli_generates_markdown_json(tmp_path):
    md=tmp_path/"live_env_check.md"; js=tmp_path/"live_env_check.json"
    r=subprocess.run([sys.executable, str(ROOT/"scripts/run_live_env_check.py"), "--output", str(md), "--json-output", str(js), "--allowed-symbols", "510300.SH,510500.SH", "--max-total-capital", "5000", "--max-single-order-value", "1000"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert r.returncode == 0, r.stderr
    assert md.exists() and js.exists()

def test_register_task_preview_live_env_check_safe():
    r=subprocess.run([sys.executable, str(ROOT/"scripts/register_daily_pipeline_task.py"), "--enable-live-env-check", "--live-env-check-output-dir", "live_env_check", "--live-env-check-allowed-symbols", "510300.SH,510500.SH", "--live-env-check-max-total-capital", "5000", "--live-env-check-max-single-order-value", "1000"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert r.returncode == 0, r.stderr
    assert "--enable-live-env-check" in r.stdout
    assert "--live-enabled" not in r.stdout
    assert "--execute-live" not in r.stdout

def test_dashboard_collector_live_env_section(tmp_path):
    (tmp_path/"a.live_env_check.md").write_text("Live environment read-only check summary", encoding="utf-8")
    sec=collect_live_env_check_section(DashboardConfig(include_live_env_check=True, live_env_check_dir=str(tmp_path), report_dirs={"live_env_check": str(tmp_path)}))
    assert sec.status == DashboardStatus.OK

def test_gitignore_and_roadmap_stage38_stage39():
    assert "live_env_check/" in (ROOT/".gitignore").read_text(encoding="utf-8")
    rd=(ROOT/"docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段三十八" in rd and "极小资金灰度只读环境核验" in rd
    assert "阶段三十九" in rd and "极小资金灰度最终人工授权包" in rd

def test_sync_all_not_touched_expected_path_exists():
    assert (ROOT/"scripts/sync_all.ps1").exists()
