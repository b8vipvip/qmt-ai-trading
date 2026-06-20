from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_gray_candidate.models import *
from qmt_ai_trading.live_gray_candidate.service import *
from qmt_ai_trading.live_gray_candidate.formatters import format_live_gray_candidate_report_markdown
from qmt_ai_trading.live_gray_candidate.safety import scan_live_gray_candidate_text_for_forbidden_markers

def _write_stage56(root, decision="READY_FOR_REAL_CACHE_QUALITY_REVIEW", critical=0):
    d=root/"real_cache_quality_stage56"; d.mkdir(); (d/"real_cache_quality.json").write_text(json.dumps({"decision":decision,"summary":{"critical":critical},"coverage":[{"symbol":"510300.SH"}]}),encoding='utf-8')
    for n in ["long_sample_gap_fill.json","field_quality_review.json","next_backtest_attribution_plan.json"]: (d/n).write_text("{}",encoding='utf-8')
def _write_stage55(root, decision="READY", critical=0):
    d=root/"qmt_dryrun_calibration_stage55"; d.mkdir(); (d/"qmt_dryrun_calibration.json").write_text(json.dumps({"decision":decision,"summary":{"critical":critical}}),encoding='utf-8'); (d/"etf_whitelist_calibration.json").write_text(json.dumps({"validated_symbols":["510500.SH"]}),encoding='utf-8')
def _roadmap(root):
    p=root/"docs"; p.mkdir(); (p/"qmt-ai-trading-project-roadmap.md").write_text("完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）\nStage61：API Gateway 基础层\nStage75：本地控制台封版 / 可选桌面化\nUI 不直接访问 QMT\nUI 不能绕过 Risk Gate\nUI 不能绕过 Human Approval\nUI 不能自动 approve",encoding='utf-8')

def test_config_and_report_defaults():
    cfg=LiveGrayCandidateConfig(); rpt=LiveGrayCandidateReport(); assert cfg.gray_total_capital_limit==1000.0; assert rpt.decision==LiveGrayCandidateDecision.NEED_MORE_EVIDENCE

def test_missing_stage56_does_not_crash(tmp_path):
    _roadmap(tmp_path); _write_stage55(tmp_path); r=run_live_gray_candidate(build_default_live_gray_candidate_config(repo_root=tmp_path)); assert r.decision in {LiveGrayCandidateDecision.NEED_MORE_EVIDENCE, LiveGrayCandidateDecision.NO_GO}

def test_stage56_ready_allows_review(tmp_path):
    _roadmap(tmp_path); _write_stage56(tmp_path); _write_stage55(tmp_path); r=run_live_gray_candidate(build_default_live_gray_candidate_config(repo_root=tmp_path)); assert r.decision==LiveGrayCandidateDecision.READY_FOR_GRAY_CANDIDATE_REVIEW

def test_stage56_need_more_evidence(tmp_path):
    _roadmap(tmp_path); _write_stage56(tmp_path,"NEED_MORE_EVIDENCE",0); _write_stage55(tmp_path); r=run_live_gray_candidate(build_default_live_gray_candidate_config(repo_root=tmp_path)); assert r.decision==LiveGrayCandidateDecision.NEED_MORE_EVIDENCE

def test_no_go_conditions(tmp_path):
    _roadmap(tmp_path); _write_stage56(tmp_path,"NO_GO",0); _write_stage55(tmp_path); assert run_live_gray_candidate(build_default_live_gray_candidate_config(repo_root=tmp_path)).decision==LiveGrayCandidateDecision.NO_GO
    tmp2=tmp_path/"b"; tmp2.mkdir(); _roadmap(tmp2); _write_stage56(tmp2); _write_stage55(tmp2,"NO_GO",0); assert run_live_gray_candidate(build_default_live_gray_candidate_config(repo_root=tmp2)).decision==LiveGrayCandidateDecision.NO_GO

def test_conservative_limits_and_sections(tmp_path):
    _roadmap(tmp_path); _write_stage56(tmp_path); _write_stage55(tmp_path)
    cfg=build_default_live_gray_candidate_config(repo_root=tmp_path, gray_total_capital_limit=99999, single_trade_capital_limit=99999, daily_trade_capital_limit=99999, max_single_symbol_weight=0.9, max_portfolio_exposure=0.9)
    assert cfg.gray_total_capital_limit<=1000 and cfg.single_trade_capital_limit<=cfg.gray_total_capital_limit and cfg.daily_trade_capital_limit<=cfg.gray_total_capital_limit and cfg.max_portfolio_exposure<=0.5 and cfg.max_single_symbol_weight<=0.2
    r=run_live_gray_candidate(cfg); md=format_live_gray_candidate_report_markdown(r)
    assert "510300.SH" in r.allowed_symbols and "510500.SH" in r.allowed_symbols
    assert "Risk Gate" in md and "Human Approval" in md and "Rollback" in md and "Safety Note" in md and "不代表实盘授权" in md

def test_safety_marker_classification():
    crit=scan_live_gray_candidate_text_for_forbidden_markers("xttrader XtQuantTrader place_order query_stock_asset", "actual executable")
    assert all(x["severity"]=="CRITICAL" for x in crit)
    warn=scan_live_gray_candidate_text_for_forbidden_markers("xttrader place_order", "docs/tests/safety marker definitions")
    assert all(x["severity"]=="WARN" for x in warn)
    assert not scan_live_gray_candidate_text_for_forbidden_markers("xtdata xtquant.xtdata", "actual executable")

def test_cli_generates_all_outputs(tmp_path):
    _roadmap(tmp_path); _write_stage56(tmp_path); _write_stage55(tmp_path); out=tmp_path/"out"
    cmd=[sys.executable,"scripts/run_live_gray_candidate.py","--repo-root",str(tmp_path),"--output-dir",str(out),"--output",str(out/"live_gray_candidate.md"),"--json-output",str(out/"live_gray_candidate.json"),"--risk-output",str(out/"gray_risk_limits.md"),"--risk-json-output",str(out/"gray_risk_limits.json"),"--approval-output",str(out/"gray_approval_checklist.md"),"--approval-json-output",str(out/"gray_approval_checklist.json"),"--rollback-output",str(out/"gray_rollback_circuit_breaker.md"),"--rollback-json-output",str(out/"gray_rollback_circuit_breaker.json"),"--plan-output",str(out/"next_gray_approval_package_plan.md"),"--plan-json-output",str(out/"next_gray_approval_package_plan.json")]
    assert subprocess.run(cmd, cwd=Path.cwd()).returncode==0
    for n in ["live_gray_candidate.md","live_gray_candidate.json","gray_risk_limits.md","gray_risk_limits.json","gray_approval_checklist.md","gray_approval_checklist.json","gray_rollback_circuit_breaker.md","gray_rollback_circuit_breaker.json","next_gray_approval_package_plan.md","next_gray_approval_package_plan.json"]: assert (out/n).exists()

def test_repo_static_requirements():
    assert Path("scripts/sync_all.ps1").exists()
    roadmap=Path("docs/qmt-ai-trading-project-roadmap.md").read_text(encoding='utf-8')
    for s in ["完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）","Stage61：API Gateway 基础层","Stage75：本地控制台封版 / 可选桌面化","UI 不直接访问 QMT","UI 不能绕过 Risk Gate","UI 不能绕过 Human Approval","UI 不能自动 approve"]: assert s in roadmap
    val=Path("scripts/validate_stage57.ps1").read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in val and 'Print-File' in val and 'Check-NoBackup' in val
    assert not list(Path("scripts").glob("validate_stage56.ps1.bak_stage56fix_*"))
