from pathlib import Path
import json, subprocess, sys
from qmt_ai_trading.local_console.binding_models import *
from qmt_ai_trading.local_console.binding_service import *
from qmt_ai_trading.local_console.binding_reader import *
from qmt_ai_trading.local_console.binding_assets import build_bound_app_js, ROUTES
from qmt_ai_trading.local_console.binding_safety import classify_local_console_binding_marker
from qmt_ai_trading.local_console.binding_formatters import format_binding_report_md

def test_config_and_report_defaults():
    assert LocalConsoleBindingConfig().read_only is True
    assert LocalConsoleBindingReport().summary['dry_run_only'] is True

def test_missing_stage65_needs_more_evidence(tmp_path):
    r=run_local_console_binding_review(LocalConsoleBindingConfig(repo_root=tmp_path))
    assert r.decision in {LocalConsoleBindingDecision.NEED_MORE_EVIDENCE, LocalConsoleBindingDecision.NO_GO}

def _pkg(tmp_path, stage65_decision='READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW', critical=0):
    for d in ['local_console_shell_stage65','local_console_dashboard_stage64','local_console_detail_stage63','local_console_stage62','api_gateway_stage61','validation_logs']:(tmp_path/d).mkdir()
    (tmp_path/'local_console_shell_stage65/local_console_shell_report.json').write_text(json.dumps({'decision':stage65_decision,'summary':{'critical_count':critical},'warnings':[]}),encoding='utf-8')
    for path in ['local_console_dashboard_stage64/local_console_dashboard_report.json','local_console_detail_stage63/local_console_detail_report.json','local_console_stage62/local_console_report.json','api_gateway_stage61/api_gateway_report.json']:
        (tmp_path/path).write_text(json.dumps({'decision':'PASS','summary':{'critical_count':0}}),encoding='utf-8')
    for path in ['local_console_dashboard_stage64/dashboard_card_index.json','local_console_dashboard_stage64/stage_status_cards.json','local_console_dashboard_stage64/warning_blocking_stats.json','local_console_dashboard_stage64/manifest_hash_status.json','local_console_dashboard_stage64/scheduler_preview_status.json','local_console_dashboard_stage64/safety_boundary_status.json','local_console_stage62/report_list.json','local_console_detail_stage63/filter_index.json']:
        (tmp_path/path).write_text('{"ok": true}',encoding='utf-8')
    (tmp_path/'validation_logs/stage65_validation_20260101_000000.log').write_text('ok',encoding='utf-8')

def test_ready_and_nogo_decisions(tmp_path):
    _pkg(tmp_path)
    assert run_local_console_binding_review(LocalConsoleBindingConfig(repo_root=tmp_path)).decision==LocalConsoleBindingDecision.READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW
    tmp2=tmp_path/'nogo'; tmp2.mkdir(); _pkg(tmp2,'NO_GO',1)
    assert run_local_console_binding_review(LocalConsoleBindingConfig(repo_root=tmp2)).decision==LocalConsoleBindingDecision.NO_GO

def test_outputs_bundle_manifest_assets(tmp_path):
    _pkg(tmp_path); out=tmp_path/'out'
    r=run_local_console_binding_review(LocalConsoleBindingConfig(repo_root=tmp_path,output_dir=out))
    save_local_console_binding_report(r,out/'local_console_binding_report.md',out/'local_console_binding_report.json')
    save_data_bundle_report(build_data_bundle_report(r),out/'data_bundle.md',out/'data_bundle.json')
    save_binding_manifest_report(build_binding_manifest_report(r),out/'binding_manifest.md',out/'binding_manifest.json')
    save_data_source_map_report(build_data_source_map_report(r),out/'data_source_map.md',out/'data_source_map.json')
    save_missing_data_placeholder_report(build_missing_data_placeholder_report(r),out/'missing_data_placeholders.md',out/'missing_data_placeholders.json')
    save_bound_asset_index_report(build_bound_asset_index_report(r),out/'bound_asset_index.md',out/'bound_asset_index.json')
    save_static_data_safety_report(build_static_data_safety_report(),out/'static_data_safety.md',out/'static_data_safety.json')
    save_next_console_preview_server_plan_report(build_next_console_preview_server_plan_report(),out/'next_console_preview_server_plan.md',out/'next_console_preview_server_plan.json')
    for name in ['data_bundle.json','binding_manifest.json','data_source_map.json','missing_data_placeholders.json','bound_asset_index.json','static_data_safety.json','index.html','app.js','style.css','next_console_preview_server_plan.json']:
        assert (out/name).exists()
    b=json.loads((out/'data_bundle.json').read_text())
    assert b['metadata']['read_only'] and b['metadata']['dry_run_only'] and b['metadata']['no_trade_authorization']
    for k in ['dashboard','report_list','detail_filters','api_capability','scheduler_preview','safety_boundary']: assert k in b
    sm=json.loads((out/'data_source_map.json').read_text())
    assert 'local_console_dashboard_stage64/dashboard_card_index.json' in sm
    assert 'local_console_stage62/report_list.json' in sm
    assert 'local_console_detail_stage63/filter_index.json' in sm
    assert 'api_gateway_stage61/api_gateway_report.json' in sm

def test_app_js_and_routes_safe():
    js=build_bound_app_js()
    assert "fetch('./data_bundle.json')" in js or 'fetch(source)' in js
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/live')",'XMLHttpRequest']:
        assert bad not in js
    for bad in ['#/order','#/trade','#/approve','#/account','#/positions']: assert bad not in ROUTES

def test_reader_markdown_fallback_and_encoding(tmp_path):
    j=tmp_path/'bad.json'; m=tmp_path/'x.md'; j.write_text('{bad',encoding='utf-8'); m.write_bytes('摘要正常'.encode('utf-16le'))
    r=read_json_or_markdown_tolerant(j,m)
    assert r['fallback_used'] is True and '\x00' not in r['summary'] and not r['summary'].startswith('\ufeff')
    bad=clean_mojibake_for_display('�'*30)
    assert 'encoding_warning=True' in bad

def test_marker_classification_and_formatter():
    assert classify_local_console_binding_marker('xttrader','local_console_shell_stage65/index.html',generated=True) in {'WARN','INFO'}
    assert classify_local_console_binding_marker('xttrader','qmt_ai_trading/x.py',executable=True)=='CRITICAL'
    assert classify_local_console_binding_marker('place_order','qmt_ai_trading/x.py',executable=True)=='CRITICAL'
    md=format_binding_report_md(LocalConsoleBindingReport(decision=LocalConsoleBindingDecision.READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW))
    assert 'Safety Note' in md and '不是实盘授权' in md

def test_cli_generates(tmp_path):
    _pkg(tmp_path); out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_local_console_binding_review.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'local_console_binding_report.md'),'--json-output',str(out/'local_console_binding_report.json'),'--bundle-output',str(out/'data_bundle.md'),'--bundle-json-output',str(out/'data_bundle.json'),'--manifest-output',str(out/'binding_manifest.md'),'--manifest-json-output',str(out/'binding_manifest.json'),'--source-map-output',str(out/'data_source_map.md'),'--source-map-json-output',str(out/'data_source_map.json'),'--missing-output',str(out/'missing_data_placeholders.md'),'--missing-json-output',str(out/'missing_data_placeholders.json'),'--asset-output',str(out/'bound_asset_index.md'),'--asset-json-output',str(out/'bound_asset_index.json'),'--safety-output',str(out/'static_data_safety.md'),'--safety-json-output',str(out/'static_data_safety.json'),'--plan-output',str(out/'next_console_preview_server_plan.md'),'--plan-json-output',str(out/'next_console_preview_server_plan.json')]
    assert subprocess.run(cmd,cwd=Path.cwd()).returncode==0
    assert (out/'local_console_binding_report.md').exists() and (out/'next_console_preview_server_plan.json').exists()

def test_validate_and_docs_rules():
    v=Path('scripts/validate_stage66.ps1').read_text(encoding='utf-8') if Path('scripts/validate_stage66.ps1').exists() else ''
    assert 'Clean-PythonCache' in v and 'Print-File' in v and 'Check-NoBackup' in v
    assert 'powershell -NoProfile -Command' not in v
    assert '\\`' not in v
    road=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in road
    assert 'Stage61-75' in road and '不能绕过 Risk Gate / Human Approval' in road
    assert not list(Path('scripts').glob('validate_stage65.ps1.bak_stage65fix_*'))
    assert Path('scripts/sync_all.ps1').exists()
