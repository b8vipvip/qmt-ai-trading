from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.pre_gray_final_review.models import *
from qmt_ai_trading.pre_gray_final_review.service import *
from qmt_ai_trading.pre_gray_final_review.safety import *
from qmt_ai_trading.pre_gray_final_review.formatters import format_pre_gray_final_review_report_markdown

def _pkg(tmp_path: Path, s59='READY_FOR_READONLY_SEAL_REVIEW', critical=0, others='READY'):
    dirs={'live_gray_readonly_seal_stage59':'live_gray_readonly_seal.json','live_gray_final_approval_stage58':'live_gray_final_approval.json','live_gray_candidate_stage57':'live_gray_candidate.json','real_cache_quality_stage56':'real_cache_quality.json','qmt_dryrun_calibration_stage55':'qmt_dryrun_calibration.json'}
    decs=[s59, others, others, others, others]
    for (d,f),dec in zip(dirs.items(),decs):
        p=tmp_path/d; p.mkdir(); (p/f).write_text(json.dumps({'decision':dec,'summary':{'critical':critical if d.endswith('stage59') else 0}},ensure_ascii=False),encoding='utf-8')
        (p/f.replace('.json','.md')).write_text('不调用 xttrader dry_run_only no_task_registered',encoding='utf-8')
    seal=tmp_path/'live_gray_readonly_seal_stage59'
    for f in ['material_lock.json','pre_run_checklist.json','final_signoff_recheck.json','next_pre_gray_review_plan.json']:
        (seal/f).write_text('{"ok":true}',encoding='utf-8')
    (seal/'readonly_seal_manifest.json').write_text('{"items":[{"sha256":"abc"}],"dry_run_only":true,"no_task_registered":true}',encoding='utf-8')
    docs=tmp_path/'docs'; docs.mkdir(); (docs/'qmt-ai-trading-project-roadmap.md').write_text('完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）\nStage61：API Gateway 基础层\nStage75：本地控制台封版 / 可选桌面化\nUI 不直接访问 QMT\nUI 不能绕过 Risk Gate\nUI 不能绕过 Human Approval\nUI 不能自动 approve',encoding='utf-8')

def test_defaults():
    assert PreGrayFinalReviewConfig(); assert PreGrayFinalReviewReport()

def test_missing_stage59_no_crash(tmp_path):
    r=run_pre_gray_final_review(build_default_pre_gray_final_review_config(repo_root=tmp_path))
    assert r.decision in (PreGrayFinalReviewDecision.NEED_MORE_EVIDENCE, PreGrayFinalReviewDecision.NO_GO)

def test_stage59_ready_and_need_more_and_no_go(tmp_path):
    _pkg(tmp_path); r=run_pre_gray_final_review(build_default_pre_gray_final_review_config(repo_root=tmp_path))
    assert r.decision==PreGrayFinalReviewDecision.READY_FOR_PRE_GRAY_FINAL_REVIEW
    tmp2=tmp_path/'b'; tmp2.mkdir(); _pkg(tmp2,s59='NEED_MORE_EVIDENCE'); r2=run_pre_gray_final_review(build_default_pre_gray_final_review_config(repo_root=tmp2)); assert r2.decision==PreGrayFinalReviewDecision.NEED_MORE_EVIDENCE
    tmp3=tmp_path/'c'; tmp3.mkdir(); _pkg(tmp3,s59='NO_GO'); r3=run_pre_gray_final_review(build_default_pre_gray_final_review_config(repo_root=tmp3)); assert r3.decision==PreGrayFinalReviewDecision.NO_GO
    tmp4=tmp_path/'d'; tmp4.mkdir(); _pkg(tmp4,critical=1); r4=run_pre_gray_final_review(build_default_pre_gray_final_review_config(repo_root=tmp4)); assert r4.decision==PreGrayFinalReviewDecision.NO_GO

def test_upstream_no_go(tmp_path):
    _pkg(tmp_path, others='NO_GO')
    r=run_pre_gray_final_review(build_default_pre_gray_final_review_config(repo_root=tmp_path))
    assert r.decision==PreGrayFinalReviewDecision.NO_GO

def test_reports_and_formatters_complete(tmp_path):
    _pkg(tmp_path); r=run_pre_gray_final_review(build_default_pre_gray_final_review_config(repo_root=tmp_path))
    assert r.go_no_go_decision==GoNoGoDraftDecision.GO_DRAFT
    md=format_pre_gray_final_review_report_markdown(r)
    for s in ['Safety Note','READY_FOR_PRE_GRAY_FINAL_REVIEW 只表示','GO_DRAFT 不是实盘授权','Stage61 API Gateway Plan']:
        assert s in md
    assert any('UI 直接访问 QMT' in i.name for i in r.stage61_items)
    assert any('Risk Gate' in i.name for i in r.stage61_items)
    assert any('Human Approval' in i.name for i in r.stage61_items)
    assert any('不自动 approve' in i.name for i in r.stage61_items)
    assert len(r.blockers)>=10 and len(r.conditions)>=10

def test_safety_classification():
    assert classify_pre_gray_final_review_marker('xtdata','actual executable','x.py')!=PreGrayFinalReviewSeverity.CRITICAL
    assert classify_pre_gray_final_review_marker('xttrader','actual executable','x.py')==PreGrayFinalReviewSeverity.CRITICAL
    assert classify_pre_gray_final_review_marker('xttrader','不调用 xttrader','stage59/generated.md')==PreGrayFinalReviewSeverity.WARN
    hits=scan_pre_gray_final_review_text_for_forbidden_markers('xttrader XtQuantTrader place_order query_stock_asset','actual executable.py')
    assert any(h['severity']==PreGrayFinalReviewSeverity.CRITICAL for h in hits)
    hits2=scan_pre_gray_final_review_text_for_forbidden_markers('不调用 xttrader','docs/tests/safety marker definitions')
    assert hits2[0]['severity']==PreGrayFinalReviewSeverity.WARN

def test_cli_generates_all(tmp_path):
    _pkg(tmp_path)
    out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_pre_gray_final_review.py','--repo-root',str(tmp_path),'--output-dir',str(out)]
    cp=subprocess.run(cmd,cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True)
    assert cp.returncode==0, cp.stderr+cp.stdout
    for f in ['pre_gray_final_review','material_recheck','go_no_go_draft','no_go_blockers','go_conditions','stage61_api_gateway_plan']:
        assert (out/f'{f}.md').exists(); assert (out/f'{f}.json').exists()

def test_daily_scheduled_register_args(tmp_path):
    out=tmp_path/'pg'
    cp=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--enable-pre-gray-final-review','--pre-gray-final-review-output-dir',str(out)],text=True,capture_output=True)
    assert cp.returncode in (0,1); assert (out/'pre_gray_final_review.md').exists()
    cp2=subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--enable-pre-gray-final-review','--pre-gray-final-review-output-dir',str(out)],text=True,capture_output=True)
    assert cp2.returncode in (0,1)
    cp3=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-pre-gray-final-review','--pre-gray-final-review-output-dir','pre_gray_final_review','--time','15:30'],text=True,capture_output=True)
    assert 'read_only=True' in cp3.stdout and 'no_task_registered=True' in cp3.stdout

def test_repo_guards():
    assert Path('scripts/sync_all.ps1').exists()
    roadmap=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    for s in ['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61-75','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不直接访问 QMT','UI 不能自动 approve']:
        assert s in roadmap
    assert not list(Path('scripts').glob('validate_stage59.ps1.bak_stage59fix_*'))
    v=Path('scripts/validate_stage60.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v
    assert 'Print-File' in v and 'Check-NoBackup' in v
