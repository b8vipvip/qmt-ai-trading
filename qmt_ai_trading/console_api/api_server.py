from __future__ import annotations
import json, mimetypes
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from .safety import assert_localhost_bind, assert_http_method_allowed, ConsoleSafetyError
from .task_registry import list_tasks
from .task_store import TaskStore
from .task_runner import run_task
from .serializers import task_to_dict, run_to_dict
from .routes import ROUTES
from .routes.common import payload
from qmt_ai_trading.common.json_safe import json_safe

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8768
STORE = TaskStore()


def _json(handler, code, data):
    raw = json.dumps(json_safe(data), ensure_ascii=False).encode('utf-8')
    handler.send_response(code)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _coerce(value):
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {'true', '1', 'yes', 'on'}:
            return True
        if v in {'false', '0', 'no', 'off'}:
            return False
    return value


def _int_param(query, name, default=50, maximum=200):
    try:
        raw = (query.get(name) or [default])[0]
        return min(max(0, int(raw)), maximum)
    except Exception:
        return default


def _summary():
    runs = STORE.list()
    return payload(
        summary={
            'title': 'QMT AI 统一本地量化控制台',
            'mode': 'dry-run/shadow/read-only',
            'task_total': len(runs),
            'success_count': sum(r.status == 'SUCCESS' for r in runs),
            'live_status': 'DISABLED_FOR_SAFETY',
        }
    )


def _task_history(limit=50):
    all_runs = STORE.list()
    runs = STORE.list(limit)
    success_count = sum(r.status == 'SUCCESS' for r in all_runs)
    failed_count = sum(r.status not in {'SUCCESS', 'RUNNING', 'PENDING'} for r in all_runs)
    running_count = sum(r.status == 'RUNNING' for r in all_runs)
    latest = all_runs[0] if all_runs else None
    return payload(
        status='READY',
        feature_status='TASK_HISTORY_READY',
        history_mode='in_memory_current_api_process',
        run_count=len(runs),
        total_run_count=len(all_runs),
        success_count=success_count,
        failed_count=failed_count,
        running_count=running_count,
        latest_run_id=getattr(latest, 'run_id', None),
        latest_task_id=getattr(latest, 'task_id', None),
        latest_finished_at=getattr(latest, 'finished_at', None),
        runs=[run_to_dict(r) for r in runs],
    )


def make_handler(static_dir=None):
    root = Path(static_dir).resolve() if static_dir else None

    class Handler(BaseHTTPRequestHandler):
        def _safe(self, fn):
            try:
                assert_http_method_allowed(self.command, urlparse(self.path).path)
                fn()
            except ConsoleSafetyError as e:
                _json(self, 403, payload(ok=False, status='BLOCKED', error=str(e)))
            except Exception as e:
                _json(self, 500, payload(ok=False, status='FAILED', error=str(e)))

        def do_GET(self):
            self._safe(self._get)

        def do_POST(self):
            self._safe(self._post)

        def do_PUT(self):
            self._safe(lambda: _json(self, 405, payload(ok=False, status='METHOD_DISABLED')))

        def do_PATCH(self):
            self._safe(lambda: _json(self, 405, payload(ok=False, status='METHOD_DISABLED')))

        def do_DELETE(self):
            self._safe(lambda: _json(self, 405, payload(ok=False, status='METHOD_DISABLED')))

        def _get(self):
            parsed = urlparse(self.path)
            p = parsed.path
            query = parse_qs(parsed.query)
            if p == '/api/v1/health':
                return _json(self, 200, payload(**{'service': 'unified_local_console'}, host='127.0.0.1'))
            if p in ROUTES:
                return _json(self, 200, ROUTES[p]())
            if p == '/api/v1/console/summary':
                return _json(self, 200, _summary())
            if p == '/api/v1/tasks/catalog':
                return _json(self, 200, payload(tasks=[task_to_dict(t) for t in list_tasks()]))
            if p == '/api/v1/tasks/history':
                return _json(self, 200, _task_history(_int_param(query, 'limit', 50, 200)))
            if p == '/api/v1/tasks':
                limit = _int_param(query, 'limit', 50, 200) if 'limit' in query else None
                return _json(self, 200, payload(tasks=[run_to_dict(r) for r in STORE.list(limit)]))
            if p.startswith('/api/v1/tasks/'):
                parts = p.split('/')
                rid = parts[4] if len(parts) > 4 else ''
                run = STORE.get(rid)
                if not run:
                    return _json(self, 404, payload(ok=False, status='DATA_MISSING', error='任务不存在'))
                if len(parts) > 5 and parts[5] == 'logs':
                    return _json(self, 200, payload(task_id=rid, logs=run.logs[-50:]))
                return _json(self, 200, payload(task=run_to_dict(run)))
            return self._static(p)

        def _post(self):
            p = urlparse(self.path).path
            raw = self.rfile.read(int(self.headers.get('Content-Length', '0') or 0))
            body = json.loads(raw.decode('utf-8') or '{}') if raw else {}
            if p == '/api/v1/tasks/run':
                run = run_task(body.get('task_id', ''), {k: _coerce(v) for k, v in body.get('params', {}).items()}, STORE)
                return _json(self, 200, payload(task=run_to_dict(run)))
            return _json(self, 404, payload(ok=False, status='DATA_MISSING', error='not found'))

        def _static(self, p):
            if not root:
                return _json(self, 404, payload(ok=False, status='DATA_MISSING', error='not found'))
            target = (root / ('index.html' if p == '/' else p.lstrip('/'))).resolve()
            if not str(target).startswith(str(root)) or not target.exists() or target.is_dir():
                return _json(self, 404, payload(ok=False, status='DATA_MISSING', error='not found'))
            data = target.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):
            return

    return Handler


def run_server(host=DEFAULT_HOST, port=DEFAULT_PORT, static_dir=None):
    assert_localhost_bind(host)
    HTTPServer((host, port), make_handler(static_dir)).serve_forever()
