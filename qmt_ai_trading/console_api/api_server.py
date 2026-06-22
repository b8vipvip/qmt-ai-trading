from __future__ import annotations
import json, mimetypes
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from .safety import assert_localhost_bind, assert_http_method_allowed, ConsoleSafetyError
from .task_registry import list_tasks
from .task_store import TaskStore
from .task_runner import run_task
from .serializers import task_to_dict, run_to_dict
from qmt_ai_trading.ai_provider.model_discovery import discover_models, LATEST_DISCOVERY
from qmt_ai_trading.ai_provider.stress_test import run_stress_test, LATEST_BENCHMARK
from qmt_ai_trading.ai_provider.usage_mapping import save_usage_draft, get_usage_draft
from qmt_ai_trading.ai_provider.serializers import to_dict
from qmt_ai_trading.research.factor_registry import catalog_as_dict
from qmt_ai_trading.research.factor_config import config_seed_as_dict
from qmt_ai_trading.console_api.workflow_console import workflow_status, feature_matrix, reports_index, dry_run_check
from qmt_ai_trading.common.json_safe import json_safe
DEFAULT_HOST='127.0.0.1'; DEFAULT_PORT=8768
STORE=TaskStore()
LATEST_FACTOR_SCAN={'factor_results': [], 'factor_evaluation': {}, 'factor_candidates': []}
LATEST_FACTOR_STRATEGY={'strategy_signals': [], 'trade_intents': [], 'risk_decisions': [], 'strategy_report': {}}

def _read_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        return {'error':str(e),'read_only':True,'dry_run':True,'not_live_trading':True}

def _read_factor_file(name, default):
    return _read_json_file(Path('local_console_factor_stage79')/name, default)

def _read_artifact_file(name, default):
    path=Path('local_console_artifact_migration_stage87')/name
    if not path.exists():
        try:
            from qmt_ai_trading.common.artifact_migration import run_artifact_migration_stage87
            run_artifact_migration_stage87('.', 'local_console_artifact_migration_stage87')
        except Exception:
            pass
    return _read_json_file(path, default)

def _read_agent_file(name, default):
    path=Path('local_console_agent_stage81')/name
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: return {'error':str(e),'dry_run':True,'not_live_trading':True}

def _read_backtest_file(name, default):
    path=Path('local_console_backtest_stage82')/name
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: return {'error':str(e),'dry_run':True,'not_live_trading':True,'research_only':True}


def _read_monitoring_file(name, default):
    path=Path('local_console_monitoring_stage83')/name
    if not path.exists():
        try:
            from qmt_ai_trading.monitoring import run_monitoring_stage83
            run_monitoring_stage83('.', 'local_console_monitoring_stage83')
        except Exception:
            pass
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: return {'error':str(e),'dry_run':True,'not_live_trading':True,'research_only':True,'no_real_notification':True}


def _read_market_file(name, default):
    path=Path('local_console_market_stage84')/name
    if not path.exists():
        try:
            from qmt_ai_trading.market_gateway import run_market_gateway_stage84
            run_market_gateway_stage84('.', 'local_console_market_stage84')
        except Exception:
            pass
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: return {'error':str(e),'sandbox':True,'read_only':True,'not_live_trading':True,'no_qmt_trader_api':True}


def _read_xtdata_file(name, default):
    path=Path('local_console_xtdata_stage85')/name
    if not path.exists():
        try:
            from qmt_ai_trading.market_gateway import run_xtdata_boundary_stage85
            run_xtdata_boundary_stage85('.', 'local_console_xtdata_stage85')
        except Exception:
            pass
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: return {'error':str(e),'enabled':False,'dry_run':True,'read_only':True,'xtdata_imported':False,'mini_qmt_connected':False,'real_market_data':False,'sandbox_fallback':True}



def _read_xtdata_enable_file(name, default):
    path=Path('local_console_xtdata_enable_stage86')/name
    if not path.exists():
        try:
            from qmt_ai_trading.market_gateway import run_xtdata_enable_stage86
            run_xtdata_enable_stage86('.', 'local_console_xtdata_enable_stage86')
        except Exception:
            pass
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: return {'error':str(e),'enable_xtdata':False,'dry_run':True,'read_only':True,'xtdata_imported':False,'mini_qmt_connected':False,'real_market_data':False,'requires_human_review':True}




def _bool_param(qs, name, default=False):
    value = qs.get(name, [default])[0]
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}

def _split_symbols(value):
    if isinstance(value, list):
        if len(value) == 1 and isinstance(value[0], str):
            value = value[0]
        else:
            return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in value.split(',') if x.strip()]
    return ["510300.SH", "510500.SH", "588000.SH"]

def _xtdata_live_config_from_qs(qs):
    from qmt_ai_trading.market_gateway.xtdata_live_config import XtDataLiveReadOnlyConfig
    warnings=[]
    for forbidden in ("allow_xttrader", "allow_order_submit", "allow_account_query"):
        if _bool_param(qs, forbidden, False):
            warnings.append(f"{forbidden}=true is not accepted; forced to false for read-only xtdata mode")
    symbols = _split_symbols(qs.get('symbols', [None])[0] or qs.get('symbol', [None])[0] or "510300.SH,510500.SH,588000.SH")
    try:
        limit = max(1, min(int(qs.get('limit', [20])[0]), 500))
    except Exception:
        limit = 20
    cfg = XtDataLiveReadOnlyConfig(
        enabled=_bool_param(qs, 'enable_xtdata', False),
        allow_import_xtdata=_bool_param(qs, 'allow_import_xtdata', False),
        allow_real_market_data=_bool_param(qs, 'allow_real_market_data', False),
        allow_connect_miniqmt=_bool_param(qs, 'allow_connect_miniqmt', False),
        read_only=True,
        allow_xttrader=False,
        allow_account_query=False,
        allow_order_submit=False,
        symbols=symbols,
        period=str(qs.get('period', ['1d'])[0] or '1d'),
        limit=limit,
    )
    return cfg, warnings

def _with_xtdata_live_safety(payload, warnings=None):
    payload = dict(payload or {})
    payload.update({'read_only': True, 'allow_xttrader': False, 'allow_order_submit': False, 'allow_account_query': False, 'no_xttrader': True, 'no_order_submitted': True, 'no_account_query': True})
    payload['xtdata_imported'] = payload.get('import_status') == 'IMPORTED'
    payload.setdefault('mini_qmt_connected', bool(payload.get('real_market_data')))
    if payload.get('sandbox_fallback') and payload.get('status') == 'FALLBACK_TO_SANDBOX':
        payload.setdefault('error_message', payload.get('error') or payload.get('import_error') or payload.get('connection_error') or 'xtdata real readonly mode is disabled or unavailable; using sandbox fallback')
    if warnings:
        payload['warnings'] = list(payload.get('warnings', [])) + warnings
    return payload

def _xtdata_live_response(qs, kind):
    from qmt_ai_trading.market_gateway.xtdata_live_provider import XtDataLiveReadOnlyProvider
    cfg, warnings = _xtdata_live_config_from_qs(qs)
    provider = XtDataLiveReadOnlyProvider(cfg)
    if kind == 'status':
        payload = provider.get_status()
    elif kind == 'snapshots':
        payload = provider.get_snapshot(cfg.symbols)
    elif kind == 'bars':
        symbol = str(qs.get('symbol', [cfg.symbols[0]])[0] or cfg.symbols[0])
        payload = provider.get_bars(symbol, cfg.period, cfg.limit)
    elif kind == 'report':
        status = provider.get_status()
        payload = {'stage':'Stage87','task_id':'xtdata_live_readonly_smoke','provider':'xtdata_live_readonly', **status}
    else:
        payload = {}
    return json_safe(_with_xtdata_live_safety(payload, warnings))

def _read_xtdata_live_file(name, default):
    path=Path('local_console_xtdata_live_stage87')/name
    if not path.exists():
        try:
            from qmt_ai_trading.market_gateway import run_xtdata_live_stage87
            run_xtdata_live_stage87('.', 'local_console_xtdata_live_stage87')
        except Exception:
            pass
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: return {'error':str(e),'provider':'xtdata_live_readonly','read_only':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'not_live_trading':True,'real_market_data':False,'sandbox_fallback':True}

def _json(handler, code, payload):
    raw=json.dumps(json_safe(payload), ensure_ascii=False).encode('utf-8'); handler.send_response(code); handler.send_header('Content-Type','application/json; charset=utf-8'); handler.send_header('Content-Length',str(len(raw))); handler.end_headers(); handler.wfile.write(raw)
def summary():
    runs=STORE.list(); return {'title':'QMT AI 本地量化控制台','mode':'dry-run/shadow','read_only':True,'no_trade_authorization':True,'live_status':'实盘关闭','task_total':len(runs),'success_count':sum(r.status=='SUCCESS' for r in runs),'risk_block_count':1,'agent_report_count':sum(r.category=='AGENTS' for r in runs),'recent_signal_count':sum(len(r.output.get('signals',[])) for r in runs)}
def _latest_factor_output():
    for r in STORE.list():
        if r.task_id=='factor_scan' and r.output:
            return r.output
    return LATEST_FACTOR_SCAN
def _latest_strategy_output():
    for r in STORE.list():
        if r.task_id=='factor_strategy_dry_run' and r.output:
            return r.output
    return LATEST_FACTOR_STRATEGY
def reports(): return [{'name':'Stage77 dry-run 业务控制台摘要','type':'dry-run report','summary':'仅白名单摘要，不暴露 reports/logs 原始目录'},{'name':'Agent 投研结构化建议','type':'agent report','summary':'只输出 confidence/reasons/risk_flags，不下单'}]
def market_snapshot(qs): return {'symbol':qs.get('symbol',['510300.SH'])[0],'source':'local readonly/mock','time':'dry-run latest','ohlcv':{'open':3.91,'high':3.96,'low':3.88,'close':3.94,'volume':1200000},'quality_status':'OK','read_only':True}
def make_handler(static_dir=None):
    root=Path(static_dir).resolve() if static_dir else None
    class Handler(BaseHTTPRequestHandler):
        def _safe(self, fn):
            try: assert_http_method_allowed(self.command, urlparse(self.path).path); fn()
            except ConsoleSafetyError as e: _json(self, 403, {'ok':False,'status':'BLOCKED','error':str(e)})
            except Exception as e: _json(self, 500, {'ok':False,'status':'FAILED','error':str(e)})
        def do_GET(self): self._safe(self._get)
        def do_POST(self): self._safe(self._post)
        def do_PUT(self): self._safe(lambda: None)
        def do_PATCH(self): self._safe(lambda: None)
        def do_DELETE(self): self._safe(lambda: None)
        def _get(self):
            u=urlparse(self.path); p=u.path

            if p=='/api/v1/workflow/status': return _json(self,200,{'ok':True,**workflow_status('.')})
            if p=='/api/v1/workflow/feature-matrix': return _json(self,200,{'ok':True,**feature_matrix('.')})
            if p=='/api/v1/workflow/reports': return _json(self,200,{'ok':True,**reports_index('.')})
            if p=='/api/v1/datahub/status': return _json(self,200,{'ok':True,'status':'BACKEND_MISSING','module':'Data Hub','message':'Data Hub interactive API is not implemented yet','next_action':'Implement Data Hub read-only status and cache API','read_only':True,'not_live_trading':True})
            if p=='/api/v1/datahub/symbols': return _json(self,200,{'ok':True,'status':'BACKEND_MISSING','module':'Data Hub / symbols','symbols':[],'next_action':'后端待开发，需要新增 Data Hub symbols API','read_only':True,'not_live_trading':True})
            if p=='/api/v1/datahub/cache/status': return _json(self,200,{'ok':True,'status':'BACKEND_MISSING','module':'Data Hub / cache','next_action':'后端待开发，需要新增 Data Hub cache status API','read_only':True,'not_live_trading':True})
            if p=='/api/v1/datahub/market/latest': return _json(self,200,{'ok':True,'status':'BACKEND_MISSING','module':'Data Hub / market latest','next_action':'后端待开发，需要新增 Data Hub latest market API','read_only':True,'not_live_trading':True})
            if p=='/api/v1/strategy/context': return _json(self,200,{'ok':True,'context':{'module':'Strategy Engine','status':'INTERACTIVE','dry_run':True,'read_only':True,'no_order_submitted':True}})
            if p=='/api/v1/strategy/signals/latest': return _json(self,200,{'ok':True,'signals':_latest_strategy_output().get('strategy_signals',[])})
            if p=='/api/v1/strategy/trade-intents/latest': return _json(self,200,{'ok':True,'trade_intents':_latest_strategy_output().get('trade_intents',[])})
            if p=='/api/v1/risk/context': return _json(self,200,{'ok':True,'context':{'module':'Risk Gate','status':'INTERACTIVE','dry_run':True,'read_only':True,'no_order_submitted':True}})
            if p=='/api/v1/risk/decisions/latest': return _json(self,200,{'ok':True,'decisions':_latest_strategy_output().get('risk_decisions',[])})
            if p=='/api/v1/risk/report/latest': return _json(self,200,{'ok':True,'report':{'status':'INTERACTIVE','source':'risk_gate_dry_run','dry_run':True,'no_order_submitted':True}})
            if p=='/api/v1/approval/status': return _json(self,200,{'ok':True,'status':'BACKEND_MISSING','module':'Human Approval','message':'Human Approval read-only API is not implemented yet','next_action':'后端待开发，需要新增 approval status API','read_only':True,'not_live_trading':True})
            if p=='/api/v1/approval/requests/latest': return _json(self,200,{'ok':True,'status':'BACKEND_MISSING','requests':[],'next_action':'后端待开发，需要新增 approval requests API','read_only':True})
            if p=='/api/v1/paper-trading/status': return _json(self,200,{'ok':True,'status':'BACKEND_MISSING','module':'Paper Trading','next_action':'后端待开发，需要新增 paper trading status API','read_only':True,'not_live_trading':True})
            if p=='/api/v1/paper-trading/orders/latest': return _json(self,200,{'ok':True,'status':'BACKEND_MISSING','orders':[],'next_action':'后端待开发，需要新增 paper orders API','read_only':True})
            if p=='/api/v1/shadow-trading/report/latest': return _json(self,200,{'ok':True,'status':'BACKEND_MISSING','report':{},'next_action':'后端待开发，需要新增 shadow trading report API','read_only':True})
            if p=='/api/v1/live/status': return _json(self,200,{'ok':True,'status':'DISABLED','feature_status':'DISABLED_FOR_SAFETY','live_trading_enabled':False,'allow_order_submit':False,'allow_xttrader':False,'requires_human_approval':True,'message':'Live trading is disabled by default'})
            if p=='/api/v1/health': return _json(self,200,{'ok':True,'service':'console_api_stage77','host':'127.0.0.1','read_only':True,'dry_run':True,'no_trade_authorization':True,'live_disabled':True})
            if p=='/api/v1/tasks/catalog': return _json(self,200,{'ok':True,'tasks':[task_to_dict(t) for t in list_tasks()]})
            if p=='/api/v1/tasks': return _json(self,200,{'ok':True,'tasks':[run_to_dict(r) for r in STORE.list()]})
            if p.startswith('/api/v1/tasks/'):
                parts=p.split('/'); rid=parts[4] if len(parts)>4 else ''; run=STORE.get(rid)
                if not run: return _json(self,404,{'ok':False,'error':'任务不存在'})
                if len(parts)>5 and parts[5]=='logs': return _json(self,200,{'ok':True,'task_id':rid,'logs':run.logs[-50:]})
                return _json(self,200,{'ok':True,'task':run_to_dict(run)})
            if p=='/api/v1/reports': return _json(self,200,{'ok':True,'reports':reports()})
            if p=='/api/v1/market/snapshot': return _json(self,200,{'ok':True,'snapshot':market_snapshot(parse_qs(u.query))})
            if p=='/api/v1/console/summary': return _json(self,200,{'ok':True,'summary':summary()})
            if p=='/api/v1/factors/catalog': return _json(self,200,{'ok':True,'factors':catalog_as_dict()})
            if p=='/api/v1/factors/config': return _json(self,200,{'ok':True,'config':config_seed_as_dict()})
            if p=='/api/v1/factors/results': return _json(self,200,{'ok':True,'results':_latest_factor_output().get('factor_results',[])})
            if p=='/api/v1/factors/evaluation': return _json(self,200,{'ok':True,'evaluation':_latest_factor_output().get('factor_evaluation',{})})
            if p=='/api/v1/factors/candidates': return _json(self,200,{'ok':True,'candidates':_latest_factor_output().get('factor_candidates',[])})
            if p=='/api/v1/factor/context': return _json(self,200,{'ok':True,'context':_read_factor_file('factor_context.json',{'source_path':'local_console_factor_stage79/factor_context.json','read_only':True,'dry_run':True,'not_live_trading':True,'status':'DATA_MISSING'})})
            if p=='/api/v1/factor/candidates/latest': return _json(self,200,{'ok':True,'source_path':'local_console_factor_stage79/factor_candidates.json','candidates':_read_factor_file('factor_candidates.json',_latest_factor_output().get('factor_candidates',[]))})
            if p=='/api/v1/factor/report/latest': return _json(self,200,{'ok':True,'source_path':'local_console_factor_stage79/factor_report.json','report':_read_factor_file('factor_report.json',{'status':'DATA_MISSING','read_only':True,'dry_run':True,'not_live_trading':True})})
            if p=='/api/v1/strategy/factor-signals': return _json(self,200,{'ok':True,'signals':_latest_strategy_output().get('strategy_signals',[])})
            if p=='/api/v1/strategy/trade-intents': return _json(self,200,{'ok':True,'trade_intents':_latest_strategy_output().get('trade_intents',[])})
            if p=='/api/v1/strategy/risk-decisions': return _json(self,200,{'ok':True,'risk_decisions':_latest_strategy_output().get('risk_decisions',[])})
            if p=='/api/v1/strategy/report': return _json(self,200,{'ok':True,'report':_latest_strategy_output().get('strategy_report',{})})
            if p=='/api/v1/agents/context': return _json(self,200,{'ok':True,'context':_read_agent_file('agent_context.json',{'dry_run':True,'not_live_trading':True,'research_only':True})})
            if p=='/api/v1/agents/model-usage': return _json(self,200,{'ok':True,'model_usage':_read_agent_file('agent_model_usage.json',{'fallback_used':True,'mappings':{}})})
            if p=='/api/v1/agents/runs/latest': return _json(self,200,{'ok':True,'runs':_read_agent_file('agent_runs.json',[])})
            if p=='/api/v1/agents/debate/latest': return _json(self,200,{'ok':True,'debate':_read_agent_file('agent_debate.json',{})})
            if p=='/api/v1/agents/risk-review/latest': return _json(self,200,{'ok':True,'risk_review':_read_agent_file('agent_risk_review.json',{})})
            if p=='/api/v1/agents/portfolio-review/latest': return _json(self,200,{'ok':True,'portfolio_review':_read_agent_file('agent_portfolio_review.json',{})})
            if p=='/api/v1/agents/report/latest': return _json(self,200,{'ok':True,'report':_read_agent_file('agent_research_report.json',{})})
            if p=='/api/v1/backtest/context': return _json(self,200,{'ok':True,'context':_read_backtest_file('backtest_input_context.json',{'dry_run':True,'not_live_trading':True,'research_only':True,'fallback_used':True})})
            if p=='/api/v1/backtest/shadow-replay/latest': return _json(self,200,{'ok':True,'shadow_replay':_read_backtest_file('shadow_replay_result.json',{})})
            if p=='/api/v1/backtest/performance/latest': return _json(self,200,{'ok':True,'performance':_read_backtest_file('performance_metrics.json',{})})
            if p=='/api/v1/backtest/attribution/latest': return _json(self,200,{'ok':True,'attribution':_read_backtest_file('performance_attribution.json',{})})
            if p=='/api/v1/backtest/agent-comparison/latest': return _json(self,200,{'ok':True,'agent_comparison':_read_backtest_file('agent_backtest_comparison.json',{})})
            if p=='/api/v1/backtest/report/latest': return _json(self,200,{'ok':True,'report':_read_backtest_file('backtest_dashboard_report.json',{})})
            if p=='/api/v1/monitoring/context': return _json(self,200,{'ok':True,'context':_read_monitoring_file('monitoring_input_context.json',{'dry_run':True,'not_live_trading':True,'research_only':True})})
            if p=='/api/v1/monitoring/alerts/latest': return _json(self,200,{'ok':True,'alerts':_read_monitoring_file('monitoring_alerts.json',{'alerts':[]})})
            if p=='/api/v1/monitoring/circuit-breaker/latest': return _json(self,200,{'ok':True,'circuit_breaker':_read_monitoring_file('circuit_breaker_status.json',{})})
            if p=='/api/v1/monitoring/risk-events/latest': return _json(self,200,{'ok':True,'risk_events':_read_monitoring_file('risk_event_timeline.json',{'events':[]})})
            if p=='/api/v1/monitoring/system-health/latest': return _json(self,200,{'ok':True,'system_health':_read_monitoring_file('system_health_report.json',{})})
            if p=='/api/v1/monitoring/report/latest': return _json(self,200,{'ok':True,'report':_read_monitoring_file('system_health_report.json',{})})
            if p=='/api/v1/market/sandbox/context': return _json(self,200,{'ok':True,'context':_read_market_file('market_input_context.json',{'sandbox':True,'read_only':True,'not_live_trading':True})})
            if p=='/api/v1/market/sandbox/symbols': return _json(self,200,{'ok':True,'symbols':_read_market_file('market_symbols.json',{'symbols':[]})})
            if p=='/api/v1/market/sandbox/snapshots': return _json(self,200,{'ok':True,'snapshots':_read_market_file('market_snapshots.json',{'snapshots':[]})})
            if p=='/api/v1/market/sandbox/bars': return _json(self,200,{'ok':True,'bars':_read_market_file('market_bars.json',{'bars':[]})})
            if p=='/api/v1/market/sandbox/replay/latest': return _json(self,200,{'ok':True,'replay':_read_market_file('replay_events.json',{'events':[]})})
            if p=='/api/v1/market/sandbox/quality/latest': return _json(self,200,{'ok':True,'quality':_read_market_file('market_data_quality.json',{})})
            if p=='/api/v1/market/sandbox/report/latest': return _json(self,200,{'ok':True,'report':_read_market_file('market_gateway_report.json',{})})
            if p=='/api/v1/market/xtdata/context': return _json(self,200,{'ok':True,'context':_read_xtdata_file('xtdata_input_context.json',{'enabled':False,'dry_run':True,'read_only':True})})
            if p=='/api/v1/market/xtdata/config': return _json(self,200,{'ok':True,'config':_read_xtdata_file('xtdata_adapter_config.json',{})})
            if p=='/api/v1/market/xtdata/import-guard': return _json(self,200,{'ok':True,'import_guard':_read_xtdata_file('xtdata_import_guard_report.json',{})})
            if p=='/api/v1/market/xtdata/capability-probe': return _json(self,200,{'ok':True,'capability_probe':_read_xtdata_file('xtdata_capability_probe.json',{})})
            if p=='/api/v1/market/xtdata/safety': return _json(self,200,{'ok':True,'safety':_read_xtdata_file('xtdata_safety_report.json',{})})
            if p=='/api/v1/market/xtdata/report': return _json(self,200,{'ok':True,'report':_read_xtdata_file('xtdata_boundary_report.json',{})})
            if p=='/api/v1/xtdata/boundary/report': return _json(self,200,{'ok':True,'report':_read_xtdata_file('xtdata_boundary_report.json',{})})

            if p=='/api/v1/market/xtdata-enable/context': return _json(self,200,{'ok':True,'context':_read_xtdata_enable_file('xtdata_enable_input_context.json',{'enable_xtdata':False,'dry_run':True,'read_only':True})})
            if p=='/api/v1/market/xtdata-enable/request': return _json(self,200,{'ok':True,'request':_read_xtdata_enable_file('xtdata_enable_request.json',{})})
            if p=='/api/v1/market/xtdata-enable/environment': return _json(self,200,{'ok':True,'environment':_read_xtdata_enable_file('xtdata_environment_check.json',{})})
            if p=='/api/v1/market/xtdata-enable/checklist': return _json(self,200,{'ok':True,'checklist':_read_xtdata_enable_file('xtdata_manual_checklist.json',{})})
            if p=='/api/v1/market/xtdata-enable/audit': return _json(self,200,{'ok':True,'audit':_read_xtdata_enable_file('xtdata_config_audit.json',{})})
            if p=='/api/v1/market/xtdata-enable/decision': return _json(self,200,{'ok':True,'decision':_read_xtdata_enable_file('xtdata_enable_decision.json',{})})
            if p=='/api/v1/market/xtdata-enable/report': return _json(self,200,{'ok':True,'report':_read_xtdata_enable_file('xtdata_enable_report.json',{})})
            if p=='/api/v1/xtdata-enable/report': return _json(self,200,{'ok':True,'report':_read_xtdata_enable_file('xtdata_enable_report.json',{})})
            if p=='/api/v1/market/xtdata-live/status': return _json(self,200,{'ok':True,'status':_xtdata_live_response(parse_qs(u.query),'status')})
            if p=='/api/v1/market/xtdata-live/snapshots': return _json(self,200,{'ok':True,'snapshots':_xtdata_live_response(parse_qs(u.query),'snapshots')})
            if p=='/api/v1/xtdata-live/status': return _json(self,200,{'ok':True,'status':_xtdata_live_response(parse_qs(u.query),'status')})
            if p=='/api/v1/xtdata-live/snapshots': return _json(self,200,{'ok':True,'snapshots':_xtdata_live_response(parse_qs(u.query),'snapshots')})
            if p=='/api/v1/market/xtdata-live/bars': return _json(self,200,{'ok':True,'bars':_xtdata_live_response(parse_qs(u.query),'bars')})
            if p=='/api/v1/market/xtdata-live/safety': return _json(self,200,{'ok':True,'safety':_read_xtdata_live_file('xtdata_live_safety_report.json',{})})
            if p=='/api/v1/market/xtdata-live/report': return _json(self,200,{'ok':True,'report':_xtdata_live_response(parse_qs(u.query),'report')})
            if p=='/api/v1/artifacts/migration/report': return _json(self,200,{'ok':True,'report':_read_artifact_file('artifact_migration_report.json',{})})
            if p=='/api/v1/artifacts/registry': return _json(self,200,{'ok':True,'registry':_read_artifact_file('artifact_registry.json',{})})
            if p=='/api/v1/ai/models/latest': return _json(self,200,{'ok':True,'result':LATEST_DISCOVERY})
            if p=='/api/v1/ai/benchmark/latest': return _json(self,200,{'ok':True,'report':LATEST_BENCHMARK})
            if p=='/api/v1/ai/model-usage/draft': return _json(self,200,{'ok':True,'draft':get_usage_draft()})
            return self._static(p)
        def _post(self):
            raw=self.rfile.read(int(self.headers.get('Content-Length','0') or 0))
            body=json.loads(raw.decode('utf-8') or '{}')
            p=urlparse(self.path).path
            if p=='/api/v1/tasks/run':
                params={**{k:v for k,v in body.items() if k!='task_id' and k!='params'}, **body.get('params',{})}; run=run_task(body.get('task_id',''), params, STORE); payload=run_to_dict(run); payload.update(run.output if isinstance(run.output,dict) else {}); return _json(self,200,{'ok':True,'task':payload})
            if p=='/api/v1/ai/models/discover':
                res=discover_models(body.get('provider_type','openai_compatible'), body.get('base_url',''), body.get('api_key',''), int(body.get('timeout_seconds',60))); return _json(self,200,{'ok':res.success,'result':to_dict(res)})
            if p=='/api/v1/ai/models/stress-test':
                rep=run_stress_test(body.get('provider_type','openai_compatible'), body.get('base_url',''), body.get('api_key',''), body.get('selected_models',[]), body.get('test_sizes',[1000,3000,5000]), int(body.get('timeout_seconds',90)), body.get('endpoint_type','chat_completions')); return _json(self,200,{'ok':True,'report':to_dict(rep)})
            if p=='/api/v1/ai/model-usage/draft':
                return _json(self,200,{'ok':True,'draft':save_usage_draft(body.get('mappings',{}))})
            return _json(self,404,{'ok':False,'error':'not found'})
        def _static(self,p):
            if not root: return _json(self,404,{'ok':False,'error':'not found'})
            target=(root / ('index.html' if p=='/' else p.lstrip('/'))).resolve()
            if not str(target).startswith(str(root)) or not target.exists() or target.is_dir(): return _json(self,404,{'ok':False,'error':'not found'})
            data=target.read_bytes(); self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(str(target))[0] or 'application/octet-stream'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        def log_message(self, fmt,*args): return
    return Handler
def run_server(host=DEFAULT_HOST, port=DEFAULT_PORT, static_dir=None):
    assert_localhost_bind(host); HTTPServer((host,port), make_handler(static_dir)).serve_forever()
