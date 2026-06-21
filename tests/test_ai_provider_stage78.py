from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import json, pytest
from qmt_ai_trading.ai_provider.safety import *
from qmt_ai_trading.ai_provider.model_discovery import discover_models
from qmt_ai_trading.ai_provider.stress_test import run_stress_test
from qmt_ai_trading.ai_provider.serializers import to_dict

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('/v1/models') or self.path.endswith('/models'):
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps({'data':[{'id':'b-model','owned_by':'u'},{'id':'a-model','created':1}]}).encode())
        else: self.send_response(404); self.end_headers()
    def do_POST(self):
        self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps({'choices':[{'message':{'content':'摘要 JSON 理解成功'}}],'usage':{'total_tokens':12}}).encode())
    def log_message(self,*a): pass
@pytest.fixture
def server():
    s=HTTPServer(('127.0.0.1',0),H); t=Thread(target=s.serve_forever,daemon=True); t.start(); yield f'http://127.0.0.1:{s.server_port}'; s.shutdown()

def test_mask_api_key_no_full_leak():
    k='dummy-stage78-long-key'; assert k not in mask_api_key(k) and mask_api_key(k).startswith('dumm')
def test_discovery_v1_models(server):
    r=discover_models('openai_compatible',server+'/v1','dummy-stage78-key'); assert r.success and [m.model_id for m in r.models]==['a-model','b-model']
def test_discovery_models_fallback_and_parse(server):
    r=discover_models('openai_compatible',server,'dummy-stage78-key'); assert r.success and r.model_count==2 and r.models[0].supports_chat
def test_limits_and_safe_sizes():
    with pytest.raises(AiProviderSafetyError): assert_safe_selected_models(['m']*6)
    with pytest.raises(AiProviderSafetyError): assert_safe_test_sizes([999])
    with pytest.raises(AiProviderSafetyError): assert_stress_test_limits(['m']*5,[1000,3000,5000,1000])
def test_report_no_api_key_and_masked_key(server):
    key='dummy-stage78-key-value'; rep=run_stress_test('openai_compatible',server+'/v1',key,['a-model'],[1000],10); d=to_dict(rep); txt=json.dumps(d,ensure_ascii=False); assert key not in txt and mask_api_key(key) in txt and d['summary']['total']==1
