from pathlib import Path
import json, subprocess, sys
from qmt_ai_trading.local_console.preview_models import *
from qmt_ai_trading.local_console.preview_service import *
from qmt_ai_trading.local_console.preview_safety import *
from qmt_ai_trading.local_console.preview_formatters import format_preview_report_md
from qmt_ai_trading.local_console.preview_routes import FORBIDDEN_ROUTES

def _stage66(tmp_path, decision='READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW', critical=0):
    d=tmp_path/'local_console_binding_stage66'; d.mkdir()
    (d/'local_console_binding_report.json').write_text(json.dumps({'decision':decision,'summary':{'critical_count':critical},'warnings':[]}),encoding='utf-8')
    (d/'index.html').write_text('<div>安全提示：不调用 xttrader</div>',encoding='utf-8')
    (d/'app.js').write_text("fetch('./data_bundle.json')",encoding='utf-8')
    (d/'style.css').write_text('body{}',encoding='utf-8')
    for n in ['data_bundle.json','binding_manifest.json','data_source_map.json','static_data_safety.json']:(d/n).write_text('{"read_only":true}',encoding='utf-8')
    return d

def test_defaults_and_missing_stage66(tmp_path):
    assert LocalConsolePreviewConfig().host=='127.0.0.1' and LocalConsolePreviewConfig().port==8767
    assert PreviewServerReport().summary['read_only'] is True
    r=run_local_console_preview_review(LocalConsolePreviewConfig(repo_root=str(tmp_path)))
    assert r.decision in {LocalConsolePreviewDecision.NEED_MORE_EVIDENCE, LocalConsolePreviewDecision.NO_GO}

def test_ready_and_stage66_nogo(tmp_path):
    _stage66(tmp_path)
    r=run_local_console_preview_review(LocalConsolePreviewConfig(repo_root=str(tmp_path)))
    assert r.decision==LocalConsolePreviewDecision.READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW
    tmp2=tmp_path/'x'; tmp2.mkdir(); _stage66(tmp2,'NO_GO',1)
    assert run_local_console_preview_review(LocalConsolePreviewConfig(repo_root=str(tmp2))).decision==LocalConsolePreviewDecision.NO_GO

def test_host_routes_methods_and_reports(tmp_path):
    _stage66(tmp_path)
    r=run_local_console_preview_review(LocalConsolePreviewConfig(repo_root=str(tmp_path)))
    assert run_local_console_preview_review(LocalConsolePreviewConfig(repo_root=str(tmp_path),host='0.0.0.0')).decision==LocalConsolePreviewDecision.NO_GO
    assert assert_no_public_bind('0.0.0.0') is False and assert_no_public_bind('192.168.1.2') is False
    paths={x.path for x in r.routes}
    for p in ['/','/index.html','/app.js','/style.css','/data_bundle.json','/binding_manifest.json','/data_source_map.json','/health']: assert p in paths
    assert set(assert_no_forbidden_preview_methods(['POST','PUT','PATCH','DELETE']))=={'POST','PUT','PATCH','DELETE'}
    for p in ['/order','/trade','/approve','/account','/positions','/assets']: assert classify_preview_route(p)['severity']=='CRITICAL'
    assert build_preview_route_map_report(r).routes and build_static_file_index_report(r).files and build_response_manifest_report(r).responses and build_preview_safety_report(r).boundary

def test_cli_and_server(tmp_path):
    _stage66(tmp_path); out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_local_console_preview_review.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--dry-run']
    assert subprocess.run(cmd,cwd=Path.cwd()).returncode==0
    for n in ['local_console_preview_report.json','preview_route_map.json','static_file_index.json','response_manifest.json','preview_safety_boundary.json','next_console_refresh_plan.json']: assert (out/n).exists()
    assert subprocess.run([sys.executable,'scripts/run_local_console_preview_server.py','--repo-root',str(tmp_path),'--host','127.0.0.1','--port','8767','--dry-run'],cwd=Path.cwd()).returncode==0
    assert subprocess.run([sys.executable,'scripts/run_local_console_preview_server.py','--repo-root',str(tmp_path),'--host','127.0.0.1','--port','8767','--serve-once','--timeout-seconds','1'],cwd=Path.cwd()).returncode==0

def test_marker_classification_and_formatter():
    assert classify_preview_marker('xttrader','index.html',generated=True) in {'WARN','INFO'}
    assert classify_preview_marker('xttrader','qmt_ai_trading/local_console/preview_server.py',executable=True)=='CRITICAL'
    assert classify_preview_marker('XtQuantTrader','app.py',executable=True)=='CRITICAL'
    assert classify_preview_marker('xtdata','x.py',executable=True)=='INFO'
    assert classify_preview_marker('xttrader','local_console_binding_stage66/index.html',generated=True) in {'WARN','INFO'}
    assert classify_preview_marker('place_order','docs/safety_marker_definitions.md',generated=True)=='WARN'
    md=format_preview_report_md(PreviewServerReport(decision=LocalConsolePreviewDecision.READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW))
    assert 'Safety Note' in md and '不是实盘授权' in md

def test_app_js_safe_daily_scheduled_register_and_docs(tmp_path):
    _stage66(tmp_path)
    js=(tmp_path/'local_console_binding_stage66/app.js').read_text()
    for bad in ["fetch('/order')","fetch('/trade')",'XMLHttpRequest']: assert bad not in js
    out=tmp_path/'daily'
    assert subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'cache'),'--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-preview-review','--local-console-preview-review-output-dir',str(out)],cwd=Path.cwd()).returncode==0
    assert (out/'local_console_preview_report.json').exists()
    so=tmp_path/'sched'
    assert subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--warmup-universe','--warmup-provider','mock','--universe-lookback-days','90','--warmup-frequency','1d','--cache-root',str(tmp_path/'cache2'),'--data-source-mode','cached_real_first','--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-preview-review','--local-console-preview-review-output-dir',str(so)],cwd=Path.cwd()).returncode==0
    cp=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-local-console-preview-review','--local-console-preview-review-output-dir','local_console_preview','--time','15:30'],cwd=Path.cwd(),capture_output=True,text=True)
    assert cp.returncode==0 and 'no_task_registered=True' in cp.stdout
    assert 'validation_logs/' in Path('.gitignore').read_text()
    assert not list(Path('scripts').glob('validate_stage66.ps1.bak_stage66fix_*'))
    v=Path('scripts/validate_stage67.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v and '\\`' not in v and 'Clean-PythonCache' in v
    assert v.rfind('Clean-PythonCache') < v.rfind('sync_all.ps1 -Mode scan')
    road=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in road and 'Stage61-75' in road
    assert '不能绕过 Risk Gate' in road and '不能绕过 Human Approval' in road and '不能直接访问 QMT' in road and '不能自动 approve' in road
    assert Path('scripts/sync_all.ps1').exists()
