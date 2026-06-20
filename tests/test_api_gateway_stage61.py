from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.api_gateway.models import ApiGatewayConfig, ApiGatewayReport, ApiGatewayDecision
from qmt_ai_trading.api_gateway.service import build_route_index, run_api_gateway_review
from qmt_ai_trading.api_gateway.safety import classify_api_gateway_route, scan_api_gateway_text_for_forbidden_markers
from qmt_ai_trading.api_gateway.handlers import handle_request
from qmt_ai_trading.api_gateway.server import DEFAULT_HOST, validate_host, make_handler
from qmt_ai_trading.api_gateway.formatters import format_api_gateway_report_md

def test_defaults():
    assert ApiGatewayConfig().read_only is True
    assert ApiGatewayReport().decision == ApiGatewayDecision.NEED_MORE_EVIDENCE

def test_missing_stage60_no_crash(tmp_path):
    r=run_api_gateway_review(ApiGatewayConfig(repo_root=tmp_path, pre_gray_final_review_dir='missing'))
    assert r.decision in {ApiGatewayDecision.NEED_MORE_EVIDENCE, ApiGatewayDecision.NO_GO}

def test_stage60_ready_allows_ready(tmp_path):
    d=tmp_path/'pre_gray_final_review_stage60'; d.mkdir(); (d/'pre_gray_final_review.json').write_text(json.dumps({'decision':'READY_FOR_PRE_GRAY_FINAL_REVIEW','summary':{'critical_count':0}}),encoding='utf-8')
    assert run_api_gateway_review(ApiGatewayConfig(repo_root=tmp_path)).decision == ApiGatewayDecision.READY_FOR_API_GATEWAY_REVIEW

def test_stage60_no_go_blocks(tmp_path):
    d=tmp_path/'pre_gray_final_review_stage60'; d.mkdir(); (d/'pre_gray_final_review.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':1}}),encoding='utf-8')
    assert run_api_gateway_review(ApiGatewayConfig(repo_root=tmp_path)).decision == ApiGatewayDecision.NO_GO

def test_route_index_required():
    paths={e.path for e in build_route_index().endpoints}
    for p in ['/health','/api/v1/capabilities','/api/v1/safety-boundary','/api/v1/reports/stage60','/api/v1/reports/stage59','/api/v1/reports/stage58','/api/v1/reports/stage57','/api/v1/reports/stage56','/api/v1/reports/stage55']:
        assert p in paths

def test_forbidden_routes():
    for m,p in [('POST','/order'),('POST','/trade'),('POST','/approve'),('GET','/account'),('GET','/positions'),('GET','/orders')]:
        assert classify_api_gateway_route(p,m).forbidden
        code,payload=handle_request(p,m,'.')
        assert code in {403,405} and payload['read_only'] and payload['dry_run_only'] and payload['no_trade_authorization'] and 'forbidden route' in payload['blocking_reasons']

def test_api_response_flags_and_host():
    code,payload=handle_request('/health','GET','.')
    assert code==200 and payload['read_only'] and payload['dry_run_only'] and payload['no_trade_authorization']
    assert DEFAULT_HOST=='127.0.0.1'; assert validate_host('localhost'); assert not validate_host('0.0.0.0')

def test_markers_contexts():
    crit=scan_api_gateway_text_for_forbidden_markers('xttrader XtQuantTrader place_order query_stock_asset', 'qmt_ai_trading/api_gateway/server.py')
    assert all(x['severity']=='CRITICAL' for x in crit)
    warn=scan_api_gateway_text_for_forbidden_markers('不调用 xttrader forbidden marker definitions', 'docs/stage60.md', generated=True)
    assert warn and all(x['severity']=='WARN' for x in warn)
    assert scan_api_gateway_text_for_forbidden_markers('xtdata xtquant.xtdata', 'code.py') == []

def test_formatter_safety_note():
    md=format_api_gateway_report_md(ApiGatewayReport(decision=ApiGatewayDecision.READY_FOR_API_GATEWAY_REVIEW))
    assert '## Safety Note' in md and 'READY_FOR_API_GATEWAY_REVIEW 只表示 API Gateway 基础层材料可供人工复核' in md

def test_cli_generates_all(tmp_path):
    out=tmp_path/'api_gateway_stage61'
    cmd=[sys.executable,'scripts/run_api_gateway_review.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'api_gateway_report.md'),'--json-output',str(out/'api_gateway_report.json'),'--route-output',str(out/'route_index.md'),'--route-json-output',str(out/'route_index.json'),'--safety-output',str(out/'safety_boundary.md'),'--safety-json-output',str(out/'safety_boundary.json'),'--stage-status-output',str(out/'stage_status.md'),'--stage-status-json-output',str(out/'stage_status.json'),'--plan-output',str(out/'next_ui_dashboard_plan.md'),'--plan-json-output',str(out/'next_ui_dashboard_plan.json')]
    assert subprocess.run(cmd,cwd=Path.cwd()).returncode==0
    for n in ['api_gateway_report.md','api_gateway_report.json','route_index.md','route_index.json','safety_boundary.md','safety_boundary.json','stage_status.md','stage_status.json','next_ui_dashboard_plan.md','next_ui_dashboard_plan.json']:
        assert (out/n).exists()

def test_server_dry_run_constructs_handler():
    assert make_handler('.') is not None
    assert subprocess.run([sys.executable,'scripts/run_api_gateway.py','--repo-root','.','--host','127.0.0.1','--port','8765','--dry-run']).returncode==0

def test_docs_and_validation_rules():
    roadmap=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in roadmap
    assert 'Stage61-75 前端 UI 产品化计划' in roadmap
    for s in ['UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能直接访问 QMT','UI 不能自动 approve']:
        assert s in roadmap
    assert not list(Path('scripts').glob('validate_stage60.ps1.bak_stage60fix_*'))
    v=Path('scripts/validate_stage61.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in v
    assert 'Print-File' in v and 'Check-NoBackup' in v
