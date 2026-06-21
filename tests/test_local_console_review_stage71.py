from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.local_console.review_models import *
from qmt_ai_trading.local_console.review_assets import *
from qmt_ai_trading.local_console.review_safety import *
from qmt_ai_trading.local_console.review_formatters import format_local_console_review_workbench_report_md
from qmt_ai_trading.local_console.review_service import build_default_local_console_review_config, run_local_console_review_workbench_review


def test_models_default_constructible():
    assert LocalConsoleReviewConfig().read_only is True
    assert LocalConsoleReviewWorkbenchReport().summary['no_trade_authorization'] is True

def test_missing_stage70_needs_more_evidence(tmp_path):
    r=run_local_console_review_workbench_review(LocalConsoleReviewConfig(repo_root=str(tmp_path)))
    assert r.decision in {LocalConsoleReviewDecision.NEED_MORE_EVIDENCE, LocalConsoleReviewDecision.NO_GO}

def test_stage70_ready_allows_stage71_ready(tmp_path):
    d=tmp_path/'local_console_drilldown_stage70'; d.mkdir()
    (d/'local_console_drilldown_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW','summary':{'critical_count':0}}),encoding='utf-8')
    r=run_local_console_review_workbench_review(LocalConsoleReviewConfig(repo_root=str(tmp_path)))
    assert r.decision == LocalConsoleReviewDecision.READY_FOR_LOCAL_CONSOLE_REVIEW_WORKBENCH_REVIEW

def test_stage70_nogo_or_critical_blocks(tmp_path):
    d=tmp_path/'local_console_drilldown_stage70'; d.mkdir()
    (d/'local_console_drilldown_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':0}}),encoding='utf-8')
    assert run_local_console_review_workbench_review(LocalConsoleReviewConfig(repo_root=str(tmp_path))).decision == LocalConsoleReviewDecision.NO_GO
    (d/'local_console_drilldown_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW','summary':{'critical_count':1}}),encoding='utf-8')
    assert run_local_console_review_workbench_review(LocalConsoleReviewConfig(repo_root=str(tmp_path))).decision == LocalConsoleReviewDecision.NO_GO

def test_assets_routes_and_forbidden_absent():
    html=build_review_index_html(); js=build_review_app_js(); css=build_review_style_css()
    assert 'Manual Review Workbench Panel' in html and 'Review Checklist Panel' in html and css
    for fn in ['loadDataBundle()','loadReviewManifest()','loadReviewChecklist()','renderReviewWorkbench()','renderReviewChecklist()','renderReviewNotesTemplate()','renderLocalConfirmationChecklist()','renderReviewPackageIndex()','renderReviewStatusPlaceholder()','renderReviewConclusionDraft()','toggleChecklistItemLocalOnly()','copyReviewNotesTemplateReadOnly()','exportReviewNotesDraftReadOnly()','renderForbiddenRouteState()','renderCurrentRoute()','updateLastLoadedAt()']:
        assert fn in js
    routes=build_review_manifest().routes
    for r in ['#/review-workbench','#/review-checklist','#/review-notes','#/review-package','#/local-confirmations']:
        assert r in routes
    for r in ['#/order','#/trade','#/approve','#/approval','#/auto-approve','#/account','#/positions']:
        assert r not in routes
    for source in ['./review_manifest.json','./review_checklist.json','./review_notes_template.json','./local_confirmation_checklist.json','./review_package_index.json','./data_bundle.json','./static_data_safety.json']:
        assert source in js
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/live')",'XMLHttpRequest']:
        assert bad not in js
    for bad in ['tradeButton','approveButton','orderButton','liveButton','autoApproveButton']:
        assert bad not in html

def test_assets_reports_semantics():
    assert '不是审批授权' in build_review_notes_template().body
    assert '不是交易授权' in build_local_confirmation_checklist()[0].note
    assert all(i.read_only for i in build_review_package_index())
    js=build_review_app_js()
    assert 'localChecklistState' in js and 'no_approval_write:true' in js

def test_safety_classification():
    assert classify_review_marker('xttrader','index.html','Safety Banner：不调用 xttrader') != LocalConsoleReviewSeverity.CRITICAL
    assert classify_review_marker('xttrader','review_notes_template.md','不是审批授权，不调用 xttrader',generated=True) != LocalConsoleReviewSeverity.CRITICAL
    assert classify_review_marker("fetch('/trade')",'app.js',"fetch('/trade')") == LocalConsoleReviewSeverity.CRITICAL
    assert classify_review_marker('xtdata','x.py','xtquant.xtdata') != LocalConsoleReviewSeverity.CRITICAL
    assert_review_notes_are_not_approval({'note':'不是审批授权'})
    assert_checklist_is_not_trade_authorization({'note':'不是交易授权'})

def test_formatter_safety_note():
    md=format_local_console_review_workbench_report_md(LocalConsoleReviewWorkbenchReport(decision=LocalConsoleReviewDecision.READY_FOR_LOCAL_CONSOLE_REVIEW_WORKBENCH_REVIEW))
    assert '## Safety Note' in md
    assert 'READY_FOR_LOCAL_CONSOLE_REVIEW_WORKBENCH_REVIEW 只表示' in md

def test_cli_generates_all_outputs(tmp_path):
    out=tmp_path/'pkg'; root=Path(__file__).resolve().parents[1]
    cmd=[sys.executable,'scripts/run_local_console_review_workbench.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'local_console_review_workbench_report.md'),'--json-output',str(out/'local_console_review_workbench_report.json'),'--manifest-output',str(out/'review_manifest.md'),'--manifest-json-output',str(out/'review_manifest.json'),'--checklist-output',str(out/'review_checklist.md'),'--checklist-json-output',str(out/'review_checklist.json'),'--notes-output',str(out/'review_notes_template.md'),'--notes-json-output',str(out/'review_notes_template.json'),'--confirmation-output',str(out/'local_confirmation_checklist.md'),'--confirmation-json-output',str(out/'local_confirmation_checklist.json'),'--package-output',str(out/'review_package_index.md'),'--package-json-output',str(out/'review_package_index.json'),'--safety-output',str(out/'review_safety_report.md'),'--safety-json-output',str(out/'review_safety_report.json'),'--plan-output',str(out/'next_ui_acceptance_summary_plan.md'),'--plan-json-output',str(out/'next_ui_acceptance_summary_plan.json')]
    res=subprocess.run(cmd,cwd=root,text=True,capture_output=True)
    assert res.returncode == 0, res.stderr + res.stdout
    for name in ['local_console_review_workbench_report.md','local_console_review_workbench_report.json','review_manifest.md','review_manifest.json','review_checklist.md','review_checklist.json','review_notes_template.md','review_notes_template.json','local_confirmation_checklist.md','local_confirmation_checklist.json','review_package_index.md','review_package_index.json','review_safety_report.md','review_safety_report.json','next_ui_acceptance_summary_plan.md','next_ui_acceptance_summary_plan.json','index.html','app.js','style.css']:
        assert (out/name).exists(), name

def test_daily_scheduled_register_flags(tmp_path):
    root=Path(__file__).resolve().parents[1]
    out=tmp_path/'review'
    res=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'market'),'--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-review-workbench','--local-console-review-workbench-output-dir',str(out)],cwd=root,text=True,capture_output=True)
    assert res.returncode == 0, res.stderr + res.stdout
    assert (out/'local_console_review_workbench_report.md').exists()
    out2=tmp_path/'sch'
    res=subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--warmup-universe','--warmup-provider','mock','--universe-lookback-days','90','--warmup-frequency','1d','--cache-root',str(tmp_path/'market2'),'--data-source-mode','cached_real_first','--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-review-workbench','--local-console-review-workbench-output-dir',str(out2)],cwd=root,text=True,capture_output=True)
    assert res.returncode == 0, res.stderr + res.stdout
    assert (out2/'local_console_review_workbench_report.md').exists()
    res=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-local-console-review-workbench','--local-console-review-workbench-output-dir','local_console_review','--time','15:30'],cwd=root,text=True,capture_output=True)
    assert res.returncode == 0
    assert 'no_task_registered=True' in res.stdout and 'enable_local_console_review_workbench=True' in res.stdout

def test_repo_policy_files():
    root=Path(__file__).resolve().parents[1]
    assert not list((root/'scripts').glob('validate_stage70.ps1.bak_stage70fix_*'))
    assert not list((root/'scripts').glob('validate_stage71.ps1.bak_stage71fix_*'))
    roadmap=(root/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线' in roadmap and 'Stage61-75' in roadmap
    assert 'Risk Gate' in roadmap and 'Human Approval' in roadmap and '不能直接访问 QMT' in roadmap and '不能自动 approve' in roadmap
    validate=(root/'scripts/validate_stage71.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in validate
    assert 'Clean-PythonCache' in validate and validate.index('Clean-PythonCache') < validate.rindex('sync_all.ps1')
    assert '\\`' not in validate
    gi=(root/'.gitignore').read_text(encoding='utf-8')
    assert 'validation_logs/' in gi and 'local_console_review_stage71/' in gi and '__pycache__/' in gi
