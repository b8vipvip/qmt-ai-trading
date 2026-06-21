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
DEFAULT_HOST='127.0.0.1'; DEFAULT_PORT=8768
STORE=TaskStore()
LATEST_FACTOR_SCAN={'factor_results': [], 'factor_evaluation': {}, 'factor_candidates': []}
LATEST_FACTOR_STRATEGY={'strategy_signals': [], 'trade_intents': [], 'risk_decisions': [], 'strategy_report': {}}
def _json(handler, code, payload):
    raw=json.dumps(payload, ensure_ascii=False).encode('utf-8'); handler.send_response(code); handler.send_header('Content-Type','application/json; charset=utf-8'); handler.send_header('Content-Length',str(len(raw))); handler.end_headers(); handler.wfile.write(raw)
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
            if p=='/api/v1/strategy/factor-signals': return _json(self,200,{'ok':True,'signals':_latest_strategy_output().get('strategy_signals',[])})
            if p=='/api/v1/strategy/trade-intents': return _json(self,200,{'ok':True,'trade_intents':_latest_strategy_output().get('trade_intents',[])})
            if p=='/api/v1/strategy/risk-decisions': return _json(self,200,{'ok':True,'risk_decisions':_latest_strategy_output().get('risk_decisions',[])})
            if p=='/api/v1/strategy/report': return _json(self,200,{'ok':True,'report':_latest_strategy_output().get('strategy_report',{})})
            if p=='/api/v1/ai/models/latest': return _json(self,200,{'ok':True,'result':LATEST_DISCOVERY})
            if p=='/api/v1/ai/benchmark/latest': return _json(self,200,{'ok':True,'report':LATEST_BENCHMARK})
            if p=='/api/v1/ai/model-usage/draft': return _json(self,200,{'ok':True,'draft':get_usage_draft()})
            return self._static(p)
        def _post(self):
            raw=self.rfile.read(int(self.headers.get('Content-Length','0') or 0))
            body=json.loads(raw.decode('utf-8') or '{}')
            p=urlparse(self.path).path
            if p=='/api/v1/tasks/run':
                run=run_task(body.get('task_id',''), body.get('params',{}), STORE); return _json(self,200,{'ok':True,'task':run_to_dict(run)})
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
