from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.local_console.demo_models import *
from qmt_ai_trading.local_console.demo_assets import *
from qmt_ai_trading.local_console.demo_safety import *
from qmt_ai_trading.local_console.demo_formatters import format_local_console_demo_package_report_md
from qmt_ai_trading.local_console.demo_service import build_default_local_console_demo_config, run_local_console_demo_package_review

def test_models_defaults():
    assert LocalConsoleDemoConfig().read_only is True
    assert LocalConsoleDemoPackageReport().decision == LocalConsoleDemoDecision.NEED_MORE_EVIDENCE

def test_missing_stage73_needs_evidence(tmp_path):
    r=run_local_console_demo_package_review(build_default_local_console_demo_config(repo_root=str(tmp_path)))
    assert r.decision in {LocalConsoleDemoDecision.NEED_MORE_EVIDENCE, LocalConsoleDemoDecision.NO_GO}

def test_stage73_ready_allows_ready(tmp_path):
    d=tmp_path/'local_console_help_stage73'; d.mkdir()
    (d/'local_console_help_docs_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW','summary':{'critical_count':0}},ensure_ascii=False),encoding='utf-8')
    r=run_local_console_demo_package_review(build_default_local_console_demo_config(repo_root=str(tmp_path)))
    assert r.decision == LocalConsoleDemoDecision.READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW

def test_stage73_no_go_blocks(tmp_path):
    d=tmp_path/'local_console_help_stage73'; d.mkdir()
    (d/'local_console_help_docs_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':0}},ensure_ascii=False),encoding='utf-8')
    assert run_local_console_demo_package_review(build_default_local_console_demo_config(repo_root=str(tmp_path))).decision == LocalConsoleDemoDecision.NO_GO
    (d/'local_console_help_docs_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW','summary':{'critical_count':1}},ensure_ascii=False),encoding='utf-8')
    assert run_local_console_demo_package_review(build_default_local_console_demo_config(repo_root=str(tmp_path))).decision == LocalConsoleDemoDecision.NO_GO

def test_assets_routes_and_frontend_are_readonly():
    html=build_demo_index_html(); js=build_demo_app_js(); css=build_demo_style_css()
    assert 'Header / Project Title' in html and 'Safety Banner' in html and 'Footer' in html and css
    for name in ['loadDemoManifest','loadDemoGuide','loadDemoRouteMap','loadDemoAssetManifest','loadDemoPackageIndex','loadDemoSafetyReport','loadDemoValidationSummary','renderDemoHome','renderDemoGuide','renderDemoRouteMap','renderDemoAssetManifest','renderDemoPackageIndex','renderDemoSafetyReport','renderDemoValidationSummary','searchDemoReadOnly','copyDemoSectionReadOnly','renderForbiddenRouteState','renderCurrentRoute','updateLastLoadedAt']:
        assert f'function {name}' in js or f'async function {name}' in js
    for route in ['#/demo','#/demo/guide','#/demo/routes','#/demo/assets','#/demo/package','#/demo/safety','#/demo/validation']:
        assert route in js
    for route in ['#/order','#/trade','#/approve','#/approval','#/auto-approve','#/account','#/positions']:
        assert route not in [x.route for x in build_demo_route_map() if x.allowed]
    for f in ["fetch('./demo_manifest.json')","fetch('./demo_guide.json')","fetch('./demo_route_map.json')","fetch('./demo_asset_manifest.json')","fetch('./demo_package_index.json')","fetch('./demo_safety_report.json')","fetch('./demo_validation_summary.json')"]:
        assert f in js
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/live')",'XMLHttpRequest','tradeButton','approveButton','orderButton','liveButton','autoApproveButton']:
        assert bad not in js and bad not in html

def test_content_sections_are_safe():
    assert build_demo_manifest() and build_demo_guide() and build_demo_route_map() and build_demo_asset_manifest() and build_demo_package_index() and build_demo_safety_report() and build_demo_validation_summary()
    guide=' '.join(x.body for x in build_demo_guide())
    manifest=build_demo_manifest().safety_note
    package=' '.join(x.note for x in build_demo_package_index())
    assert '不是审批授权' in guide and '不是交易授权' in manifest and '只列本地演示材料' in package
    for bad in ['.env','token','secret','market_data','reports','logs','validation_logs']:
        assert all(bad not in x.file_name for x in build_demo_package_index())

def test_safety_classification():
    assert classify_demo_marker('xttrader','Safety Banner：不调用 xttrader','index.html') != LocalConsoleDemoSeverity.CRITICAL
    assert classify_demo_marker('不是审批授权','demo guide 不是审批授权','demo_guide.md') != LocalConsoleDemoSeverity.CRITICAL
    assert classify_demo_marker("fetch('/trade')","function x(){ fetch('/trade') }",'app.js') == LocalConsoleDemoSeverity.CRITICAL
    assert classify_demo_marker('xtdata','xtquant.xtdata','reader.py') != LocalConsoleDemoSeverity.CRITICAL

def test_formatter_safety_note():
    r=LocalConsoleDemoPackageReport(decision=LocalConsoleDemoDecision.READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW)
    md=format_local_console_demo_package_report_md(r)
    assert '## Safety Note' in md
    assert 'READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW 只表示本地演示打包层材料可供人工复核' in md

def test_cli_generates_all_outputs(tmp_path):
    help_dir=tmp_path/'local_console_help_stage73'; help_dir.mkdir()
    (help_dir/'local_console_help_docs_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW','summary':{'critical_count':0}},ensure_ascii=False),encoding='utf-8')
    out=tmp_path/'local_console_demo_stage74'
    cmd=[sys.executable,'scripts/run_local_console_demo_package.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--help-dir','local_console_help_stage73']
    res=subprocess.run(cmd,cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True,check=False)
    assert res.returncode == 0, res.stderr + res.stdout
    for n in ['local_console_demo_package_report','demo_manifest','demo_guide','demo_route_map','demo_asset_manifest','demo_package_index','demo_safety_report','demo_validation_summary','next_ui_productization_closure_plan']:
        assert (out/f'{n}.md').exists() and (out/f'{n}.json').exists()
    assert (out/'index.html').exists() and (out/'app.js').exists() and (out/'style.css').exists()
    text='\n'.join(p.read_text(encoding='utf-8') for p in out.glob('*.md'))
    for bad in ['鏈','鍙','楠','涓','绛','璇','瀹','鐩','鎺','鏉','�','\x00']:
        assert bad not in text

def test_repo_stage74_static_requirements():
    root=Path(__file__).resolve().parents[1]
    roadmap=(root/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in roadmap
    assert 'Stage61-75 前端 UI 产品化计划' in roadmap
    assert 'UI 不能绕过 Risk Gate' in roadmap and '不能直接访问 QMT' in roadmap and '不能自动 approve' in roadmap
    assert not list((root/'scripts').glob('validate_stage73.ps1.bak_stage73fix_*'))
    v=(root/'scripts/validate_stage74.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v
    assert 'Clean-PythonCache' in v and 'Print-File' in v and 'Check-NoBackup' in v
    assert v.find('Clean-PythonCache') < v.rfind('sync_all.ps1')
