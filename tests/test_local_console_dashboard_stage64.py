from pathlib import Path
import json, subprocess, sys
from qmt_ai_trading.local_console.dashboard_models import *
from qmt_ai_trading.local_console.dashboard_service import *
from qmt_ai_trading.local_console.dashboard_cards import *
from qmt_ai_trading.local_console.dashboard_reader import decode_text_file_auto, read_latest_validation_detail
from qmt_ai_trading.local_console.dashboard_safety import *
from qmt_ai_trading.local_console.dashboard_formatters import format_dashboard_report_md

def test_defaults_and_cards():
    assert LocalConsoleDashboardConfig()
    assert LocalConsoleDashboardReport()
    ev=[LocalConsoleDashboardEvidence(stage="Stage63",decision="READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW")]
    cards=[build_stage_status_card(ev),build_latest_validation_card({"status":"PASS"}),build_warning_blocking_stats_card(ev),build_manifest_hash_card(ev),build_scheduler_preview_card(),build_safety_boundary_card(),build_api_capability_card(),build_detail_filter_card()]
    assert all(c.read_only and c.dry_run_only and c.no_trade_authorization for c in cards)
    assert "/dashboard/overview" in DASHBOARD_ROUTES and "/dashboard/stage-status" in DASHBOARD_ROUTES and "/dashboard/latest-validation" in DASHBOARD_ROUTES

def test_decisions(tmp_path):
    r=run_local_console_dashboard_review(LocalConsoleDashboardConfig(repo_root=tmp_path))
    assert r.decision in {LocalConsoleDashboardDecision.NEED_MORE_EVIDENCE, LocalConsoleDashboardDecision.NO_GO}
    d=tmp_path/'local_console_detail_stage63'; d.mkdir(); (d/'local_console_detail_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW','summary':{'critical_count':0},'warnings':[]}),encoding='utf-8')
    r=run_local_console_dashboard_review(LocalConsoleDashboardConfig(repo_root=tmp_path))
    assert r.decision==LocalConsoleDashboardDecision.READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW
    (d/'local_console_detail_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':1}}),encoding='utf-8')
    assert run_local_console_dashboard_review(LocalConsoleDashboardConfig(repo_root=tmp_path)).decision==LocalConsoleDashboardDecision.NO_GO

def test_validation_decode_and_safety(tmp_path):
    p=tmp_path/'x.log'; p.write_bytes(b'\xff\xfeA\x00B\x00')
    txt,enc=decode_text_file_auto(p); assert '\x00' not in txt and not txt.startswith('\ufeff')
    log=tmp_path/'validation_logs'; log.mkdir(); (log/'stage64_validation_1.log').write_bytes(b'\xef\xbb\xbfOK\x00')
    d=read_latest_validation_detail(log); assert not d['contains_nul'] and not d['summary'].startswith('\ufeff')
    assert classify_local_console_dashboard_marker('xtquant.xtdata')=='INFO'
    assert classify_local_console_dashboard_marker('xttrader','docs/x.md',generated=True)=='WARN'
    assert classify_local_console_dashboard_marker('xttrader','qmt_ai_trading/x.py',executable=True)=='CRITICAL'
    assert scan_local_console_dashboard_text_for_forbidden_markers('place_order query_stock_asset','qmt_ai_trading/x.py',executable=True)[0]['severity']=='CRITICAL'

def test_formatter_and_cli(tmp_path):
    d=tmp_path/'local_console_detail_stage63'; d.mkdir(); (d/'local_console_detail_report.json').write_text(json.dumps({'decision':'READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW','summary':{'critical_count':0},'route_index':['/dashboard/detail'],'filter_index':{'warnings':1,'blocking_reasons':0}}),encoding='utf-8')
    out=tmp_path/'out'; r=run_local_console_dashboard_review(LocalConsoleDashboardConfig(repo_root=tmp_path, output_dir=out)); md=format_dashboard_report_md(r)
    assert '## Safety Note' in md and 'READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW 只表示' in md
    cmd=[sys.executable,'scripts/run_local_console_dashboard_review.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'local_console_dashboard_report.md'),'--json-output',str(out/'local_console_dashboard_report.json'),'--card-index-output',str(out/'dashboard_card_index.md'),'--card-index-json-output',str(out/'dashboard_card_index.json'),'--stage-cards-output',str(out/'stage_status_cards.md'),'--stage-cards-json-output',str(out/'stage_status_cards.json'),'--stats-output',str(out/'warning_blocking_stats.md'),'--stats-json-output',str(out/'warning_blocking_stats.json'),'--manifest-output',str(out/'manifest_hash_status.md'),'--manifest-json-output',str(out/'manifest_hash_status.json'),'--scheduler-output',str(out/'scheduler_preview_status.md'),'--scheduler-json-output',str(out/'scheduler_preview_status.json'),'--safety-output',str(out/'safety_boundary_status.md'),'--safety-json-output',str(out/'safety_boundary_status.json'),'--plan-output',str(out/'next_console_shell_plan.md'),'--plan-json-output',str(out/'next_console_shell_plan.json')]
    assert subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1]).returncode==0
    for name in ['local_console_dashboard_report.md','local_console_dashboard_report.json','dashboard_card_index.md','dashboard_card_index.json','stage_status_cards.md','stage_status_cards.json','warning_blocking_stats.md','warning_blocking_stats.json','manifest_hash_status.md','manifest_hash_status.json','scheduler_preview_status.md','scheduler_preview_status.json','safety_boundary_status.md','safety_boundary_status.json','next_console_shell_plan.md','next_console_shell_plan.json']:
        assert (out/name).exists()
