from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.local_console.help_models import *
from qmt_ai_trading.local_console.help_assets import *
from qmt_ai_trading.local_console.help_safety import *
from qmt_ai_trading.local_console.help_formatters import format_local_console_help_docs_report_md
from qmt_ai_trading.local_console.help_service import build_default_local_console_help_config, run_local_console_help_docs_review


def test_models_defaults():
    assert LocalConsoleHelpConfig().read_only is True
    assert LocalConsoleHelpDocsReport().decision == LocalConsoleHelpDecision.NEED_MORE_EVIDENCE


def test_missing_stage72_needs_evidence(tmp_path):
    r=run_local_console_help_docs_review(build_default_local_console_help_config(repo_root=str(tmp_path)))
    assert r.decision in {LocalConsoleHelpDecision.NEED_MORE_EVIDENCE, LocalConsoleHelpDecision.NO_GO}


def test_stage72_ready_allows_ready(tmp_path):
    d=tmp_path/'local_console_acceptance_stage72'; d.mkdir()
    (d/'local_console_ui_acceptance_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW','summary':{'critical_count':0}},ensure_ascii=False),encoding='utf-8')
    r=run_local_console_help_docs_review(build_default_local_console_help_config(repo_root=str(tmp_path)))
    assert r.decision == LocalConsoleHelpDecision.READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW


def test_stage72_no_go_blocks(tmp_path):
    d=tmp_path/'local_console_acceptance_stage72'; d.mkdir()
    (d/'local_console_ui_acceptance_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':0}},ensure_ascii=False),encoding='utf-8')
    r=run_local_console_help_docs_review(build_default_local_console_help_config(repo_root=str(tmp_path)))
    assert r.decision == LocalConsoleHelpDecision.NO_GO
    (d/'local_console_ui_acceptance_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW','summary':{'critical_count':1}},ensure_ascii=False),encoding='utf-8')
    r=run_local_console_help_docs_review(build_default_local_console_help_config(repo_root=str(tmp_path)))
    assert r.decision == LocalConsoleHelpDecision.NO_GO


def test_assets_and_routes_are_readonly():
    html=build_help_index_html(); js=build_help_app_js(); css=build_help_style_css()
    assert 'Header / Project Title' in html and 'Safety Banner' in html and 'Footer' in html
    assert css
    for name in ['loadHelpHome','loadPageHelp','loadFeatureHelp','loadSafetyHelp','loadFaq','loadErrorHandlingGuide','loadGlossary','loadRouteHelpMap','loadHelpPackageIndex','renderHelpHome','renderPageHelp','renderFeatureHelp','renderSafetyHelp','renderFaq','renderErrorHandlingGuide','renderGlossary','renderRouteHelpMap','renderHelpPackageIndex','searchHelpReadOnly','copyHelpSectionReadOnly','renderForbiddenRouteState','renderCurrentRoute','updateLastLoadedAt']:
        assert f'function {name}' in js or f'async function {name}' in js
    for route in ['#/help','#/help/pages','#/help/features','#/help/safety','#/help/faq','#/help/errors','#/help/glossary','#/help/routes','#/help/package']:
        assert route in js
    for route in ['#/order','#/trade','#/approve','#/approval','#/auto-approve','#/account','#/positions']:
        assert route not in [x.route for x in build_page_help()]
    for f in ["fetch('./help_home.json')","fetch('./page_help.json')","fetch('./feature_help.json')","fetch('./safety_help.json')","fetch('./faq.json')","fetch('./error_handling_guide.json')","fetch('./glossary.json')","fetch('./route_help_map.json')","fetch('./help_package_index.json')","fetch('./docs_safety_report.json')"]:
        assert f in js
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/live')","XMLHttpRequest",'tradeButton','approveButton','orderButton','liveButton','autoApproveButton']:
        assert bad not in js and bad not in html


def test_content_sections_are_safe():
    assert build_help_home() and build_page_help() and build_feature_help() and build_safety_help()
    assert build_faq() and build_error_handling_guide() and build_glossary() and build_route_help_map() and build_help_package_index()
    faq=' '.join(x.answer for x in build_faq())
    glossary=' '.join(x.definition for x in build_glossary())
    package=' '.join(x.note for x in build_help_package_index())
    assert '不是审批授权' in faq
    assert '绕过风控' not in faq
    assert '自动授权' not in glossary
    assert '不触发任务' in package


def test_safety_classification():
    assert classify_help_marker('xttrader','Safety Banner：不调用 xttrader','index.html') != LocalConsoleHelpSeverity.CRITICAL
    assert classify_help_marker('不是审批授权','help docs 不是审批授权','faq.md') != LocalConsoleHelpSeverity.CRITICAL
    assert classify_help_marker("fetch('/trade')","function x(){ fetch('/trade') }",'app.js') == LocalConsoleHelpSeverity.CRITICAL
    assert classify_help_marker('xtdata','xtquant.xtdata','reader.py') != LocalConsoleHelpSeverity.CRITICAL


def test_formatter_safety_note():
    r=LocalConsoleHelpDocsReport(decision=LocalConsoleHelpDecision.READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW)
    md=format_local_console_help_docs_report_md(r)
    assert '## Safety Note' in md
    assert 'READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW 只表示本地文档/帮助层材料可供人工复核' in md


def test_cli_generates_all_outputs(tmp_path):
    acc=tmp_path/'local_console_acceptance_stage72'; acc.mkdir()
    (acc/'local_console_ui_acceptance_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW','summary':{'critical_count':0}},ensure_ascii=False),encoding='utf-8')
    out=tmp_path/'local_console_help_stage73'
    cmd=[sys.executable,'scripts/run_local_console_help_docs.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--acceptance-dir','local_console_acceptance_stage72']
    res=subprocess.run(cmd,cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True,check=False)
    assert res.returncode == 0, res.stderr + res.stdout
    for n in ['local_console_help_docs_report','help_home','page_help','feature_help','safety_help','faq','error_handling_guide','glossary','route_help_map','help_package_index','docs_safety_report','next_local_demo_package_plan']:
        assert (out/f'{n}.md').exists()
        assert (out/f'{n}.json').exists()
    assert (out/'index.html').exists() and (out/'app.js').exists() and (out/'style.css').exists()
    text='\n'.join(p.read_text(encoding='utf-8') for p in out.glob('*.md'))
    for bad in ['鏈','鍙','楠','涓','绛','璇','瀹','鐩','鎺','鏉','�','\x00']:
        assert bad not in text


def test_repo_stage73_static_requirements():
    root=Path(__file__).resolve().parents[1]
    roadmap=(root/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in roadmap
    assert 'Stage61-75 前端 UI 产品化计划' in roadmap
    assert 'UI 不能绕过 Risk Gate' in roadmap and '不能直接访问 QMT' in roadmap and '不能自动 approve' in roadmap
    assert not list((root/'scripts').glob('validate_stage72.ps1.bak_stage72fix_*'))
    v=(root/'scripts/validate_stage73.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v
    assert 'Clean-PythonCache' in v and 'Print-File' in v and 'Check-NoBackup' in v
    assert v.find('Clean-PythonCache') < v.rfind('sync_all.ps1')
