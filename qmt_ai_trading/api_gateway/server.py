from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from functools import partial
from .handlers import handle_request
DEFAULT_HOST='127.0.0.1'; DEFAULT_PORT=8765
def validate_host(host): return host in {'127.0.0.1','localhost'}
def make_handler(repo_root='.'):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, payload):
            raw=json.dumps(payload,ensure_ascii=False).encode('utf-8'); self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
        def do_GET(self): code,payload=handle_request(self.path,'GET',repo_root); self._send(code,payload)
        def do_POST(self): code,payload=handle_request(self.path,'POST',repo_root); self._send(code,payload)
        def do_PUT(self): code,payload=handle_request(self.path,'PUT',repo_root); self._send(code,payload)
        def do_PATCH(self): code,payload=handle_request(self.path,'PATCH',repo_root); self._send(code,payload)
        def do_DELETE(self): code,payload=handle_request(self.path,'DELETE',repo_root); self._send(code,payload)
        def log_message(self, fmt, *args): return
    return Handler
def run_server(repo_root='.', host=DEFAULT_HOST, port=DEFAULT_PORT):
    if not validate_host(host): raise ValueError('Stage61 API Gateway refuses non-localhost host')
    httpd=HTTPServer((host,port), make_handler(repo_root)); httpd.serve_forever()
