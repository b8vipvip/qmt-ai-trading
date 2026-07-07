from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .common import CONSOLE, payload, read_json
from . import workbench_api_config

SETTINGS_FILE = CONSOLE / 'system' / 'system_settings.private.json'
QMT_EXE_KEYWORDS = ('qmt', 'xt', 'trade', 'trader', 'client', '国金', '交易', '终端')
QMT_EXE_NAMES = (
    'XtMiniQmt.exe', 'miniQmt.exe', 'MiniQmt.exe', 'qmt.exe', '国金证券QMT交易端.exe',
    'XtItClient.exe', 'xiadan.exe', 'trader.exe', 'client.exe'
)

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


def _find_client_executable(path: str) -> Path | None:
    if not path:
        return None
    p = Path(path)
    if p.is_file() and p.suffix.lower() == '.exe':
        return p
    if not p.exists() or not p.is_dir():
        return None
    search_dirs = [p, p / 'bin.x64', p / 'bin', p / 'bin64']
    for d in search_dirs:
        if not d.exists() or not d.is_dir():
            continue
        for name in QMT_EXE_NAMES:
            candidate = d / name
            if candidate.exists() and candidate.is_file():
                return candidate
        for exe in d.glob('*.exe'):
            lower = exe.name.lower()
            if any(k in lower for k in QMT_EXE_KEYWORDS) or any(k in exe.name for k in ('交易', '终端', '国金')):
                return exe
    return None


def _path_has_xtdata_files(path: str) -> bool:
    p = Path(path)
    if not p.exists() or not p.is_dir():
        return False
    try:
        return any(p.iterdir())
    except Exception:
        return True


def _xtquant_dir_valid(path: str) -> bool:
    p = Path(path)
    return p.exists() and p.is_dir() and ((p / 'xtdata.py').exists() or (p / '__init__.py').exists())


def _candidate(path: Path, kind: str, label: str = '') -> dict[str, Any]:
    exe = _find_client_executable(str(path)) if kind == 'qmtClientPath' else None
    return {'path': str(path), 'kind': kind, 'label': label or kind, 'exists': path.exists(), 'clientName': _detect_client_name(str(path)), 'executable': str(exe) if exe else ''}


def _add_candidate(candidates: list[dict[str, Any]], seen: set[str], path: Path, kind: str, label: str = '') -> None:
    key = f'{kind}:{str(path).lower()}'
    if key in seen:
        return
    seen.add(key)
    if kind == 'qmtClientPath':
        if path.exists() and _find_client_executable(str(path)):
            candidates.append(_candidate(path, kind, label))
        return
    if kind == 'xtdataPath':
        if _path_has_xtdata_files(str(path)):
            candidates.append(_candidate(path, kind, label))
        return
    if kind == 'xtquantPythonPath':
        if _xtquant_dir_valid(str(path)):
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
            fr'{drive}\\国金证券QMT交易端', fr'{drive}\\国金证券QMT交易端\\bin.x64', fr'{drive}\\QMT', fr'{drive}\\QMT\\bin.x64',
            fr'{drive}\\迅投极速交易终端睿智融科版', fr'{drive}\\Program Files\\QMT', fr'{drive}\\Program Files (x86)\\QMT',
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
                _add_candidate(candidates, seen, base / rel, 'xtquantPythonPath', 'xtquant Python目录')
    return candidates[:120]


def _process_running(exe: Path) -> bool:
    if os.name != 'nt':
        return False
    try:
        result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {exe.name}'], capture_output=True, text=True, timeout=5)
        return exe.name.lower() in result.stdout.lower()
    except Exception:
        return False


def _launch_client(exe: Path) -> tuple[str, str]:
    if _process_running(exe):
        return 'READY', f'客户端进程已运行：{exe.name}'
    try:
        flags = 0
        if os.name == 'nt':
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        proc = subprocess.Popen([str(exe)], cwd=str(exe.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, creationflags=flags)
        time.sleep(1.5)
        if proc.poll() is None or _process_running(exe):
            return 'READY', f'客户端已启动：{exe}'
        return 'FAILED', f'客户端启动后立即退出，退出码：{proc.poll()}'
    except Exception as exc:
        return 'FAILED', f'客户端启动失败：{exc}'


def _xtdata_api_probe(python_path: str) -> tuple[str, str]:
    if python_path and python_path not in sys.path and Path(python_path).exists():
        sys.path.insert(0, python_path)
    try:
        from xtquant import xtdata  # type: ignore
    except Exception as exc:
        return 'FAILED', f'xtquant.xtdata 不可导入：{exc}'
    probes = []
    for name, fn in [
        ('get_trading_dates', lambda: xtdata.get_trading_dates('SH', '20240101', '20240131')),
        ('get_stock_list_in_sector', lambda: xtdata.get_stock_list_in_sector('沪深A股')),
    ]:
        try:
            value = fn()
            size = len(value) if hasattr(value, '__len__') else 0
            probes.append(f'{name}=OK({size})')
            if size:
                return 'READY', 'xtdata 只读 API 正常：' + ', '.join(probes)
        except Exception as exc:
            probes.append(f'{name}=FAILED({exc})')
    return 'FAILED', 'xtdata 已导入，但只读 API 调用失败。请确认 QMT 客户端已打开并已登录：' + '; '.join(probes)


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
    return payload(status='READY', source='qmt_path_scanner', data={'target': target, 'current': settings_data.get('qmt', {}), 'candidates': candidates, 'count': len(candidates), 'note': '只返回真实存在且可识别的目录：QMT 客户端目录必须包含真实 exe；xtdata/xtquant 目录必须真实存在。'})


def _test_path(kind: str, qmt: dict[str, Any]) -> dict[str, Any]:
    path = _clean_text(qmt.get(kind), '', 500)
    labels = {'qmtClientPath': 'QMT客户端目录', 'xtdataPath': 'xtdata数据目录', 'xtquantPythonPath': 'xtquant Python目录'}
    label = labels.get(kind, kind)
    if not path:
        return {'kind': kind, 'label': label, 'path': path, 'status': 'FAILED', 'message': '未配置路径'}
    if kind == 'qmtClientPath':
        exe = _find_client_executable(path)
        if not Path(path).exists():
            return {'kind': kind, 'label': label, 'path': path, 'status': 'FAILED', 'message': '目录不存在'}
        if not exe:
            return {'kind': kind, 'label': label, 'path': path, 'status': 'FAILED', 'message': '目录存在，但未发现真实 QMT 客户端 exe'}
        status, message = _launch_client(exe)
        return {'kind': kind, 'label': label, 'path': path, 'status': status, 'message': message, 'executable': str(exe)}
    if kind == 'xtdataPath':
        if _path_has_xtdata_files(path):
            return {'kind': kind, 'label': label, 'path': path, 'status': 'READY', 'message': 'xtdata 数据目录存在且非空'}
        return {'kind': kind, 'label': label, 'path': path, 'status': 'FAILED', 'message': 'xtdata 数据目录不存在或为空'}
    if kind == 'xtquantPythonPath':
        if _xtquant_dir_valid(path):
            return {'kind': kind, 'label': label, 'path': path, 'status': 'READY', 'message': 'xtquant Python 目录存在，包含 xtdata.py 或 __init__.py'}
        return {'kind': kind, 'label': label, 'path': path, 'status': 'FAILED', 'message': 'xtquant Python 目录无效'}
    return {'kind': kind, 'label': label, 'path': path, 'status': 'FAILED', 'message': '未知测试类型'}


def test_qmt_settings(body: dict[str, Any] | None = None):
    body = body or {}
    kind = _clean_text(body.get('kind'), 'all', 40)
    if kind not in {'all', 'qmtClientPath', 'xtdataPath', 'xtquantPythonPath', 'loginApi'}:
        kind = 'all'
    settings_data = _settings()
    qmt = settings_data.get('qmt', {})
    checks: list[dict[str, Any]] = []
    for key in ['qmtClientPath', 'xtdataPath', 'xtquantPythonPath']:
        if kind in {'all', key}:
            checks.append(_test_path(key, qmt))
    if kind in {'all', 'loginApi'}:
        status, message = _xtdata_api_probe(_clean_text(qmt.get('xtquantPythonPath'), '', 500))
        checks.append({'kind': 'loginApi', 'label': '登录后 xtdata API 测试', 'path': _clean_text(qmt.get('xtquantPythonPath'), '', 500), 'status': status, 'message': message})
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
