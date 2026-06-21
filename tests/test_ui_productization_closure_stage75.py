from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.local_console.closure_models import *
from qmt_ai_trading.local_console.closure_assets import *
from qmt_ai_trading.local_console.closure_safety import *
from qmt_ai_trading.local_console.closure_formatters import format_ui_productization_closure_report_md
from qmt_ai_trading.local_console.closure_service import build_default_local_console_closure_config, run_ui_productization_closure_review

def test_models_defaults():
    assert LocalConsoleClosureConfig().read_only is True
    assert UiProductizationClosureReport().decision == LocalConsoleClosureDecision.NEED_MORE_EVIDENCE

def test_missing_stage74_needs_evidence(tmp_path):
    r=run_ui_productization_closure_review(build_default_local_console_closure_config(repo_root=str(tmp_path)))
    assert r.decision in {LocalConsoleClosureDecision.NEED_MORE_EVIDENCE, LocalConsoleClosureDecision.NO_GO}

def test_stage74_ready_and_no_go(tmp_path):
    d=tmp_path/'local_console_demo_stage74'; d.mkdir()
    (d/'local_console_demo_package_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW','summary':{'critical_count':0}},ensure_ascii=False),encoding='utf-8')
    assert run_ui_productization_closure_review(build_default_local_console_closure_config(repo_root=str(tmp_path))).decision == LocalConsoleClosureDecision.READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW
    (d/'local_console_demo_package_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':0}},ensure_ascii=False),encoding='utf-8')
    assert run_ui_productization_closure_review(build_default_local_console_closure_config(repo_root=str(tmp_path))).decision == LocalConsoleClosureDecision.NO_GO
    (d/'local_console_demo_package_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW','summary':{'critical_count':1}},ensure_ascii=False),encoding='utf-8')
    assert run_ui_productization_closure_review(build_default_local_console_closure_config(repo_root=str(tmp_path))).decision == LocalConsoleClosureDecision.NO_GO

def test_assets_routes_and_frontend_are_readonly():
    html=build_closure_index_html(); js=build_closure_app_js(); css=build_closure_style_css()
    for s in ['Header / Project Title','Safety Banner','UI Productization Closure Home Panel','Stage Overview Panel','Capability Matrix Panel','Safety Boundary Table Panel','Read-only Demo Entry Panel','Route Coverage Summary Panel','Asset Coverage Summary Panel','Risk and Limitation Summary Panel','Final Acceptance Conclusion Draft Panel','Future Roadmap Recommendation Panel','Stage74 Demo Evidence Panel','Loading State','Error State','Empty State','Footer']:
        assert s in html
    assert css
    for name in ['loadClosureReport','loadStageOverview','loadCapabilityMatrix','loadSafetyBoundaryTable','loadReadonlyDemoEntry','loadRouteCoverageSummary','loadAssetCoverageSummary','loadRiskLimitationSummary','loadFinalAcceptanceConclusionDraft','loadFutureRoadmapRecommendation','loadClosureSafetyReport','renderClosureHome','renderStageOverview','renderCapabilityMatrix','renderSafetyBoundaryTable','renderReadonlyDemoEntry','renderRouteCoverageSummary','renderAssetCoverageSummary','renderRiskLimitationSummary','renderFinalAcceptanceConclusionDraft','renderFutureRoadmapRecommendation','renderClosureSafetyReport','searchClosureReadOnly','copyClosureSectionReadOnly','renderForbiddenRouteState','renderCurrentRoute','updateLastLoadedAt']:
        assert f'function {name}' in js or f'async function {name}' in js
    for route in ['#/closure','#/closure/stages','#/closure/capabilities','#/closure/safety','#/closure/demo','#/closure/routes','#/closure/assets','#/closure/risks','#/closure/conclusion','#/closure/roadmap']:
        assert route in js
    for route in ['#/order','#/trade','#/approve','#/approval','#/auto-approve','#/account','#/positions']:
        assert route not in [x.route for x in build_route_coverage_summary() if x.allowed]
    for f in ["fetch('./ui_productization_closure_report.json')","fetch('./stage_overview.json')","fetch('./capability_matrix.json')","fetch('./safety_boundary_table.json')","fetch('./readonly_demo_entry.json')","fetch('./route_coverage_summary.json')","fetch('./asset_coverage_summary.json')","fetch('./risk_limitation_summary.json')","fetch('./final_acceptance_conclusion_draft.json')","fetch('./future_roadmap_recommendation.json')","fetch('./closure_safety_report.json')"]:
        assert f in js
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/live')",'XMLHttpRequest','tradeButton','approveButton','orderButton','liveButton','autoApproveButton']:
        assert bad not in js and bad not in html

def test_content_sections_are_safe():
    assert build_stage_overview() and build_capability_matrix() and build_safety_boundary_table() and build_readonly_demo_entry() and build_route_coverage_summary() and build_asset_coverage_summary() and build_risk_limitation_summary() and build_final_acceptance_conclusion_draft() and build_future_roadmap_recommendation() and build_closure_safety_report()
    assert '不是审批授权' in ' '.join(x.safety_note for x in build_capability_matrix())
    assert '不是交易授权' in build_final_acceptance_conclusion_draft().conclusion
    assert '不越级接实盘' in ' '.join(x.recommendation for x in build_future_roadmap_recommendation())
    for bad in ['.env','token','secret','market_data','reports','logs','validation_logs']:
        assert all(bad not in x.file_name for x in build_asset_coverage_summary())

def test_safety_classification_and_formatter():
    assert classify_closure_marker('xttrader','Safety Banner：不调用 xttrader','index.html') != LocalConsoleClosureSeverity.CRITICAL
    assert classify_closure_marker('不是审批授权','final conclusion 不是审批授权','final_acceptance_conclusion_draft.md') != LocalConsoleClosureSeverity.CRITICAL
    assert classify_closure_marker("fetch('/trade')","function x(){ fetch('/trade') }",'app.js') == LocalConsoleClosureSeverity.CRITICAL
    assert classify_closure_marker('xtdata','xtquant.xtdata','reader.py') != LocalConsoleClosureSeverity.CRITICAL
    md=format_ui_productization_closure_report_md(UiProductizationClosureReport(decision=LocalConsoleClosureDecision.READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW))
    assert '## Safety Note' in md and 'READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW 只表示 UI 产品化收口层材料可供人工复核' in md

def test_cli_generates_all_outputs(tmp_path):
    d=tmp_path/'local_console_demo_stage74'; d.mkdir()
    (d/'local_console_demo_package_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW','summary':{'critical_count':0}},ensure_ascii=False),encoding='utf-8')
    out=tmp_path/'local_console_closure_stage75'
    res=subprocess.run([sys.executable,'scripts/run_ui_productization_closure.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--demo-dir','local_console_demo_stage74'],cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True,check=False)
    assert res.returncode == 0, res.stderr + res.stdout
    for n in ['ui_productization_closure_report','stage_overview','capability_matrix','safety_boundary_table','readonly_demo_entry','route_coverage_summary','asset_coverage_summary','risk_limitation_summary','final_acceptance_conclusion_draft','future_roadmap_recommendation','closure_safety_report']:
        assert (out/f'{n}.md').exists() and (out/f'{n}.json').exists()
    assert (out/'index.html').exists() and (out/'app.js').exists() and (out/'style.css').exists()
    text='\n'.join(p.read_text(encoding='utf-8') for p in out.glob('*.md'))
    for bad in ['鏈','鍙','楠','涓','绛','璇','瀹','鐩','鎺','鏉','�','\x00']:
        assert bad not in text

def test_daily_scheduled_register_and_repo_static(tmp_path):
    root=Path(__file__).resolve().parents[1]
    assert 'validation_logs/' in (root/'.gitignore').read_text(encoding='utf-8')
    assert not list((root/'scripts').glob('validate_stage74.ps1.bak_stage74fix_*'))
    assert (root/'scripts/sync_all.ps1').exists()
    roadmap=(root/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in roadmap and 'Stage61-75 前端 UI 产品化计划' in roadmap
    assert 'UI 不能绕过 Risk Gate' in roadmap and '不能直接访问 QMT' in roadmap and '不能自动 approve' in roadmap
    v=(root/'scripts/validate_stage75.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v and 'Clean-PythonCache' in v and 'Print-File' in v and 'Check-NoBackup' in v
    assert v.find('Clean-PythonCache') < v.rfind('sync_all.ps1')
    assert '\\`' not in v
