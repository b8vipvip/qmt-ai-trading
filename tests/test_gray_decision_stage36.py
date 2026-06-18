from __future__ import annotations
import subprocess, sys
from pathlib import Path
from qmt_ai_trading.gray_decision.models import GrayDecisionConfig, GrayDecisionPackage, GrayDecision, GrayDecisionEvidenceType, SAFETY_NOTE
from qmt_ai_trading.gray_decision.safety import contains_forbidden_gray_decision_action
from qmt_ai_trading.gray_decision.evidence import collect_evidence_from_file
from qmt_ai_trading.gray_decision.service import run_gray_decision_package
from qmt_ai_trading.gray_decision.formatters import format_gray_decision_package_markdown
from qmt_ai_trading.dashboard.collector import collect_gray_decision_section
from qmt_ai_trading.dashboard.models import DashboardConfig, DashboardStatus

def test_models_and_safety():
    assert GrayDecisionConfig().max_total_capital == 5000.0
    assert GrayDecisionPackage().safety_note
    for text in ["--live-enabled", "xttrader", "submit_order", "place_order", "real_send", "requests.post", "smtp", "sendMessage", "webhook", "查询资金", "查询持仓", "查询订单", "查询成交"]:
        assert contains_forbidden_gray_decision_action(text)

def test_evidence_missing_and_blocker(tmp_path):
    ev=collect_evidence_from_file(tmp_path/"missing.md", GrayDecisionEvidenceType.RISK_GATE)
    assert str(ev.status) in {"GrayDecisionEvidenceStatus.MISSING", "MISSING"}
    f=tmp_path/"bad.md"; f.write_text("xttrader --live-enabled submit_order", encoding="utf-8")
    ev2=collect_evidence_from_file(f, GrayDecisionEvidenceType.RISK_GATE)
    assert str(ev2.status).endswith("FAIL")

def test_package_and_markdown():
    pkg=run_gray_decision_package()
    assert pkg.decision in {GrayDecision.NEED_MORE_EVIDENCE, GrayDecision.NOT_ELIGIBLE}
    md=format_gray_decision_package_markdown(pkg)
    assert SAFETY_NOTE in md and "manual-only" in md

def test_cli_generates_markdown_json(tmp_path):
    md=tmp_path/"p.md"; js=tmp_path/"p.json"
    cp=subprocess.run([sys.executable,"scripts/run_gray_decision_package.py","--output",str(md),"--json-output",str(js),"--allowed-symbols","510300.SH,510500.SH"], text=True, capture_output=True)
    assert cp.returncode == 0, cp.stderr
    assert md.exists() and js.exists() and "Gray decision package summary" in md.read_text(encoding="utf-8")

def test_daily_scheduled_register_and_dashboard(tmp_path):
    cp=subprocess.run([sys.executable,"scripts/run_daily_pipeline.py","--data-source-mode","mock","--enable-gray-decision-package","--gray-decision-output-dir",str(tmp_path/"gd"),"--gray-decision-allowed-symbols","510300.SH"], text=True, capture_output=True)
    assert cp.returncode == 0, cp.stderr
    assert "Gray Decision Package" in cp.stdout
    cp2=subprocess.run([sys.executable,"scripts/run_scheduled_daily_pipeline.py","--data-source-mode","mock","--enable-gray-decision-package","--gray-decision-output-dir",str(tmp_path/"gd2"),"--gray-decision-allowed-symbols","510300.SH"], text=True, capture_output=True)
    assert cp2.returncode == 0, cp2.stderr
    reg=subprocess.run([sys.executable,"scripts/register_daily_pipeline_task.py","--data-source-mode","mock","--enable-gray-decision-package","--gray-decision-output-dir","gray_decision","--gray-decision-allowed-symbols","510300.SH,510500.SH","--gray-decision-max-total-capital","5000","--gray-decision-max-single-order-value","1000"], text=True, capture_output=True)
    assert reg.returncode == 0, reg.stderr
    assert "--enable-gray-decision-package" in reg.stdout and "--live-enabled" not in reg.stdout
    (tmp_path/"gdsec").mkdir(); (tmp_path/"gdsec"/"latest.gray_decision.md").write_text("# Gray Decision\n"+SAFETY_NOTE, encoding="utf-8")
    sec=collect_gray_decision_section(DashboardConfig(include_gray_decision=True, gray_decision_dir=str(tmp_path/"gdsec"), report_dirs={"gray_decision":str(tmp_path/"gdsec")}))
    assert sec.status == DashboardStatus.OK

def test_gitignore_and_roadmap_and_sync_untouched():
    gi=Path('.gitignore').read_text(encoding='utf-8')
    assert 'gray_decision/' in gi or 'gray_decision_stage36/' in gi
    roadmap=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '阶段三十六：小资金灰度准入复核 / 人工决策包' in roadmap
    assert '阶段三十七：极小资金灰度实盘人工审批准备' in roadmap
    assert Path('scripts/sync_all.ps1').exists()
