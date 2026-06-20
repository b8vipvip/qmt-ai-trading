from __future__ import annotations
import json, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from .preview_models import LocalConsolePreviewConfig
from .preview_safety import assert_no_public_bind, classify_preview_route
FILES={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/style.css':'style.css','/data_bundle.json':'data_bundle.json','/binding_manifest.json':'binding_manifest.json','/data_source_map.json':'data_source_map.json','/static_data_safety.json':'static_data_safety.json'}
def run_preview_server_once(config: LocalConsolePreviewConfig):
    if not assert_no_public_bind(config.host): raise ValueError('Stage67 preview server only binds 127.0.0.1')
    static=Path(config.repo_root)/config.static_dir
    class H(BaseHTTPRequestHandler):
        def _send(self, head=False):
            c=classify_preview_route(self.path,self.command)
            if c['forbidden'] or self.path.split('?')[0] not in list(FILES)+['/health','/preview-safety','/preview-manifest']:
                self.send_response(405 if self.command not in ('GET','HEAD') else 404); self.end_headers(); return
            p=self.path.split('?')[0]
            if p=='/health': body=b'{"status":"PASS","read_only":true}'
            elif p=='/preview-safety': body=json.dumps({'read_only':True,'dry_run_only':True,'no_trade_authorization':True},ensure_ascii=False).encode()
            elif p=='/preview-manifest': body=json.dumps({'routes':list(FILES)},ensure_ascii=False).encode()
            else:
                f=static/FILES[p]; body=f.read_bytes() if f.exists() else b''
                if not f.exists(): self.send_response(404); self.end_headers(); return
            self.send_response(200); self.end_headers();
            if not head: self.wfile.write(body)
        def do_GET(self): self._send(False)
        def do_HEAD(self): self._send(True)
        def do_POST(self): self.send_response(405); self.end_headers()
        do_PUT=do_PATCH=do_DELETE=do_POST
        def log_message(self,*a): pass
    httpd=ThreadingHTTPServer((config.host,config.port),H)
    th=threading.Thread(target=httpd.serve_forever,daemon=True); th.start(); time.sleep(min(config.timeout_seconds,5)); httpd.shutdown(); th.join(timeout=2); return True
