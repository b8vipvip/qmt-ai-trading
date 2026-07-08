from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .common import CONSOLE, payload
from . import workbench_system, workbench_market

SYNC_FILE = CONSOLE / 'market' / 'qmt_universe_sync_result.json'
GROUP_FILES = {
    'all_a': CONSOLE / 'market' / 'qmt_universe_all_a.json',
    'etf': CONSOLE / 'market' / 'qmt_universe_etf.json',
    'index': CONSOLE / 'market' / 'qmt_universe_index.json',
}

GROUP_DEFS = {
    'all_a': {'name': 'QMT 全A股票池', 'description': '从 QMT / xtdata 真实同步沪深北 A 股代码，用于构建全A可交易池的基础列表。', 'aliases': ['沪深A股', 'A股', '上证A股', '深证A股', '北证A股']},
    'etf': {'name': 'QMT ETF全量池', 'description': '从 QMT / xtdata 真实同步场内 ETF / 基金代码，用于 ETF 轮动和主题池。', 'aliases': ['沪深ETF', 'ETF', 'ETF基金', '沪深基金', '场内基金', '基金']},
    'index': {'name': 'QMT 指数池', 'description': '从 QMT / xtdata 真实同步指数代码，用于基准、行业和风格分析。', 'aliases': ['沪深指数', '指数', '上证指数', '深证指数', '中证指数']},
}

PREFIX_RE = re.compile(r'^(SH|SZ|BJ)[\.:-]?(\d{6})$', re.I)
SUFFIX_RE = re.compile(r'^(\d{6})[\.:-]?(SH|SZ|BJ)$', re.I)


def _now() -> str:
    return datetime.now().isoformat(timespec='seconds')


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default
    return default


def _write_json(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return path.as_posix()


def _normalize_qmt_symbol(value: Any) -> str:
    raw = str(value or '').strip().upper().replace(' ', '')
    if not raw:
        return ''
    m = PREFIX_RE.match(raw)
    if m:
        raw = f'{m.group(2)}.{m.group(1).upper()}'
    else:
        m = SUFFIX_RE.match(raw)
        if m:
            raw = f'{m.group(1)}.{m.group(2).upper()}'
    return workbench_market._normalize_symbol(raw)


def _dedupe_symbols(values: Any) -> list[str]:
    if not isinstance(values, list):
        values = list(values or []) if values is not None and not isinstance(values, (str, bytes)) else [values]
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        symbol = _normalize_qmt_symbol(item)
        if symbol and symbol not in seen:
            seen.add(symbol)
            out.append(symbol)
    return out


def _import_xtdata() -> tuple[Any | None, str]:
    settings = workbench_system._settings()
    python_path = str(settings.get('qmt', {}).get('xtquantPythonPath') or '').strip()
    if python_path and Path(python_path).exists() and python_path not in sys.path:
        sys.path.insert(0, python_path)
    try:
        from xtquant import xtdata  # type: ignore
        return xtdata, 'IMPORTED'
    except Exception as exc:
        return None, f'IMPORT_FAILED:{type(exc).__name__}: {exc}'


def _call_sector(xtdata: Any, sector_name: str) -> dict[str, Any]:
    try:
        raw = xtdata.get_stock_list_in_sector(sector_name)
        symbols = _dedupe_symbols(raw)
        return {'sector': sector_name, 'status': 'READY' if symbols else 'EMPTY', 'count': len(symbols), 'symbols': symbols, 'error': ''}
    except Exception as exc:
        return {'sector': sector_name, 'status': 'FAILED', 'count': 0, 'symbols': [], 'error': f'{type(exc).__name__}: {exc}'}


def _sync_group(xtdata: Any, group_key: str) -> dict[str, Any]:
    definition = GROUP_DEFS[group_key]
    sector_results = [_call_sector(xtdata, sector) for sector in definition['aliases']]
    symbols: list[str] = []
    seen: set[str] = set()
    for result in sector_results:
        for symbol in result.get('symbols') or []:
            if symbol not in seen:
                seen.add(symbol)
                symbols.append(symbol)
    status = 'READY' if symbols else 'FAILED'
    errors = [f"{r['sector']}:{r['error']}" for r in sector_results if r.get('error')]
    doc = {'key': group_key, 'name': definition['name'], 'description': definition['description'], 'status': status, 'syncedAt': _now(), 'symbolCount': len(symbols), 'symbols': symbols, 'sectorResults': sector_results, 'errors': errors, 'source': 'xtdata.get_stock_list_in_sector', 'readOnly': True, 'noXtTrader': True, 'noOrderSubmitted': True, 'noAccountQuery': True}
    doc['sourcePath'] = _write_json(GROUP_FILES[group_key], doc)
    return doc


def _last_sync() -> dict[str, Any]:
    data = _read_json(SYNC_FILE, {})
    if isinstance(data, dict) and data:
        return data
    groups = [_read_json(path, {}) for path in GROUP_FILES.values()]
    groups = [g for g in groups if isinstance(g, dict) and g]
    return {'status': 'NOT_SYNCED', 'syncedAt': '', 'groups': groups, 'groupCount': len(groups), 'message': '尚未同步 QMT 真实股票列表', 'sourcePath': SYNC_FILE.as_posix()}


def qmt_universe_sync_status():
    return payload(status='READY', source='qmt_universe_sync_store', data=_last_sync())


def sync_qmt_universe(body: dict[str, Any] | None = None):
    body = body or {}
    requested = body.get('groups') or ['all_a', 'etf', 'index']
    if isinstance(requested, str):
        requested = [requested]
    groups = [g for g in requested if g in GROUP_DEFS]
    if not groups:
        groups = ['all_a', 'etf', 'index']
    client_probe = workbench_system.test_qmt_settings({'kind': 'qmtClientPath'}).get('data', {})
    xtdata, import_status = _import_xtdata()
    if xtdata is None:
        result = {'status': 'FAILED', 'syncedAt': _now(), 'message': f'xtquant.xtdata 导入失败，无法同步真实列表：{import_status}', 'importStatus': import_status, 'clientProbe': client_probe, 'groups': [], 'groupCount': 0, 'readOnly': True, 'noXtTrader': True, 'noOrderSubmitted': True, 'noAccountQuery': True}
        result['sourcePath'] = _write_json(SYNC_FILE, result)
        return payload(ok=False, status='FAILED', error=result['message'], data=result)
    results = [_sync_group(xtdata, group) for group in groups]
    ready_count = sum(1 for item in results if item.get('status') == 'READY')
    total_symbols = sum(int(item.get('symbolCount') or 0) for item in results)
    status = 'READY' if ready_count else 'FAILED'
    message = f'QMT 真实列表同步完成：成功 {ready_count}/{len(results)} 组，总标的 {total_symbols} 个' if ready_count else 'QMT 真实列表同步失败：未从 get_stock_list_in_sector 获取到任何标的。请确认 QMT 客户端已启动并登录。'
    result = {'status': status, 'syncedAt': _now(), 'message': message, 'importStatus': import_status, 'clientProbe': client_probe, 'groups': results, 'groupCount': len(results), 'readyGroupCount': ready_count, 'totalSymbolCount': total_symbols, 'source': 'xtdata.get_stock_list_in_sector', 'readOnly': True, 'noXtTrader': True, 'noOrderSubmitted': True, 'noAccountQuery': True}
    result['sourcePath'] = _write_json(SYNC_FILE, result)
    return payload(status=status, source='qmt_universe_sync', data=result)
