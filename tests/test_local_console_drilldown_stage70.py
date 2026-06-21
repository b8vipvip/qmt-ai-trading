from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

from qmt_ai_trading.local_console.drilldown_models import *
from qmt_ai_trading.local_console.drilldown_assets import *
from qmt_ai_trading.local_console.drilldown_safety import *
from qmt_ai_trading.local_console.drilldown_export import *
from qmt_ai_trading.local_console.drilldown_formatters import format_local_console_drilldown_report_md
from qmt_ai_trading.local_console.drilldown_service import build_default_local_console_drilldown_config, run_local_console_drilldown_review


def test_models_default_constructible():
    assert LocalConsoleDrilldownConfig().read_only is True
    assert LocalConsoleDrilldownReport().summary['no_trade_authorization'] is True


def test_missing_stage69_needs_more_evidence(tmp_path):
    r=run_local_console_drilldown_review(LocalConsoleDrilldownConfig(repo_root=str(tmp_path)))
    assert r.decision in {LocalConsoleDrilldownDecision.NEED_MORE_EVIDENCE, LocalConsoleDrilldownDecision.NO_GO}


def test_stage69_ready_allows_stage70_ready(tmp_path):
    d=tmp_path/'local_console_grouping_stage69'; d.mkdir()
    (d/'local_console_grouping_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW','summary':{'critical_count':0}}),encoding='utf-8')
    r=run_local_console_drilldown_review(LocalConsoleDrilldownConfig(repo_root=str(tmp_path)))
    assert r.decision == LocalConsoleDrilldownDecision.READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW


def test_stage69_nogo_or_critical_blocks(tmp_path):
    d=tmp_path/'local_console_grouping_stage69'; d.mkdir()
    (d/'local_console_grouping_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':0}}),encoding='utf-8')
    assert run_local_console_drilldown_review(LocalConsoleDrilldownConfig(repo_root=str(tmp_path))).decision == LocalConsoleDrilldownDecision.NO_GO
    (d/'local_console_grouping_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW','summary':{'critical_count':1}}),encoding='utf-8')
    assert run_local_console_drilldown_review(LocalConsoleDrilldownConfig(repo_root=str(tmp_path))).decision == LocalConsoleDrilldownDecision.NO_GO


def test_assets_generate_and_routes():
    html=build_drilldown_index_html(); js=build_drilldown_app_js(); css=build_drilldown_style_css()
    assert 'Report Detail Panel' in html and 'Copy Summary Button' in html and css
    assert 'loadDataBundle()' in js and 'openReportDetail(reportId)' in js
    routes=[r.route for r in build_drilldown_route_map()]
    for r in ['#/reports/detail','#/reports/preview','#/reports/export','#/review-package']:
        assert r in routes
    for r in ['#/order','#/trade','#/approve','#/account','#/positions']:
        assert r not in routes


def test_fetches_and_forbidden_buttons_absent():
    js=build_drilldown_app_js(); html=build_drilldown_index_html()
    for source in ['./data_bundle.json','./binding_manifest.json','./data_source_map.json','./static_data_safety.json','./report_detail_index.json','./export_manifest.json']:
        assert source in js
    for bad in ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/live')",'XMLHttpRequest']:
        assert bad not in js
    for bad in ['tradeButton','approveButton','orderButton','liveButton']:
        assert bad not in html
    assert 'copySummaryReadOnly' in js and 'network_enabled:false' in js
    assert 'exportMarkdownSnapshotReadOnly' in js and 'exportJsonSnapshotReadOnly' in js


def test_export_safety_rules():
    snap=build_export_snapshot()
    assert snap.read_only and snap.dry_run_only and snap.no_trade_authorization
    md=build_markdown_snapshot(snap); js=build_json_snapshot(snap)
    assert 'read_only=True' in md and 'no_trade_authorization' in js
    for bad in ['../x','/tmp/x']:
        try: assert_export_path_is_safe(bad); assert False
        except ValueError: pass
    for bad in ['.env','token','secret','credential','market_data/raw','reports/raw','logs/raw','validation_logs/raw']:
        try: assert_no_sensitive_export_sources([bad]); assert False
        except ValueError: pass


def test_forbidden_route_and_marker_classification():
    assert classify_drilldown_hash_route('#/trade') == LocalConsoleDrilldownSeverity.CRITICAL
    assert '该路由被安全边界禁止' in build_drilldown_app_js()
    assert classify_drilldown_marker('xttrader','index.html','Safety Banner：不调用 xttrader') != LocalConsoleDrilldownSeverity.CRITICAL
    assert classify_drilldown_marker('xttrader','data_bundle.json','历史说明 不调用 xttrader',generated=True) != LocalConsoleDrilldownSeverity.CRITICAL
    assert classify_drilldown_marker("fetch('/trade')",'app.js',"fetch('/trade')") == LocalConsoleDrilldownSeverity.CRITICAL
    assert classify_drilldown_marker('xtdata','x.py','xtquant.xtdata') != LocalConsoleDrilldownSeverity.CRITICAL


def test_formatter_safety_note():
    md=format_local_console_drilldown_report_md(LocalConsoleDrilldownReport(decision=LocalConsoleDrilldownDecision.READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW))
    assert '## Safety Note' in md
    assert 'READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW 只表示' in md


def test_cli_generates_all_outputs(tmp_path):
    out=tmp_path/'pkg'
    cmd=[sys.executable,'scripts/run_local_console_drilldown_review.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'local_console_drilldown_report.md'),'--json-output',str(out/'local_console_drilldown_report.json'),'--detail-output',str(out/'report_detail_index.md'),'--detail-json-output',str(out/'report_detail_index.json'),'--route-output',str(out/'drilldown_route_map.md'),'--route-json-output',str(out/'drilldown_route_map.json'),'--export-output',str(out/'export_manifest.md'),'--export-json-output',str(out/'export_manifest.json'),'--snapshot-output',str(out/'export_snapshot.md'),'--snapshot-json-output',str(out/'export_snapshot.json'),'--safety-output',str(out/'export_safety_report.md'),'--safety-json-output',str(out/'export_safety_report.json'),'--plan-output',str(out/'next_manual_review_workbench_plan.md'),'--plan-json-output',str(out/'next_manual_review_workbench_plan.json')]
    res=subprocess.run(cmd,cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True)
    assert res.returncode == 0, res.stderr + res.stdout
    for name in ['local_console_drilldown_report.md','local_console_drilldown_report.json','report_detail_index.md','report_detail_index.json','drilldown_route_map.md','drilldown_route_map.json','export_manifest.md','export_manifest.json','export_snapshot.md','export_snapshot.json','export_safety_report.md','export_safety_report.json','next_manual_review_workbench_plan.md','next_manual_review_workbench_plan.json','index.html','app.js','style.css']:
        assert (out/name).exists(), name


def test_daily_scheduled_register_flags(tmp_path):
    root=Path(__file__).resolve().parents[1]
    out=tmp_path/'dd'
    res=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'market'),'--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-drilldown-review','--local-console-drilldown-review-output-dir',str(out)],cwd=root,text=True,capture_output=True)
    assert res.returncode == 0, res.stderr + res.stdout
    assert (out/'local_console_drilldown_report.md').exists()
    out2=tmp_path/'sch'
    res=subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--warmup-universe','--warmup-provider','mock','--universe-lookback-days','90','--warmup-frequency','1d','--cache-root',str(tmp_path/'market2'),'--data-source-mode','cached_real_first','--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-drilldown-review','--local-console-drilldown-review-output-dir',str(out2)],cwd=root,text=True,capture_output=True)
    assert res.returncode == 0, res.stderr + res.stdout
    assert (out2/'local_console_drilldown_report.md').exists()
    res=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-local-console-drilldown-review','--local-console-drilldown-review-output-dir','local_console_drilldown','--time','15:30'],cwd=root,text=True,capture_output=True)
    assert res.returncode == 0
    assert 'no_task_registered=True' in res.stdout and 'enable_local_console_drilldown_review=True' in res.stdout


def test_repo_policy_files():
    root=Path(__file__).resolve().parents[1]
    assert not list((root/'scripts').glob('validate_stage69.ps1.bak_stage69fix_*'))
    assert not list((root/'scripts').glob('validate_stage70.ps1.bak_stage70fix_*'))
    roadmap=(root/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线' in roadmap
    assert 'Stage61-75' in roadmap
    assert 'Risk Gate' in roadmap and 'Human Approval' in roadmap and '不能直接访问 QMT' in roadmap and '不能自动 approve' in roadmap
    validate=(root/'scripts/validate_stage70.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in validate
    assert 'Clean-PythonCache' in validate
    assert validate.index('Clean-PythonCache') < validate.rindex('sync_all.ps1')
    assert 'validation_logs/' in (root/'.gitignore').read_text(encoding='utf-8')
    assert '__pycache__/' in (root/'.gitignore').read_text(encoding='utf-8')
