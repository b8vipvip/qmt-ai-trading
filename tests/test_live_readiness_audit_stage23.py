import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.audit.checks import (
    check_gitignore_runtime_dirs,
    check_human_approval_exists,
    check_live_trading_disabled,
    check_no_xttrader_import_outside_gateway,
    check_paper_trading_exists,
    check_required_docs,
    check_risk_gate_exists,
    check_roadmap_stage_alignment,
)
from qmt_ai_trading.audit.formatters import format_audit_report_markdown
from qmt_ai_trading.audit.models import AuditCheckResult, AuditReport, AuditSeverity, AuditStatus, GoNoGoDecision, LiveReadinessPolicy
from qmt_ai_trading.audit.service import run_live_readiness_audit

ROOT = Path(__file__).resolve().parents[1]


def test_policy_default_allow_go_false():
    assert LiveReadinessPolicy().allow_go is False


def test_audit_check_result_instantiates():
    r = AuditCheckResult("id", "name", AuditStatus.PASS, AuditSeverity.INFO, "ok")
    assert r.to_dict()["status"] == "PASS"


def test_audit_report_instantiates():
    r = AuditReport("rid", "now", str(ROOT))
    assert r.decision == GoNoGoDecision.NO_GO


def test_required_docs_exist():
    assert check_required_docs(ROOT).status == AuditStatus.PASS


def test_roadmap_stage_alignment_mentions_stage23_and_24():
    assert check_roadmap_stage_alignment(ROOT).status == AuditStatus.PASS


def test_gitignore_runtime_dirs():
    r = check_gitignore_runtime_dirs(ROOT)
    assert r.status == AuditStatus.PASS
    assert not r.metadata.get("missing_patterns")


def test_risk_gate_exists():
    assert check_risk_gate_exists(ROOT).status == AuditStatus.PASS


def test_human_approval_exists():
    assert check_human_approval_exists(ROOT).status == AuditStatus.PASS


def test_paper_trading_exists():
    assert check_paper_trading_exists(ROOT).status == AuditStatus.PASS


def test_live_trading_disabled_no_crash():
    assert check_live_trading_disabled(ROOT).status in {AuditStatus.PASS, AuditStatus.WARN}


def test_no_xttrader_import_outside_gateway():
    assert check_no_xttrader_import_outside_gateway(ROOT).status == AuditStatus.PASS


def test_audit_default_decision_no_go():
    report = run_live_readiness_audit(ROOT)
    assert report.decision == GoNoGoDecision.NO_GO


def test_audit_allow_go_false_no_go_even_without_critical_requirement():
    report = run_live_readiness_audit(ROOT, LiveReadinessPolicy(allow_go=False))
    assert report.decision == GoNoGoDecision.NO_GO
    assert "GO disabled by policy" in report.summary or report.fail_count > 0


def test_markdown_contains_permission_warning():
    report = run_live_readiness_audit(ROOT)
    assert "This audit report is not permission to trade" in format_audit_report_markdown(report)


def test_cli_runs_to_stdout():
    cp = subprocess.run([sys.executable, "scripts/run_live_readiness_audit.py", "--project-root", "."], cwd=ROOT, text=True, capture_output=True)
    assert cp.returncode == 0
    assert "Live Readiness Audit Report" in cp.stdout


def test_cli_writes_markdown(tmp_path):
    out = tmp_path / "reports" / "live_readiness_audit.md"
    cp = subprocess.run([sys.executable, "scripts/run_live_readiness_audit.py", "--project-root", ".", "--output", str(out)], cwd=ROOT, text=True, capture_output=True)
    assert cp.returncode == 0
    assert out.exists()
    assert "This audit report is not permission to trade" in out.read_text(encoding="utf-8")


def test_roadmap_contains_stage23_and_stage24_names():
    text = (ROOT / "docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段二十三" in text and "实盘前安全审计" in text
    assert "阶段二十四" in text and "QMT 实机数据联调与真实缓存质量验证" in text


def test_sync_all_not_modified_in_stage23():
    cp = subprocess.run(["git", "diff", "--", "scripts/sync_all.ps1"], cwd=ROOT, text=True, capture_output=True)
    assert cp.returncode == 0
    assert cp.stdout == ""


def test_stage22_and_stage21_tests_still_pass_smoke():
    for test_file in ["tests/test_human_approval_stage21.py", "tests/test_paper_trading_stage22.py"]:
        cp = subprocess.run([sys.executable, "-m", "pytest", test_file], cwd=ROOT, text=True, capture_output=True)
        assert cp.returncode == 0, cp.stdout + cp.stderr
