from pathlib import Path
import json, subprocess, sys
from qmt_ai_trading.local_console.shell_models import *
from qmt_ai_trading.local_console.shell_assets import *
from qmt_ai_trading.local_console.shell_service import *
from qmt_ai_trading.local_console.tolerant_reader import safe_read_json_or_markdown, summarize_for_shell
from qmt_ai_trading.local_console.shell_safety import scan_local_console_shell_asset_for_forbidden_markers, classify_local_console_shell_marker
from qmt_ai_trading.local_console.shell_formatters import format_shell_report_md

def test_config_and_report_defaults():
    assert LocalConsoleShellConfig().read_only is True
    assert LocalConsoleShellReport().decision == LocalConsoleShellDecision.NEED_MORE_EVIDENCE

def test_missing_stage64_does_not_crash(tmp_path):
    r=run_local_console_shell_review(LocalConsoleShellConfig(repo_root=tmp_path))
    assert r.decision in {LocalConsoleShellDecision.NEED_MORE_EVIDENCE, LocalConsoleShellDecision.NO_GO}

def test_stage64_ready_allows_ready(tmp_path):
    d=tmp_path/'local_console_dashboard_stage64'; d.mkdir()
    (d/'local_console_dashboard_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW','summary':{'critical_count':0},'warnings':[]}),encoding='utf-8')
    r=run_local_console_shell_review(LocalConsoleShellConfig(repo_root=tmp_path))
    assert r.decision == LocalConsoleShellDecision.READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW

def test_stage64_nogo_blocks(tmp_path):
    d=tmp_path/'local_console_dashboard_stage64'; d.mkdir()
    (d/'local_console_dashboard_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':1}}),encoding='utf-8')
    assert run_local_console_shell_review(LocalConsoleShellConfig(repo_root=tmp_path)).decision == LocalConsoleShellDecision.NO_GO

def test_assets_and_routes_safe():
    html=build_index_html(); js=build_app_js(); css=build_style_css()
    assert 'Safety Banner' in html and 'Dashboard Overview Section' in html and 'Report List Section' in html and 'Detail / Filter Section' in html
    assert 'tradeButton' not in html and 'approveButton' not in html
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/live')",'XMLHttpRequest']:
        assert bad not in js
    assert css and 'fetch' not in css
    routes=[r.path for r in build_shell_route_map()]
    for good in ['#/dashboard','#/reports','#/filters','#/manifest','#/validation','#/safety']:
        assert good in routes
    for bad in ['#/order','#/trade','#/approve','#/account','#/positions']:
        assert bad not in routes
    assert build_shell_manifest([]).read_only is True
    assert build_data_binding_placeholders()
    assert build_static_safety_boundary().dry_run_only is True

def test_tolerant_reader_fallback_and_clean(tmp_path):
    jp=tmp_path/'bad.json'; mp=tmp_path/'bad.md'
    jp.write_text('{bad json',encoding='utf-8'); mp.write_text('\ufeffhello\x00 world',encoding='utf-8')
    r=safe_read_json_or_markdown(jp,mp)
    assert r['status']=='WARN' and 'json read failed' in ' '.join(r['warnings'])
    assert '\x00' not in r['summary'] and not r['summary'].startswith('\ufeff')
    assert '\x00' not in summarize_for_shell('a\x00b')

def test_safety_marker_classification():
    hits=scan_local_console_shell_asset_for_forbidden_markers('不调用 xttrader','stage64/generated.md',generated=True)
    assert hits and hits[0]['severity']=='WARN'
    assert classify_local_console_shell_marker('xttrader','qmt_ai_trading/local_console/live.py',executable=True)=='CRITICAL'
    assert classify_local_console_shell_marker('XtQuantTrader','qmt_ai_trading/local_console/live.py',executable=True)=='CRITICAL'
    assert classify_local_console_shell_marker('place_order','qmt_ai_trading/local_console/live.py',executable=True)=='CRITICAL'
    assert classify_local_console_shell_marker('query_stock_asset','qmt_ai_trading/local_console/live.py',executable=True)=='CRITICAL'
    assert classify_local_console_shell_marker('xtdata')=='INFO'

def test_formatter_safety_note():
    txt=format_shell_report_md(LocalConsoleShellReport(decision=LocalConsoleShellDecision.READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW))
    assert 'Safety Note' in txt and '不是实盘授权' in txt

def test_cli_outputs(tmp_path):
    d=tmp_path/'local_console_dashboard_stage64'; d.mkdir()
    (d/'local_console_dashboard_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW','summary':{'critical_count':0}}),encoding='utf-8')
    out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_local_console_shell_review.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--local-console-dashboard-dir','local_console_dashboard_stage64','--output',str(out/'local_console_shell_report.md'),'--json-output',str(out/'local_console_shell_report.json'),'--manifest-output',str(out/'shell_manifest.md'),'--manifest-json-output',str(out/'shell_manifest.json'),'--route-output',str(out/'route_map.md'),'--route-json-output',str(out/'route_map.json'),'--asset-output',str(out/'asset_index.md'),'--asset-json-output',str(out/'asset_index.json'),'--binding-output',str(out/'data_binding_placeholders.md'),'--binding-json-output',str(out/'data_binding_placeholders.json'),'--safety-output',str(out/'static_safety_boundary.md'),'--safety-json-output',str(out/'static_safety_boundary.json'),'--plan-output',str(out/'next_console_data_binding_plan.md'),'--plan-json-output',str(out/'next_console_data_binding_plan.json')]
    assert subprocess.run(cmd,cwd=Path.cwd()).returncode==0
    for f in ['local_console_shell_report.md','local_console_shell_report.json','shell_manifest.md','shell_manifest.json','route_map.md','route_map.json','asset_index.md','asset_index.json','data_binding_placeholders.md','data_binding_placeholders.json','static_safety_boundary.md','static_safety_boundary.json','next_console_data_binding_plan.md','next_console_data_binding_plan.json','index.html','app.js','style.css']:
        assert (out/f).exists()

def test_roadmap_and_gitignore_and_sync_unchanged():
    road=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in road
    assert 'Stage61-75 前端 UI 产品化计划' in road
    assert 'UI 不能绕过 Risk Gate' in road and 'UI 不能绕过 Human Approval' in road and 'UI 不能自动 approve' in road
    gi=Path('.gitignore').read_text(encoding='utf-8')
    assert 'validation_logs/' in gi and 'local_console_shell_stage65/' in gi
