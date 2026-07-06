from __future__ import annotations

from typing import Any

from .common import CONSOLE, payload, read_json

MODULE = 'task_history'
NAME = 'task_history.json'


def _source_path() -> str:
    return (CONSOLE / MODULE / NAME).as_posix()


def _first_array(obj: Any) -> list[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for value in obj.values():
            arr = _first_array(value)
            if arr:
                return arr
    return []


def _runs() -> list[dict[str, Any]]:
    doc = read_json(MODULE, NAME, {})
    return [item for item in _first_array(doc) if isinstance(item, dict)]


def dashboard_events():
    rows = []
    for idx, run in enumerate(_runs()[:30]):
        rows.append({
            'id': run.get('run_id') or f'run-{idx}',
            'time': run.get('finished_at') or run.get('started_at') or '',
            'level': 'normal' if run.get('status') == 'SUCCESS' else 'warning',
            'module': run.get('category') or run.get('task_id') or 'TASK',
            'message': run.get('task_name') or run.get('task_id') or '任务执行记录',
            'runId': run.get('run_id'),
            'taskId': run.get('task_id'),
            'sourcePath': _source_path(),
        })
    return payload(status='READY', source='task_history', data=rows)


def data_tasks():
    rows = []
    for run in _runs()[:30]:
        rows.append({
            'name': run.get('task_name') or run.get('task_id') or '',
            'type': run.get('category') or 'TASK',
            'cron': 'manual',
            'lastRun': run.get('finished_at') or run.get('started_at') or '',
            'nextRun': '',
            'status': run.get('status') or '',
            'cost': run.get('duration') or '',
            'sourcePath': _source_path(),
        })
    return payload(status='READY', source='task_history', data=rows)


def api_status():
    rows = [
        {'name': '统一控制台 API', 'status': 'normal', 'latency': 'local', 'sourcePath': 'qmt_ai_trading/console_api/api_server.py'},
        {'name': 'QMT / 券商 API', 'status': 'offline', 'latency': '-', 'sourcePath': 'pending_broker_adapter'},
        {'name': 'Task History', 'status': 'normal', 'latency': 'local', 'sourcePath': _source_path()},
    ]
    return payload(status='READY', source='task_history', data=rows)
