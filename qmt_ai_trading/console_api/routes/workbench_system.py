from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .common import CONSOLE, payload, read_json
from . import workbench_api_config


def _artifact_path(module: str, name: str) -> str:
    return (CONSOLE / module / name).as_posix()


def _read_text(path: str) -> str:
    try:
        p = Path(path)
        return p.read_text(encoding='utf-8') if p.exists() else ''
    except Exception:
        return ''


def _read_json_file(path: str, default: Any) -> Any:
    try:
        p = Path(path)
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
    except Exception:
        return default


def _first_array(obj: Any) -> list[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for value in obj.values():
            arr = _first_array(value)
            if arr:
                return arr
    return []


def _task_history() -> list[dict[str, Any]]:
    doc = read_json('task_history', 'task_history.json', {})
    return [x for x in _first_array(doc) if isinstance(x, dict)]


def _task_catalog() -> list[dict[str, Any]]:
    try:
        from qmt_ai_trading.console_api.task_registry import list_tasks
        return [asdict(t) for t in list_tasks()]
    except Exception:
        return []


def config_center():
    pkg = _read_json_file('frontend/package.json', {})
    pyproject = _read_text('pyproject.toml')
    rows = [
        {'key': 'console_api_host', 'name': 'Console API 默认地址', 'value': '127.0.0.1:8768', 'source': 'scripts/run_console_api.py', 'editable': False, 'sensitive': False},
        {'key': 'frontend_dev_server', 'name': '前端开发服务', 'value': '127.0.0.1:5173', 'source': 'frontend/package.json', 'editable': False, 'sensitive': False},
        {'key': 'frontend_stack', 'name': '前端技术栈', 'value': ', '.join(sorted((pkg.get('dependencies') or {}).keys())) if isinstance(pkg, dict) else '', 'source': 'frontend/package.json', 'editable': False, 'sensitive': False},
        {'key': 'console_artifact_root', 'name': '控制台产物目录', 'value': CONSOLE.as_posix(), 'source': 'qmt_ai_trading/console_api/routes/common.py', 'editable': False, 'sensitive': False},
        {'key': 'python_version', 'name': 'Python 版本', 'value': sys.version.split()[0], 'source': 'runtime', 'editable': False, 'sensitive': False},
        {'key': 'env_secret_policy', 'name': '敏感配置策略', 'value': '不在系统管理页面展示 .env、token、secret、key 明文', 'source': 'safety_policy_runtime', 'editable': False, 'sensitive': True},
        {'key': 'pyproject_present', 'name': 'Python 项目配置', 'value': 'present' if pyproject else 'missing', 'source': 'pyproject.toml', 'editable': False, 'sensitive': False},
    ]
    return payload(status='READY', source='repo_runtime_config', data=rows)


def api_status():
    route_text = _read_text('qmt_ai_trading/console_api/routes/__init__.py')
    route_count = route_text.count("'/api/v1/")
    routes = []
    for part in route_text.split("'/api/v1/")[1:]:
        endpoint = '/api/v1/' + part.split("'", 1)[0]
        if endpoint not in routes:
            routes.append(endpoint)
    rows = [
        {'name': 'Health API', 'endpoint': '/api/v1/health', 'status': 'READY', 'method': 'GET', 'source': 'qmt_ai_trading/console_api/api_server.py'},
        {'name': 'Registered API Routes', 'endpoint': f'{route_count} routes', 'status': 'READY' if route_count else 'ERROR', 'method': 'GET/POST', 'source': 'qmt_ai_trading/console_api/routes/__init__.py'},
        {'name': 'Task Runner', 'endpoint': '/api/v1/tasks/run', 'status': 'READY', 'method': 'POST', 'source': 'qmt_ai_trading/console_api/task_runner.py'},
        {'name': 'Task Catalog', 'endpoint': '/api/v1/tasks/catalog', 'status': 'READY', 'method': 'GET', 'source': 'qmt_ai_trading/console_api/task_registry.py'},
        {'name': 'Task History', 'endpoint': '/api/v1/tasks/history', 'status': 'READY', 'method': 'GET', 'source': _artifact_path('task_history', 'task_history.json')},
        {'name': 'External API Configs', 'endpoint': '/api/v1/frontend/system/api-configs', 'status': 'READY', 'method': 'GET/POST', 'source': 'qmt_ai_trading/console_api/routes/workbench_api_config.py'},
        {'name': 'Frontend Adapter Routes', 'endpoint': '/api/v1/frontend/*', 'status': 'READY', 'method': 'GET', 'source': 'qmt_ai_trading/console_api/routes/workbench_*.py'},
    ]
    return payload(status='READY', source='registered_routes', route_count=route_count, routes=routes, data=rows)


def audit_logs():
    rows = []
    for run in _task_history()[:200]:
        rows.append({'time': run.get('finished_at') or run.get('started_at') or '', 'user': 'local_operator', 'module': run.get('category') or '', 'operation': run.get('task_name') or run.get('task_id') or '', 'paramsSummary': json.dumps(run.get('params') or {}, ensure_ascii=False)[:260], 'ip': '127.0.0.1', 'result': run.get('status') or '', 'runId': run.get('run_id'), 'sourcePath': _artifact_path('task_history', 'task_history.json')})
    return payload(status='READY', source='task_history_audit', data=rows)


def permission_matrix():
    rows = []
    for task in _task_catalog():
        rows.append({'id': task.get('task_id'), 'name': task.get('title_zh'), 'category': task.get('category'), 'safeMode': bool(task.get('safe_mode')), 'dryRunOnly': bool(task.get('dry_run_only')), 'requiresHumanApproval': bool(task.get('requires_human_approval')), 'forbiddenInLive': bool(task.get('forbidden_in_live')), 'commandAdapter': task.get('command_adapter'), 'outputArtifacts': task.get('output_artifacts') or [], 'canRunFromFrontend': bool(task.get('safe_mode')) and bool(task.get('dry_run_only')), 'sourcePath': 'qmt_ai_trading/console_api/task_registry.py'})
    return payload(status='READY', source='task_registry_permissions', data=rows)


def system_summary():
    history = _task_history()
    catalog = _task_catalog()
    api_configs = workbench_api_config._load()
    return payload(status='READY', source='system_summary', data={'artifactRoot': CONSOLE.as_posix(), 'taskCount': len(catalog), 'historyCount': len(history), 'apiConfigCount': len(api_configs), 'enabledApiConfigCount': sum(1 for x in api_configs if x.get('enabled')), 'latestRunAt': (history[0].get('finished_at') if history else ''), 'liveTradingEnabled': False, 'orderSubmitEnabled': False, 'orderCancelEnabled': False, 'sourcePath': _artifact_path('task_history', 'task_history.json')})
