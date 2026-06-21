from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.local_console.acceptance_models import *
from qmt_ai_trading.local_console.acceptance_assets import *
from qmt_ai_trading.local_console.acceptance_formatters import format_local_console_ui_acceptance_report_md
from qmt_ai_trading.local_console.acceptance_safety import classify_acceptance_marker, scan_acceptance_assets_for_forbidden_markers, LocalConsoleAcceptanceSeverity
from qmt_ai_trading.local_console.acceptance_service import *


def assert_no_mojibake(text: str) -> None:
    bad_markers = [
        "鏈", "鍙", "楠", "涓", "绛", "璇", "瀹", "鐩", "鎺", "鏉",
        "�", "\x00",
    ]
    for marker in bad_markers:
        assert marker not in text

def test_models_default():
    assert LocalConsoleAcceptanceConfig().read_only
    assert LocalConsoleUiAcceptanceReport().decision == LocalConsoleAcceptanceDecision.NEED_MORE_EVIDENCE

def test_missing_stage71_needs_more_evidence(tmp_path):
    r=run_local_console_ui_acceptance_review(LocalConsoleAcceptanceConfig(repo_root=str(tmp_path),output_dir='out'))
    assert r.decision in {LocalConsoleAcceptanceDecision.NEED_MORE_EVIDENCE, LocalConsoleAcceptanceDecision.NO_GO}

def test_stage71_ready_allows_stage72_ready(tmp_path):
    d=tmp_path/'local_console_review_stage71'; d.mkdir()
    (d/'local_console_review_workbench_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_REVIEW_WORKBENCH_REVIEW','summary':{'critical_count':0}}),encoding='utf-8')
    r=run_local_console_ui_acceptance_review(LocalConsoleAcceptanceConfig(repo_root=str(tmp_path),output_dir='out'))
    assert r.decision == LocalConsoleAcceptanceDecision.READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW

def test_stage71_nogo_blocks(tmp_path):
    d=tmp_path/'local_console_review_stage71'; d.mkdir()
    (d/'local_console_review_workbench_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':1}}),encoding='utf-8')
    r=run_local_console_ui_acceptance_review(LocalConsoleAcceptanceConfig(repo_root=str(tmp_path),output_dir='out'))
    assert r.decision == LocalConsoleAcceptanceDecision.NO_GO

def test_assets_and_routes_are_readonly():
    html=build_acceptance_index_html(); js=build_acceptance_app_js(); css=build_acceptance_style_css()
    for text in ['Header / Project Title','Safety Banner','Navigation Tabs','UI Acceptance Summary Panel','Page Inventory Panel','Feature Inventory Panel','Safety Checklist Panel','Open Items Panel','Route Coverage Panel','Asset Coverage Panel','Acceptance Conclusion Draft Panel','Acceptance Package Index Panel','Stage71 Review Evidence Panel','Loading State','Error State','Empty State','Footer','本地只读控制台','不是实盘授权','不下单','不调用 xttrader','不查询真实账户','不发送真实通知','不是审批授权']:
        assert text in html
    for fn in ['loadAcceptanceSummary','loadPageInventory','loadFeatureInventory','loadSafetyChecklist','loadOpenItems','loadRouteCoverage','loadAssetCoverage','renderAcceptanceSummary','renderPageInventory','renderFeatureInventory','renderSafetyChecklist','renderOpenItems','renderRouteCoverage','renderAssetCoverage','renderAcceptanceConclusionDraft','renderAcceptancePackageIndex','copyAcceptanceConclusionReadOnly','exportAcceptanceSummaryReadOnly','renderForbiddenRouteState','renderCurrentRoute','updateLastLoadedAt']:
        assert f'function {fn}' in js or f'async function {fn}' in js
    for route in ['#/ui-acceptance','#/pages','#/features','#/safety-checklist','#/open-items','#/route-coverage','#/asset-coverage','#/acceptance-conclusion','#/acceptance-package']:
        assert route in js
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/live')","XMLHttpRequest",'tradeButton','approveButton','orderButton','liveButton','autoApproveButton']:
        assert bad not in js and bad not in html
    for good in ["fetch('./ui_acceptance_summary.json')","fetch('./page_inventory.json')","fetch('./feature_inventory.json')","fetch('./safety_checklist.json')","fetch('./open_items.json')","fetch('./route_coverage.json')","fetch('./asset_coverage.json')","fetch('./acceptance_package_index.json')"]:
        assert good in js
    assert css

def test_reports_semantics_and_safety():
    assert build_ui_acceptance_summary().note.endswith('不是审批授权。')
    assert '不是交易授权' in build_acceptance_conclusion_draft().draft
    assert all(i.read_only for i in build_acceptance_package_index())
    assert classify_acceptance_marker('xttrader','index.html','不调用 xttrader') != LocalConsoleAcceptanceSeverity.CRITICAL
    assert classify_acceptance_marker('approve','md','不是审批授权') != LocalConsoleAcceptanceSeverity.CRITICAL
    assert any(f.severity==LocalConsoleAcceptanceSeverity.CRITICAL for f in scan_acceptance_assets_for_forbidden_markers({'app.js':"fetch('/trade')"}))
    md=format_local_console_ui_acceptance_report_md(LocalConsoleUiAcceptanceReport(decision=LocalConsoleAcceptanceDecision.READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW))
    assert '## Safety Note' in md and 'READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW 只表示' in md

def test_cli_generates_all_outputs(tmp_path):
    cmd=[sys.executable,'scripts/run_local_console_ui_acceptance.py','--repo-root',str(tmp_path),'--output-dir','out']
    res=subprocess.run(cmd,cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True)
    assert res.returncode == 0, res.stderr
    out=tmp_path/'out'
    for n in ['local_console_ui_acceptance_report.md','local_console_ui_acceptance_report.json','ui_acceptance_summary.md','ui_acceptance_summary.json','page_inventory.md','page_inventory.json','feature_inventory.md','feature_inventory.json','safety_checklist.md','safety_checklist.json','open_items.md','open_items.json','route_coverage.md','route_coverage.json','asset_coverage.md','asset_coverage.json','acceptance_conclusion_draft.md','acceptance_conclusion_draft.json','acceptance_package_index.md','acceptance_package_index.json','ui_acceptance_safety_report.md','ui_acceptance_safety_report.json','next_local_help_docs_plan.md','next_local_help_docs_plan.json','index.html','app.js','style.css']:
        assert (out/n).exists(), n

def test_docs_validate_and_gitignore():
    root=Path(__file__).resolve().parents[1]
    roadmap=(root/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线' in roadmap and 'Stage61-75' in roadmap
    assert 'UI 不能绕过 Risk Gate' in roadmap and 'Human Approval' in roadmap and '不能直接访问 QMT' in roadmap and '不能自动 approve' in roadmap
    assert not list((root/'scripts').glob('validate_stage71.ps1.bak_stage71fix_*'))
    v=(root/'scripts/validate_stage72.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v
    assert 'Clean-PythonCache' in v and 'Print-File' in v and 'Check-NoBackup' in v
    assert 'Get-Content -LiteralPath $Path -Encoding UTF8' in v
    assert v.find('Clean-PythonCache') < v.rfind('sync_all.ps1 -Mode scan')
    gi=(root/'.gitignore').read_text(encoding='utf-8')
    assert 'validation_logs/' in gi and 'local_console_acceptance_stage72/' in gi

def test_daily_scheduled_register_options(tmp_path):
    root=Path(__file__).resolve().parents[1]
    r=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'m'),'--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-ui-acceptance','--local-console-ui-acceptance-output-dir',str(tmp_path/'acc')],cwd=root,text=True,capture_output=True)
    assert r.returncode == 0, r.stderr
    assert (tmp_path/'acc'/'local_console_ui_acceptance_report.json').exists()
    r=subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--warmup-universe','--warmup-provider','mock','--universe-lookback-days','90','--warmup-frequency','1d','--cache-root',str(tmp_path/'m2'),'--data-source-mode','cached_real_first','--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-ui-acceptance','--local-console-ui-acceptance-output-dir',str(tmp_path/'acc2')],cwd=root,text=True,capture_output=True)
    assert r.returncode == 0, r.stderr
    assert (tmp_path/'acc2'/'local_console_ui_acceptance_report.json').exists()
    r=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-local-console-ui-acceptance','--local-console-ui-acceptance-output-dir','local_console_acceptance','--time','15:30'],cwd=root,text=True,capture_output=True)
    assert r.returncode == 0 and 'read_only=True' in r.stdout and 'dry_run_only=True' in r.stdout and 'no_trade_authorization=True' in r.stdout and 'no_task_registered=True' in r.stdout


def test_cli_outputs_utf8_readable_chinese_without_mojibake(tmp_path):
    cmd = [sys.executable, 'scripts/run_local_console_ui_acceptance.py', '--repo-root', str(tmp_path), '--output-dir', 'out']
    res = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    out = tmp_path / 'out'
    markdown_files = [
        'local_console_ui_acceptance_report.md',
        'ui_acceptance_summary.md',
        'page_inventory.md',
        'feature_inventory.md',
        'safety_checklist.md',
        'open_items.md',
        'route_coverage.md',
        'asset_coverage.md',
        'acceptance_conclusion_draft.md',
        'acceptance_package_index.md',
        'ui_acceptance_safety_report.md',
        'next_local_help_docs_plan.md',
    ]
    json_files = [name.replace('.md', '.json') for name in markdown_files]
    expected_chinese = {
        'local_console_ui_acceptance_report.md': [
            '本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。',
            'READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW 只表示本地控制台 UI 验收汇总层材料可供人工复核。',
            'UI acceptance summary / acceptance conclusion draft 都不是审批授权。',
            'Stage73 进入本地文档/帮助层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。',
        ],
        'ui_acceptance_summary.md': ['UI acceptance summary 只是本地验收材料，不是审批授权。'],
        'page_inventory.md': ['本地只读页面，不是实盘授权。'],
        'feature_inventory.md': ['UI 验收汇总', '只汇总材料状态，不写审批授权。'],
        'safety_checklist.md': ['不下单，不调用 xttrader，不查询真实账户，不发送真实通知。'],
        'route_coverage.md': ['该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。'],
        'acceptance_conclusion_draft.md': ['验收结论草稿：仅表示本地控制台 UI 验收汇总材料可供人工复核，不是审批授权，不是交易授权。'],
        'next_local_help_docs_plan.md': ['本地文档/帮助层', 'Stage73 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'],
    }
    for name in markdown_files:
        raw = (out / name).read_bytes()
        assert not raw.startswith(b'\xef\xbb\xbf'), name
        text = raw.decode('utf-8')
        assert_no_mojibake(text)
        for phrase in expected_chinese.get(name, []):
            assert phrase in text
    for name in json_files:
        raw = (out / name).read_bytes()
        assert not raw.startswith(b'\xef\xbb\xbf'), name
        text = raw.decode('utf-8')
        assert_no_mojibake(text)
        assert '\\u4' not in text and '\\u9' not in text and '\\u' not in text
        json.loads(text)
    summary_json = (out / 'ui_acceptance_summary.json').read_text(encoding='utf-8')
    assert 'UI acceptance summary 只是本地验收材料，不是审批授权。' in summary_json
    report_json = (out / 'local_console_ui_acceptance_report.json').read_text(encoding='utf-8')
    assert '验收结论草稿：仅表示本地控制台 UI 验收汇总材料可供人工复核，不是审批授权，不是交易授权。' in report_json
