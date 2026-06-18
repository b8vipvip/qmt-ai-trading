import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.liveprep.models import LiveGrayConfig, LiveGrayReadinessReport, LiveGrayDecision, LiveGrayCheckStatus
from qmt_ai_trading.liveprep.gates import check_live_switches, check_capital_limits, check_symbol_whitelist, check_quality_required, check_circuit_breaker_required
from qmt_ai_trading.liveprep.service import run_live_gray_readiness_check
from qmt_ai_trading.liveprep.formatters import format_live_gray_report_markdown

class Intent: symbol="159915.SZ"

def test_defaults():
    assert LiveGrayConfig().live_enabled is False
    assert LiveGrayConfig().gray_enabled is False
    assert LiveGrayReadinessReport().decision == LiveGrayDecision.NO_GO

def test_gates():
    cfg=LiveGrayConfig()
    assert check_live_switches(cfg)[0].status in {LiveGrayCheckStatus.SKIP, LiveGrayCheckStatus.FAIL}
    assert any(c.status==LiveGrayCheckStatus.FAIL for c in check_capital_limits(LiveGrayConfig(max_total_capital=999999)))
    assert check_symbol_whitelist(cfg)[0].status==LiveGrayCheckStatus.FAIL
    assert any(c.status==LiveGrayCheckStatus.FAIL for c in check_symbol_whitelist(LiveGrayConfig(allowed_symbols=["510300.SH"]), [Intent()]))
    assert check_quality_required(cfg, {"quality_level":"UNKNOWN"})[0].status==LiveGrayCheckStatus.FAIL
    assert check_quality_required(LiveGrayConfig(allow_unknown_quality_for_review=True), {"quality_level":"UNKNOWN"})[0].status==LiveGrayCheckStatus.WARN
    assert check_circuit_breaker_required(cfg, {"state":"OPEN"})[0].status==LiveGrayCheckStatus.FAIL

def test_service_and_format():
    assert run_live_gray_readiness_check().decision==LiveGrayDecision.NO_GO
    r=run_live_gray_readiness_check(config=LiveGrayConfig(gray_enabled=True, allowed_symbols=["510300.SH"]))
    assert r.decision != LiveGrayDecision.READY_FOR_MANUAL_REVIEW
    good=LiveGrayConfig(gray_enabled=True, allowed_symbols=["510300.SH"], require_human_approval=False, require_risk_gate=False, require_paper_trading=False, require_live_readiness_audit=False, require_monitoring=False, require_agent_research=False, require_circuit_breaker_closed=False, require_quality_pass=False)
    r2=run_live_gray_readiness_check(config=good)
    assert r2.decision in {LiveGrayDecision.READY_FOR_MANUAL_REVIEW, LiveGrayDecision.NO_GO, LiveGrayDecision.BLOCKED}
    assert "preparation report only" in format_live_gray_report_markdown(r2)

def test_cli_and_gitignore(tmp_path):
    md=tmp_path/"r.md"; js=tmp_path/"r.json"
    cp=subprocess.run([sys.executable,"scripts/run_live_gray_readiness.py","--output",str(md),"--json-output",str(js),"--allowed-symbols","510300.SH"], text=True, capture_output=True)
    assert cp.returncode==0 and md.exists() and js.exists()
    data=json.loads(js.read_text(encoding="utf-8")); assert data["config"]["live_enabled"] is False
    cp2=subprocess.run([sys.executable,"scripts/run_live_gray_readiness.py","--gray-enabled","--allowed-symbols","510300.SH"], text=True, capture_output=True)
    assert cp2.returncode==0 and "live_enabled: False" in cp2.stdout
    gi=Path('.gitignore').read_text(encoding='utf-8'); assert 'live_gray_reports/' in gi or 'live_gray_reports_stage30/' in gi
    roadmap=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8'); assert '阶段三十' in roadmap and '小资金实盘灰度准备' in roadmap and '阶段三十一' in roadmap and 'UI / Dashboard' in roadmap
