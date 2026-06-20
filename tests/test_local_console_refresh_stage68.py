from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.local_console.refresh_models import *
from qmt_ai_trading.local_console.refresh_assets import *
from qmt_ai_trading.local_console.refresh_safety import *
from qmt_ai_trading.local_console.refresh_formatters import format_local_console_refresh_report_md
from qmt_ai_trading.local_console.refresh_service import *

def prep(tmp_path, decision='READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW', critical=0):
    b=tmp_path/'local_console_binding_stage66'; p=tmp_path/'local_console_preview_stage67'; b.mkdir(); p.mkdir()
    for n in ['data_bundle.json','binding_manifest.json','data_source_map.json','static_data_safety.json']:(b/n).write_text('{"read_only":true}',encoding='utf-8')
    (p/'local_console_preview_report.json').write_text(json.dumps({'decision':decision,'summary':{'critical_count':critical},'blocking_reasons':[]}),encoding='utf-8')

def test_models_default():
    assert LocalConsoleRefreshConfig().read_only
    assert LocalConsoleRefreshReport().decision==LocalConsoleRefreshDecision.NEED_MORE_EVIDENCE

def test_missing_stage67_no_crash(tmp_path):
    r=run_local_console_refresh_review(LocalConsoleRefreshConfig(repo_root=str(tmp_path)))
    assert r.decision in {LocalConsoleRefreshDecision.NEED_MORE_EVIDENCE, LocalConsoleRefreshDecision.NO_GO}

def test_decisions(tmp_path):
    prep(tmp_path); assert run_local_console_refresh_review(LocalConsoleRefreshConfig(repo_root=str(tmp_path))).decision==LocalConsoleRefreshDecision.READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW
    tmp2=tmp_path/'x'; tmp2.mkdir(); prep(tmp2,'NO_GO',0); assert run_local_console_refresh_review(LocalConsoleRefreshConfig(repo_root=str(tmp2))).decision==LocalConsoleRefreshDecision.NO_GO
    tmp3=tmp_path/'y'; tmp3.mkdir(); prep(tmp3,'READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW',1); assert run_local_console_refresh_review(LocalConsoleRefreshConfig(repo_root=str(tmp3))).decision==LocalConsoleRefreshDecision.NO_GO

def test_assets_routes_and_states():
    html=build_refresh_index_html(); js=build_refresh_app_js(); css=build_refresh_style_css(); routes=[r.hash_route for r in build_navigation_route_map()]
    assert 'Header / Project Title' in html and 'Safety Banner' in html and 'Footer' in html
    for s in ['Dashboard Overview Section','Reports Section','Filters Section','Manifest Section','Validation Section','Scheduler Section','Safety Section','API Section','Next Stage Section','Loading State','Error State','Empty State']: assert s in html
    for r in ['#/dashboard','#/reports','#/filters','#/manifest','#/validation','#/scheduler','#/safety','#/api','#/next']: assert r in routes and r in js
    for r in ['#/order','#/trade','#/approve','#/account','#/positions']: assert r not in routes
    assert 'reloadDataBundle' in js and 'loadDataBundle' in js and 'updateLastLoadedAt' in js and 'Latest updated' in html
    for f in ["fetch('./data_bundle.json')","fetch('./binding_manifest.json')","fetch('./data_source_map.json')","fetch('./static_data_safety.json')"]: assert f in js
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/live')",'XMLHttpRequest','tradeButton','approveButton','orderButton','liveButton']: assert bad not in js and bad not in html
    assert '该路由被安全边界禁止' in js
    assert css
    assert build_refresh_manifest().read_only and build_ui_state_placeholders()

def test_safety_classification():
    assert classify_refresh_marker('xttrader','index.html','不调用 xttrader',False,True)!=LocalConsoleRefreshSeverity.CRITICAL
    assert classify_refresh_marker('xttrader','data_bundle.json','历史安全说明 不调用 xttrader',False,True)!=LocalConsoleRefreshSeverity.CRITICAL
    assert classify_refresh_marker("fetch('/order')",'app.js',"fetch('/order')",True,False)==LocalConsoleRefreshSeverity.CRITICAL
    assert classify_refresh_marker('xtdata','x.py','xtquant.xtdata',True,False)!=LocalConsoleRefreshSeverity.CRITICAL

def test_formatter_contains_safety_note():
    md=format_local_console_refresh_report_md(LocalConsoleRefreshReport(decision=LocalConsoleRefreshDecision.READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW))
    assert '## Safety Note' in md and 'READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW 只表示' in md

def test_cli_and_pipeline(tmp_path):
    prep(tmp_path); out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_local_console_refresh_review.py','--repo-root',str(tmp_path),'--output-dir',str(out)]
    assert subprocess.run(cmd,cwd=Path.cwd()).returncode==0
    for n in ['local_console_refresh_report','navigation_route_map','refresh_manifest','ui_state_placeholders','frontend_safety_report','next_console_grouping_filter_plan']:
        assert (out/f'{n}.md').exists() and (out/f'{n}.json').exists()
    out2=tmp_path/'daily'; assert subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'cache'),'--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-refresh-review','--local-console-refresh-review-output-dir',str(out2)],cwd=Path.cwd()).returncode==0
    out3=tmp_path/'sched'; assert subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--warmup-universe','--warmup-provider','mock','--universe-lookback-days','90','--warmup-frequency','1d','--cache-root',str(tmp_path/'cache2'),'--data-source-mode','cached_real_first','--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-refresh-review','--local-console-refresh-review-output-dir',str(out3)],cwd=Path.cwd()).returncode==0
    cp=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-local-console-refresh-review','--local-console-refresh-review-output-dir','local_console_refresh','--time','15:30'],cwd=Path.cwd(),capture_output=True,text=True)
    assert cp.returncode==0 and 'no_task_registered=True' in cp.stdout and 'enable_local_console_refresh_review=True' in cp.stdout

def test_repo_guards():
    roadmap=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in roadmap and 'Stage61-75 前端 UI 产品化' in roadmap
    for s in ['UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','不能直接访问 QMT','不能自动 approve']: assert s in roadmap
    assert not list(Path('scripts').glob('validate_stage67.ps1.bak_stage67fix_*'))
    v=Path('scripts/validate_stage68.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v and 'Clean-PythonCache' in v and 'Print-File' in v and 'Check-NoBackup' in v
    assert v.find('Clean-PythonCache') < v.rfind('sync_all.ps1 -Mode scan')
