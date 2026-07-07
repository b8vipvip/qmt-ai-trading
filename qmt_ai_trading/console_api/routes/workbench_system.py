from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .common import CONSOLE, payload, read_json
from . import workbench_api_config

SETTINGS_FILE = CONSOLE / 'system' / 'system_settings.private.json'

DEFAULT_SETTINGS: dict[str, Any] = {
    'runtime': {'mode': 'research'},
    'qmt': {
        'qmtClientPath': '',
        'xtdataPath': '',
        'xtquantPythonPath': '',
        'clientName': 'QMT',
    },
    'trading': {
        'defaultStockPool': '沪深300', 'commissionRate': 0.00025, 'slippageBps': 3, 'rebalancePeriod': 'daily',
        'backtestInitialCash': 1000000, 'backtestStartDate': '2021-01-01', 'backtestEndDate': '', 'stampTaxRate': 0.001,
        'enableT1': True, 'enableLimitCheck': True, 'enableSuspensionCheck': True, 'enableLiquidityLimit': True,
    },
    'risk': {'maxPositionPct': 80, 'maxSinglePositionPct': 10, 'maxIndustryExposurePct': 30, 'maxDrawdownPct': 15, 'dailyLossLimitPct': 3},
    'paths': {
        'marketCacheDir': 'artifacts/reports/console/datahub', 'factorArtifactDir': 'artifacts/reports/console/research',
        'backtestReportDir': 'artifacts/reports/console/backtest', 'taskHistoryDir': 'artifacts/reports/console/task_history',
    },
    'safety': {'allowRealOrder': False, 'allowCancelOrder': False, 'allowAccountQuery': False, 'enableHumanApproval': True},
}


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


def _write_settings(settings: dict[str, Any]) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding='utf-8')


def _merge(default: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(default)
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _settings() -> dict[str, Any]:
    data = _read_json_file(SETTINGS_FILE.as_posix(), {})
    merged = _merge(DEFAULT_SETTINGS, data if isinstance(data, dict) else {})
    qmt = merged.setdefault('qmt', {})
    if not qmt.get('qmtClientPath') and qmt.get('xtdataPath') and ('qmt' in str(qmt.get('xtdataPath')).lower() or '证券' in str(qmt.get('xtdataPath'))):
        qmt['qmtClientPath'] = qmt.get('xtdataPath')
        qmt['xtdataPath'] = ''
    if not qmt.get('clientName'):
        qmt['clientName'] = _detect_client_name(qmt.get('qmtClientPath') or qmt.get('xtdataPath') or '')
    return merged


def _num(value: Any, default: float, min_value: float, max_value: float) -> float:
    try:
        n = float(value)
    except Exception:
        return default
    return max(min_value, min(max_value, n))


def _clean_text(value: Any, default: str = '', max_len: int = 500) -> str:
    text = str(value if value is not None else default).strip()
    return text[:max_len]


def _detect_client_name(path: str) -> str:
    text = str(path).lower()
    if '国金' in str(path) or 'gjzq' in text:
        return '国金证券 QMT'
    if 'qmt' in text:
        return 'QMT'
    if 'xtquant' in text:
        return 'xtquant'
    if 'xtdata' in text:
        return 'xtdata'
    return 'QMT'


def _sanitize_settings(raw: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    current = _settings()
    data = _merge(current, raw if isinstance(raw, dict) else {})
    runtime_mode = _clean_text(data.get('runtime', {}).get('mode'), 'research')
    if runtime_mode not in {'research', 'simulation', 'shadow_live', 'small_capital_live', 'full_live'}:
        return None, '系统运行模式不合法'
    qmt = data.get('qmt', {})
    trading = data.get('trading', {})
    risk = data.get('risk', {})
    paths = data.get('paths', {})
    safety = data.get('safety', {})
    if bool(safety.get('allowRealOrder')):
        return None, '当前本地控制台安全策略禁止开启真实下单'
    if bool(safety.get('allowCancelOrder')):
        return None, '当前本地控制台安全策略禁止开启真实撤单'
    if not bool(safety.get('enableHumanApproval', True)):
        return None, '当前阶段必须启用人工审批闸门'
    qmt_client_path = _clean_text(qmt.get('qmtClientPath'), '', 500)
    xtdata_path = _clean_text(qmt.get('xtdataPath'), '', 500)
    sanitized = {
        'runtime': {'mode': runtime_mode},
        'qmt': {
            'qmtClientPath': qmt_client_path,
            'xtdataPath': xtdata_path,
            'xtquantPythonPath': _clean_text(qmt.get('xtquantPythonPath'), '', 500),
            'clientName': _detect_client_name(qmt_client_path or xtdata_path or qmt.get('clientName', 'QMT')),
        },
        'trading': {
            'defaultStockPool': _clean_text(trading.get('defaultStockPool'), '沪深300', 120),
            'commissionRate': _num(trading.get('commissionRate'), 0.00025, 0, 0.02),
            'slippageBps': _num(trading.get('slippageBps'), 3, 0, 500),
            'rebalancePeriod': _clean_text(trading.get('rebalancePeriod'), 'daily', 40),
            'backtestInitialCash': _num(trading.get('backtestInitialCash'), 1000000, 1000, 10000000000),
            'backtestStartDate': _clean_text(trading.get('backtestStartDate'), '2021-01-01', 20),
            'backtestEndDate': _clean_text(trading.get('backtestEndDate'), '', 20),
            'stampTaxRate': _num(trading.get('stampTaxRate'), 0.001, 0, 0.02),
            'enableT1': bool(trading.get('enableT1', True)),
            'enableLimitCheck': bool(trading.get('enableLimitCheck', True)),
            'enableSuspensionCheck': bool(trading.get('enableSuspensionCheck', True)),
            'enableLiquidityLimit': bool(trading.get('enableLiquidityLimit', True)),
        },
        'risk': {
            'maxPositionPct': _num(risk.get('maxPositionPct'), 80, 0, 100),
            'maxSinglePositionPct': _num(risk.get('maxSinglePositionPct'), 10, 0, 100),
            'maxIndustryExposurePct': _num(risk.get('maxIndustryExposurePct'), 30, 0, 100),
            'maxDrawdownPct': _num(risk.get('maxDrawdownPct'), 15, 0, 100),
            'dailyLossLimitPct': _num(risk.get('dailyLossLimitPct'), 3, 0, 100),
        },
        'paths': {
            'marketCacheDir': _clean_text(paths.get('marketCacheDir'), DEFAULT_SETTINGS['paths']['marketCacheDir'], 500),
            'factorArtifactDir': _clean_text(paths.get('factorArtifactDir'), DEFAULT_SETTINGS['paths']['factorArtifactDir'], 500),
            'backtestReportDir': _clean_text(paths.get('backtestReportDir'), DEFAULT_SETTINGS['paths']['backtestReportDir'], 500),
            'taskHistoryDir': _clean_text(paths.get('taskHistoryDir'), DEFAULT_SETTINGS['paths']['taskHistoryDir'], 500),
        },
        'safety': {
            'allowRealOrder': False,
            'allowCancelOrder': False,
            'allowAccountQuery': bool(safety.get('allowAccountQuery', False)),
            'enableHumanApproval': True,
        },
    }
    return sanitized, None


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


def _candidate(path: Path, kind: str, label: str = '') -> dict[str, Any]:
    return {'path': str(path), 'kind': kind, 'label': label or kind, 'exists': path.exists(), 'clientName': _detect_client_name(str(path))}


def _add_candidate(candidates: list[dict[str, Any]], seen: set[str], path: Path, kind: str, label: str = '') -> None:
    key = f'{kind}:{str(path).lower()}'
    if key in seen:
        return
    seen.add(key)
    if path.exists() or any(x in str(path).lower() for x in ['qmt', 'xtquant', 'xtdata']) or '国金' in str(path):
        candidates.append(_candidate(path, kind, label))


def _scan_qmt_candidates(target: str = 'all') -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    raw_roots: list[str] = []
    for env_name in ('QMT_PATH', 'XTQUANT_PATH', 'XTDATA_PATH', 'PATH'):
        value = os.environ.get(env_name, '')
        if env_name == 'PATH':
            raw_roots.extend([x for x in value.split(os.pathsep) if any(k in x.lower() for k in ['qmt', 'xtquant', 'xtdata'])])
        elif value:
            raw_roots.append(value)
    for drive in ['C:', 'D:', 'E:', 'F:']:
        raw_roots.extend([
            fr'{drive}\国金证券QMT交易端', fr'{drive}\国金证券QMT交易端\bin.x64', fr'{drive}\QMT', fr'{drive}\QMT\bin.x64',
            fr'{drive}\迅投极速交易终端睿智融科版', fr'{drive}\Program Files\QMT', fr'{drive}\Program Files (x86)\QMT',
        ])
    for raw in raw_roots:
        p = Path(raw)
        if target in {'all', 'qmtClientPath'}:
            for item in [p, p / 'bin.x64', p / 'bin']:
                _add_candidate(candidates, seen, item, 'qmtClientPath', 'QMT客户端目录')
        if target in {'all', 'xtdataPath'}:
            for item in [p / 'userdata_mini' / 'datadir', p / 'userdata' / 'datadir', p / 'xtdata', p / 'data']:
                _add_candidate(candidates, seen, item, 'xtdataPath', 'xtdata数据目录')
    if target in {'all', 'xtquantPythonPath'}:
        bases = [Path(sys.prefix), Path.cwd(), Path.home()]
        for extra in sys.path:
            try:
                bases.append(Path(extra))
            except Exception:
                pass
        for base in bases:
            for rel in ['Lib/site-packages/xtquant', 'site-packages/xtquant', 'xtquant']:
                p = base / rel
                if (p / 'xtdata.py').exists() or p.exists():
                    _add_candidate(candidates, seen, p, 'xtquantPythonPath', 'xtquant Python目录')
    return candidates[:120]


def settings():
    return payload(status='READY', source='system_settings_store', data=_settings(), sourcePath=SETTINGS_FILE.as_posix())


def save_settings(body: dict[str, Any]):
    raw = body.get('settings') if isinstance(body.get('settings'), dict) else body
    sanitized, error = _sanitize_settings(raw)
    if error:
        return payload(ok=False, status='FAILED', error=error)
    assert sanitized is not None
    _write_settings(sanitized)
    return payload(status='SAVED', source='system_settings_store', data=sanitized, sourcePath=SETTINGS_FILE.as_posix())


def scan_qmt_paths(body: dict[str, Any] | None = None):
    body = body or {}
    target = _clean_text(body.get('target'), 'all', 40)
    if target not in {'all', 'qmtClientPath', 'xtdataPath', 'xtquantPythonPath'}:
        target = 'all'
    settings_data = _settings()
    candidates = _scan_qmt_candidates(target)
    return payload(status='READY', source='qmt_path_scanner', data={'target': target, 'current': settings_data.get('qmt', {}), 'candidates': candidates, 'count': len(candidates), 'note': 'Web 浏览器不能直接读取本机绝对目录，使用后端扫描候选路径；也可以手动修正。'})


def _test_path(kind: str, path: str) -> tuple[str, str]:
    if not path:
        return 'FAILED', '未配置路径'
    return ('READY', '路径存在') if Path(path).exists() else ('FAILED', '路径不存在')


def test_qmt_settings(body: dict[str, Any] | None = None):
    body = body or {}
    kind = _clean_text(body.get('kind'), 'all', 40)
    settings_data = _settings()
    qmt = settings_data.get('qmt', {})
    python_path = _clean_text(qmt.get('xtquantPythonPath'), '', 500)
    if python_path and python_path not in sys.path and Path(python_path).exists():
        sys.path.insert(0, python_path)
    checks: list[dict[str, Any]] = []
    for key, label in [('qmtClientPath', 'QMT客户端目录'), ('xtdataPath', 'xtdata数据目录'), ('xtquantPythonPath', 'xtquant Python目录')]:
        if kind not in {'all', key}:
            continue
        path = _clean_text(qmt.get(key), '', 500)
        status, message = _test_path(key, path)
        checks.append({'kind': key, 'label': label, 'path': path, 'status': status, 'message': message})
    import_status = 'FAILED'
    import_message = ''
    try:
        from xtquant import xtdata  # type: ignore
        import_status, import_message = 'READY', 'xtquant.xtdata 可导入'
    except Exception as exc:
        import_message = f'xtquant.xtdata 不可导入：{exc}'
    if kind in {'all', 'xtquantPythonPath'}:
        checks.append({'kind': 'xtdataImport', 'label': 'xtquant.xtdata导入', 'path': python_path, 'status': import_status, 'message': import_message})
    final_status = 'READY' if checks and all(x['status'] == 'READY' for x in checks) else 'FAILED'
    result = {'kind': kind, 'checks': checks, 'checkedAt': workbench_api_config._now(), 'status': final_status, 'message': '；'.join([f"{x['label']}:{x['message']}" for x in checks]), 'sourcePath': SETTINGS_FILE.as_posix()}
    return payload(status=final_status, source='qmt_xtdata_system_settings_test', data=result)


def config_center():
    settings_data = _settings()
    pkg = _read_json_file('frontend/package.json', {})
    rows = [
        {'key': 'runtime.mode', 'name': '系统运行模式', 'value': settings_data['runtime']['mode'], 'source': SETTINGS_FILE.as_posix(), 'editable': True, 'sensitive': False},
        {'key': 'trading.defaultStockPool', 'name': '默认股票池', 'value': settings_data['trading']['defaultStockPool'], 'source': SETTINGS_FILE.as_posix(), 'editable': True, 'sensitive': False},
        {'key': 'risk.maxPositionPct', 'name': '最大仓位', 'value': settings_data['risk']['maxPositionPct'], 'source': SETTINGS_FILE.as_posix(), 'editable': True, 'sensitive': False},
        {'key': 'paths.marketCacheDir', 'name': '行情缓存目录', 'value': settings_data['paths']['marketCacheDir'], 'source': SETTINGS_FILE.as_posix(), 'editable': True, 'sensitive': False},
        {'key': 'safety.allowRealOrder', 'name': '允许真实下单', 'value': settings_data['safety']['allowRealOrder'], 'source': 'safety_policy_runtime', 'editable': False, 'sensitive': False},
        {'key': 'frontend_stack', 'name': '前端技术栈', 'value': ', '.join(sorted((pkg.get('dependencies') or {}).keys())) if isinstance(pkg, dict) else '', 'source': 'frontend/package.json', 'editable': False, 'sensitive': False},
    ]
    return payload(status='READY', source='system_settings_store', data=rows)


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
        {'name': 'System Settings', 'endpoint': '/api/v1/frontend/system/settings', 'status': 'READY', 'method': 'GET/POST', 'source': SETTINGS_FILE.as_posix()},
        {'name': 'QMT Path Scan/Test', 'endpoint': '/api/v1/frontend/system/qmt/scan + /qmt/test', 'status': 'READY', 'method': 'POST', 'source': SETTINGS_FILE.as_posix()},
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
    api_configs = [x for x in workbench_api_config._load() if x.get('provider') != 'qmt_xtdata']
    settings_data = _settings()
    qmt = settings_data.get('qmt', {})
    return payload(status='READY', source='system_summary', data={'artifactRoot': CONSOLE.as_posix(), 'taskCount': len(catalog), 'historyCount': len(history), 'apiConfigCount': len(api_configs), 'enabledApiConfigCount': sum(1 for x in api_configs if x.get('enabled')), 'latestRunAt': (history[0].get('finished_at') if history else ''), 'runMode': settings_data['runtime']['mode'], 'qmtPathConfigured': bool(qmt.get('qmtClientPath') or qmt.get('xtdataPath') or qmt.get('xtquantPythonPath')), 'liveTradingEnabled': False, 'orderSubmitEnabled': False, 'orderCancelEnabled': False, 'sourcePath': SETTINGS_FILE.as_posix()})
