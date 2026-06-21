from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.local_console.grouping_models import *
from qmt_ai_trading.local_console.grouping_assets import *
from qmt_ai_trading.local_console.grouping_safety import *
from qmt_ai_trading.local_console.grouping_formatters import format_local_console_grouping_report_md
from qmt_ai_trading.local_console.grouping_service import *

def prep(tmp_path, decision='READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW', critical=0):
    b=tmp_path/'local_console_binding_stage66'; r=tmp_path/'local_console_refresh_stage68'; p=tmp_path/'local_console_preview_stage67'; b.mkdir(); r.mkdir(); p.mkdir()
    for n in ['data_bundle.json','binding_manifest.json','data_source_map.json','static_data_safety.json']:(b/n).write_text('{"read_only":true}',encoding='utf-8')
    (r/'local_console_refresh_report.json').write_text(json.dumps({'decision':decision,'summary':{'critical_count':critical},'blocking_reasons':[]}),encoding='utf-8')

def test_models_default():
    assert LocalConsoleGroupingConfig().read_only
    assert LocalConsoleGroupingReport().decision==LocalConsoleGroupingDecision.NEED_MORE_EVIDENCE

def test_decisions(tmp_path):
    assert run_local_console_grouping_review(LocalConsoleGroupingConfig(repo_root=str(tmp_path))).decision in {LocalConsoleGroupingDecision.NEED_MORE_EVIDENCE, LocalConsoleGroupingDecision.NO_GO}
    prep(tmp_path); assert run_local_console_grouping_review(LocalConsoleGroupingConfig(repo_root=str(tmp_path))).decision==LocalConsoleGroupingDecision.READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW
    x=tmp_path/'x'; x.mkdir(); prep(x,'NO_GO',0); assert run_local_console_grouping_review(LocalConsoleGroupingConfig(repo_root=str(x))).decision==LocalConsoleGroupingDecision.NO_GO
    y=tmp_path/'y'; y.mkdir(); prep(y,'READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW',1); assert run_local_console_grouping_review(LocalConsoleGroupingConfig(repo_root=str(y))).decision==LocalConsoleGroupingDecision.NO_GO

def test_assets_routes_filters_and_safety():
    html=build_grouping_index_html(); js=build_grouping_app_js(); css=build_grouping_style_css(); manifest=build_grouping_manifest(); schema=build_filter_state_schema(); cards=build_grouped_card_index(); search=build_search_index(); safety=build_frontend_grouping_safety_report({'index.html':html,'app.js':js})
    for s in ['Header / Project Title','Safety Banner','Navigation Tabs','Filter Bar','Search Input','Status Filter','Severity Filter','Stage Filter','Warning Filter','Blocking Reason Filter','Clear Filters Button','Grouped Dashboard Cards Section','Grouped Reports Section','Grouped Warnings Section','Grouped Blocking Reasons Section','Loading State','Error State','Empty State','Footer']: assert s in html
    for fn in ['loadDataBundle','reloadDataBundle','buildGroupingState','applyFilters','clearFilters','searchReadOnly','groupByStatus','groupBySeverity','groupByStage','filterWarnings','filterBlockingReasons','renderGroupBadges','toggleCardCollapse','renderEmptyState','renderForbiddenRouteState','renderCurrentRoute','updateLastLoadedAt']: assert fn in js
    for r in ['#/dashboard','#/reports','#/filters','#/warnings','#/blocking-reasons','#/manifest','#/validation','#/scheduler','#/safety','#/api','#/next']: assert r in manifest.routes and r in js
    for r in ['#/order','#/trade','#/approve','#/account','#/positions']: assert r not in manifest.routes
    for x in ['status','severity','stage','warnings','blocking_reasons','search']: assert hasattr(schema,x)
    for x in ['PASS','WARN','FAIL','SKIPPED','UNAVAILABLE']: assert x in cards.status_groups
    for x in ['INFO','WARN','CRITICAL']: assert x in cards.severity_groups
    for f in ["fetch('./data_bundle.json')","fetch('./binding_manifest.json')","fetch('./data_source_map.json')","fetch('./static_data_safety.json')"]: assert f in js
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/live')",'XMLHttpRequest','tradeButton','approveButton','orderButton','liveButton']: assert bad not in js and bad not in html
    assert '该路由被安全边界禁止' in js and 'empty state' in js and 'badge' in js and css and search and safety.critical_count==0

def test_safety_classification_and_formatter():
    assert classify_grouping_marker('xttrader','index.html','不调用 xttrader',False,True)!=LocalConsoleGroupingSeverity.CRITICAL
    assert classify_grouping_marker('xttrader','data_bundle.json','历史安全说明 不调用 xttrader',False,True)!=LocalConsoleGroupingSeverity.CRITICAL
    assert classify_grouping_marker("fetch('/order')",'app.js',"fetch('/order')",True,False)==LocalConsoleGroupingSeverity.CRITICAL
    assert classify_grouping_marker('xtdata','x.py','xtquant.xtdata',True,False)!=LocalConsoleGroupingSeverity.CRITICAL
    md=format_local_console_grouping_report_md(LocalConsoleGroupingReport(decision=LocalConsoleGroupingDecision.READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW))
    assert '## Safety Note' in md and 'READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW 只表示' in md

def test_cli_and_pipeline(tmp_path):
    prep(tmp_path); out=tmp_path/'out'
    assert subprocess.run([sys.executable,'scripts/run_local_console_grouping_review.py','--repo-root',str(tmp_path),'--output-dir',str(out)],cwd=Path.cwd()).returncode==0
    for n in ['local_console_grouping_report','grouping_manifest','filter_state_schema','grouped_card_index','search_index','frontend_grouping_safety_report','next_console_drilldown_export_plan']: assert (out/f'{n}.md').exists() and (out/f'{n}.json').exists()
    out2=tmp_path/'daily'; assert subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'cache'),'--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-grouping-review','--local-console-grouping-review-output-dir',str(out2)],cwd=Path.cwd()).returncode==0
    out3=tmp_path/'sched'; assert subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--warmup-universe','--warmup-provider','mock','--universe-lookback-days','90','--warmup-frequency','1d','--cache-root',str(tmp_path/'cache2'),'--data-source-mode','cached_real_first','--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-grouping-review','--local-console-grouping-review-output-dir',str(out3)],cwd=Path.cwd()).returncode==0
    cp=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-local-console-grouping-review','--local-console-grouping-review-output-dir','local_console_grouping','--time','15:30'],cwd=Path.cwd(),capture_output=True,text=True)
    assert cp.returncode==0 and 'no_task_registered=True' in cp.stdout and 'enable_local_console_grouping_review=True' in cp.stdout

def test_repo_guards():
    roadmap=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in roadmap and 'Stage61-75 前端 UI 产品化' in roadmap
    for s in ['UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','不能直接访问 QMT','不能自动 approve']: assert s in roadmap
    assert not list(Path('scripts').glob('validate_stage68.ps1.bak_stage68fix_*'))
    v=Path('scripts/validate_stage69.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v and 'Clean-PythonCache' in v and 'Print-File' in v and 'Check-NoBackup' in v and '\\`' not in v
    assert v.find('Clean-PythonCache') < v.rfind('sync_all.ps1 -Mode scan')
