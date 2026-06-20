import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_gray_final_approval.models import *
from qmt_ai_trading.live_gray_final_approval.service import *
from qmt_ai_trading.live_gray_final_approval.formatters import format_live_gray_final_approval_report_markdown
from qmt_ai_trading.live_gray_final_approval.safety import classify_live_gray_final_approval_marker, scan_live_gray_final_approval_text_for_forbidden_markers

REQUIRED_ROADMAP=['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']

def _base(tmp_path, s57='READY_FOR_GRAY_CANDIDATE_REVIEW', c57=0, s56='READY_FOR_REAL_CACHE_QUALITY_REVIEW', c56=0, s55='READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW', c55=0):
    root=tmp_path
    (root/'docs').mkdir(parents=True); (root/'docs/qmt-ai-trading-project-roadmap.md').write_text('\n'.join(REQUIRED_ROADMAP), encoding='utf-8')
    for d,n,dec,crit in [('live_gray_candidate_stage57','live_gray_candidate.json',s57,c57),('real_cache_quality_stage56','real_cache_quality.json',s56,c56),('qmt_dryrun_calibration_stage55','qmt_dryrun_calibration.json',s55,c55)]:
        p=root/d; p.mkdir(); (p/n).write_text(json.dumps({'decision':dec,'summary':{'critical':crit}}, ensure_ascii=False), encoding='utf-8')
    return build_default_live_gray_final_approval_config(repo_root=root)

def test_config_and_report_default_constructible():
    assert LiveGrayFinalApprovalConfig()
    assert LiveGrayFinalApprovalReport().decision == LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE

def test_missing_stage57_does_not_crash(tmp_path):
    cfg=_base(tmp_path); (tmp_path/'live_gray_candidate_stage57/live_gray_candidate.json').unlink()
    r=run_live_gray_final_approval(cfg)
    assert r.decision in {LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE, LiveGrayFinalApprovalDecision.NO_GO}

def test_decision_transitions(tmp_path):
    assert run_live_gray_final_approval(_base(tmp_path/'a')).decision == LiveGrayFinalApprovalDecision.READY_FOR_FINAL_APPROVAL_REVIEW
    assert run_live_gray_final_approval(_base(tmp_path/'b', s57='NEED_MORE_EVIDENCE')).decision == LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE
    assert run_live_gray_final_approval(_base(tmp_path/'c', s57='NO_GO')).decision == LiveGrayFinalApprovalDecision.NO_GO
    assert run_live_gray_final_approval(_base(tmp_path/'d', c57=1)).decision == LiveGrayFinalApprovalDecision.NO_GO
    assert run_live_gray_final_approval(_base(tmp_path/'e', s56='NO_GO')).decision == LiveGrayFinalApprovalDecision.NO_GO
    assert run_live_gray_final_approval(_base(tmp_path/'f', c56=1)).decision == LiveGrayFinalApprovalDecision.NO_GO
    assert run_live_gray_final_approval(_base(tmp_path/'g', s55='NO_GO')).decision == LiveGrayFinalApprovalDecision.NO_GO
    assert run_live_gray_final_approval(_base(tmp_path/'h', c55=1)).decision == LiveGrayFinalApprovalDecision.NO_GO

def test_approval_tables_complete(tmp_path):
    r=run_live_gray_final_approval(_base(tmp_path))
    cap='\n'.join(i.name for i in r.capital_position_items); risk='\n'.join(i.name for i in r.risk_human_items); rb='\n'.join(i.name for i in r.rollback_circuit_items); sig='\n'.join(i.role for i in r.signoff_items)
    for x in ['总资金上限','单笔上限','单日上限','单标的上限','组合暴露上限','现金保留比例','最大持仓数','最大下单次数','人工签字状态','不代表实盘授权声明']: assert x in cap
    for x in ['Risk Gate 不可绕过','Human Approval 不可绕过','不自动 approve','RiskDecision 必须 allowed=True','Approval 必须显式 APPROVED','未批准不得进入 paper/live','UI 未来也不能绕过 Risk Gate / Human Approval','未来真实执行仍需单独审批']: assert x in risk
    for x in ['数据质量异常回滚','Risk Gate 异常回滚','Human Approval 缺失回滚','单日亏损触发熔断','总回撤触发熔断','连续错误触发熔断','通知失败时处理','日志缺失时处理','人工暂停流程','恢复前复核流程']: assert x in rb
    for x in ['策略负责人签字','风控负责人签字','运行负责人签字','数据负责人签字','最终授权人签字','确认 Stage58 不代表实盘授权','确认 Stage59 仍不得直接实盘','确认不调用 xttrader','确认不真实下单','确认不查询真实账户','确认不真实通知']: assert x in sig

def test_safety_marker_classification():
    for m in ['xttrader','XtQuantTrader','place_order','query_stock_asset']:
        assert classify_live_gray_final_approval_marker(m,'actual executable').value == 'CRITICAL'
    assert classify_live_gray_final_approval_marker('xttrader','generated final approval').value == 'WARN'
    assert scan_live_gray_final_approval_text_for_forbidden_markers('xtdata xtquant.xtdata','actual executable') == []

def test_generated_stage55_stage56_stage57_safety_notes_are_not_critical():
    samples=[
        ('qmt_dryrun_calibration_stage55/qmt_dryrun_calibration.md','Stage55 不调用 xttrader，不真实下单。'),
        ('real_cache_quality_stage56/real_cache_quality.json','{"safety_note":"Stage56 不调用 xttrader，不查询资金。"}'),
        ('live_gray_candidate_stage57/live_gray_candidate.md','Stage57 禁止调用 xttrader，READY_FOR_GRAY_CANDIDATE_REVIEW 不是实盘授权。'),
    ]
    for context, text in samples:
        findings=scan_live_gray_final_approval_text_for_forbidden_markers(text, context)
        assert findings
        assert all(f['severity'] != 'CRITICAL' for f in findings)

def test_docs_and_tests_marker_definitions_are_warn():
    docs=scan_live_gray_final_approval_text_for_forbidden_markers('禁止调用 xttrader；不真实下单。','docs/stage58-final-human-approval-before-small-money-gray.md')
    tests=scan_live_gray_final_approval_text_for_forbidden_markers("FORBIDDEN=['xttrader','order_stock']  # safety marker definitions",'tests/test_live_gray_final_approval_stage58.py')
    assert docs and tests
    assert all(f['severity'] == 'WARN' for f in docs + tests)

def test_executable_python_dangerous_markers_are_critical():
    samples=[
        ('import xttrader','xttrader'),
        ('from xtquant import xttrader\ntrader = XtQuantTrader()','XtQuantTrader'),
        ('order_stock("510300.SH", 100)\nplace_order({})\nquery_stock_asset()','order_stock'),
    ]
    for text, expected in samples:
        findings=scan_live_gray_final_approval_text_for_forbidden_markers(text, 'qmt_ai_trading/gateway/live_executor.py')
        assert any(f['marker'] == expected and f['severity'] == 'CRITICAL' for f in findings)

def test_formatter_safety_note(tmp_path):
    md=format_live_gray_final_approval_report_markdown(run_live_gray_final_approval(_base(tmp_path)))
    assert '## Safety Note' in md and 'READY_FOR_FINAL_APPROVAL_REVIEW 只表示' in md and '不是实盘授权' in md

def test_cli_generates_all_outputs(tmp_path):
    cfg=_base(tmp_path)
    out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_live_gray_final_approval.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'live_gray_final_approval.md'),'--json-output',str(out/'live_gray_final_approval.json'),'--capital-output',str(out/'capital_position_approval.md'),'--capital-json-output',str(out/'capital_position_approval.json'),'--risk-output',str(out/'risk_human_approval_review.md'),'--risk-json-output',str(out/'risk_human_approval_review.json'),'--rollback-output',str(out/'rollback_circuit_approval.md'),'--rollback-json-output',str(out/'rollback_circuit_approval.json'),'--signoff-output',str(out/'final_signoff_checklist.md'),'--signoff-json-output',str(out/'final_signoff_checklist.json'),'--plan-output',str(out/'next_readonly_seal_plan.md'),'--plan-json-output',str(out/'next_readonly_seal_plan.json')]
    res=subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    assert 'decision=READY_FOR_FINAL_APPROVAL_REVIEW' in res.stdout
    for name in ['live_gray_final_approval','capital_position_approval','risk_human_approval_review','rollback_circuit_approval','final_signoff_checklist','next_readonly_seal_plan']:
        assert (out/f'{name}.md').exists() and (out/f'{name}.json').exists()

def test_pipeline_and_register_args_generate(tmp_path):
    out=tmp_path/'daily'
    res=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'cache'),'--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-live-gray-final-approval','--live-gray-final-approval-output-dir',str(out)], cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True)
    assert res.returncode in (0,1)
    assert (out/'live_gray_final_approval.md').exists()
    prev=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-live-gray-final-approval','--live-gray-final-approval-output-dir','live_gray_final_approval','--time','15:30'], cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True)
    assert prev.returncode == 0
    assert 'enable_live_gray_final_approval=True' in prev.stdout and 'no_task_registered=True' in prev.stdout

def test_repo_guardrails():
    root=Path(__file__).resolve().parents[1]
    assert not list((root/'scripts').glob('validate_stage57.ps1.bak_stage57fix_*'))
    text=(root/'scripts/validate_stage58.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in text
    assert 'Print-File' in text and 'Check-NoBackup' in text
    roadmap=(root/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    for x in REQUIRED_ROADMAP: assert x in roadmap
