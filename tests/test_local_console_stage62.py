from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.local_console.models import *
from qmt_ai_trading.local_console.service import *
from qmt_ai_trading.local_console.console_index import build_console_route_index, build_console_report_list, build_console_safety_boundary
from qmt_ai_trading.local_console.safety import classify_local_console_route, scan_local_console_text_for_forbidden_markers
from qmt_ai_trading.local_console.reader import read_console_json, read_latest_validation_summary
from qmt_ai_trading.local_console.formatters import format_local_console_report_md

def test_defaults():
    assert LocalConsoleConfig().read_only is True
    assert LocalConsoleReport().decision == LocalConsoleDecision.NEED_MORE_EVIDENCE

def test_missing_stage61_no_crash(tmp_path):
    r=run_local_console_review(LocalConsoleConfig(repo_root=tmp_path, api_gateway_dir='missing'))
    assert r.decision in {LocalConsoleDecision.NEED_MORE_EVIDENCE, LocalConsoleDecision.NO_GO}

def test_stage61_ready_allows_ready(tmp_path):
    d=tmp_path/'api_gateway_stage61'; d.mkdir(); (d/'api_gateway_report.json').write_text(json.dumps({'decision':'READY_FOR_API_GATEWAY_REVIEW','summary':{'critical_count':0}}),encoding='utf-8')
    assert run_local_console_review(LocalConsoleConfig(repo_root=tmp_path)).decision == LocalConsoleDecision.READY_FOR_LOCAL_CONSOLE_REVIEW

def test_stage61_no_go_blocks(tmp_path):
    d=tmp_path/'api_gateway_stage61'; d.mkdir(); (d/'api_gateway_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':1}}),encoding='utf-8')
    assert run_local_console_review(LocalConsoleConfig(repo_root=tmp_path)).decision == LocalConsoleDecision.NO_GO

def test_routes_and_reports_and_safety():
    paths={r.path for r in build_console_route_index()}
    for p in ['/dashboard','/reports','/manifest','/validation/latest','/safety','/api-capabilities','/scheduler-preview']+[f'/reports/stage{i}' for i in range(55,62)]: assert p in paths
    stages={x.stage for x in build_console_report_list()}; assert all(f'Stage{i}' in stages for i in range(55,62))
    b=build_console_safety_boundary(); txt=' '.join(b.items); assert 'read_only=True' in txt and 'dry_run_only=True' in txt and 'no_trade_authorization=True' in txt

def test_forbidden_console_routes():
    for p in ['/order','/orders','/trade','/execute','/approve','/live','/notify','/account','/positions','/assets']:
        assert classify_local_console_route(p,'GET').forbidden
        assert classify_local_console_route('/dashboard','POST').forbidden

def test_reader_sensitive_and_latest(tmp_path):
    assert read_console_json(tmp_path/'.env').status == LocalConsoleStatus.FAIL
    for n in ['token.json','key.json','secret.json','credential.json']:
        assert read_console_json(tmp_path/n).status == LocalConsoleStatus.FAIL
    d=tmp_path/'validation_logs'; d.mkdir(); (d/'stage62_validation_1.log').write_text('old',encoding='utf-8'); (d/'stage62_validation_2.log').write_text('new',encoding='utf-8')
    ev=read_latest_validation_summary(d); assert ev.metadata['latest_only'] is True and ev.status==LocalConsoleStatus.PASS

def test_marker_contexts():
    warn=scan_local_console_text_for_forbidden_markers('forbidden marker definitions 不调用 xttrader place_order','docs/stage62.md',generated=True)
    assert warn and all(x['severity']=='WARN' for x in warn)
    warn2=scan_local_console_text_for_forbidden_markers('不调用 xttrader','api_gateway_stage61/api_gateway_report.json',generated=True)
    assert warn2 and all(x['severity']=='WARN' for x in warn2)
    crit=scan_local_console_text_for_forbidden_markers('xttrader XtQuantTrader place_order query_stock_asset','qmt_ai_trading/live.py')
    assert crit and all(x['severity']=='CRITICAL' for x in crit)
    assert scan_local_console_text_for_forbidden_markers('xtdata xtquant.xtdata','code.py') == []

def test_formatter_safety_note():
    md=format_local_console_report_md(LocalConsoleReport(decision=LocalConsoleDecision.READY_FOR_LOCAL_CONSOLE_REVIEW))
    assert '## Safety Note' in md and 'READY_FOR_LOCAL_CONSOLE_REVIEW 只表示本地控制台报告读取层材料可供人工复核' in md

def test_cli_generates_all(tmp_path):
    out=tmp_path/'local_console_stage62'; d=tmp_path/'api_gateway_stage61'; d.mkdir(); (d/'api_gateway_report.json').write_text(json.dumps({'decision':'READY_FOR_API_GATEWAY_REVIEW','summary':{'critical_count':0}}),encoding='utf-8')
    cmd=[sys.executable,'scripts/run_local_console_review.py','--repo-root',str(tmp_path),'--output-dir',str(out)]
    assert subprocess.run(cmd,cwd=Path.cwd()).returncode==0
    for n in ['local_console_report.md','local_console_report.json','console_index.md','console_index.json','report_list.md','report_list.json','console_safety.md','console_safety.json','next_console_detail_plan.md','next_console_detail_plan.json']:
        assert (out/n).exists()

def test_pipeline_and_register_options(tmp_path):
    out=tmp_path/'lc'
    r=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'market_data_test_stage62'),'--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-review','--local-console-review-output-dir',str(out)],cwd=Path.cwd(),timeout=120)
    assert r.returncode==0 and (out/'local_console_report.md').exists()
    out2=tmp_path/'lc2'
    r=subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--warmup-universe','--warmup-provider','mock','--universe-lookback-days','90','--warmup-frequency','1d','--cache-root',str(tmp_path/'market_data_test_stage62'),'--data-source-mode','cached_real_first','--research-start','2026-03-21','--research-end','2026-06-18','--research-frequency','1d','--min-bars','40','--cached-strategy-top-n','2','--enable-local-console-review','--local-console-review-output-dir',str(out2)],cwd=Path.cwd(),timeout=120)
    assert r.returncode==0 and (out2/'local_console_report.md').exists()
    r=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-local-console-review','--local-console-review-output-dir','local_console','--time','15:30'],cwd=Path.cwd(),capture_output=True,text=True)
    assert r.returncode==0 and 'Stage62 Local Console Review' in r.stdout and 'no_task_registered=True' in r.stdout

def test_docs_validation_gitignore_rules():
    assert 'validation_logs/' in Path('.gitignore').read_text(encoding='utf-8')
    assert not list(Path('scripts').glob('validate_stage61.ps1.bak_stage61fix_*'))
    roadmap=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    for s in ['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61-75 前端 UI 产品化计划','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能直接访问 QMT','UI 不能自动 approve']:
        assert s in roadmap
    v=Path('scripts/validate_stage62.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v and 'Print-File' in v and 'Check-NoBackup' in v
    assert '\\`' not in v
