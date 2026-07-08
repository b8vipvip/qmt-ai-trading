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

GROUP_DEFS = {
    'all_a': {'name': 'QMT 全A股票池', 'description': '从 QMT / xtdata 真实同步沪深北 A 股代码，用于构建全A可交易池的基础列表。', 'aliases': ['沪深A股', 'A股', '上证A股', '深证A股', '北证A股']},
    'etf': {'name': 'QMT ETF全量池', 'description': '从 QMT / xtdata 真实同步场内 ETF / 基金代码，用于 ETF 轮动和主题池。', 'aliases': ['沪深ETF', 'ETF', 'ETF基金', '沪深基金', '场内基金', '基金']},
    'index': {'name': 'QMT 指数池', 'description': '从 QMT / xtdata 真实同步指数代码，用于基准、行业和风格分析。', 'aliases': ['沪深指数', '指数', '上证指数', '深证指数', '中证指数']},
    'broad_market': {'name': '大盘/基准指数池', 'description': '量化研究必需的大盘基准行情，用于相对收益、市场状态、Beta、择时和风控判断。', 'aliases': ['沪深指数', '中证指数', '上证指数', '深证指数'], 'fixedSymbols': ['000001.SH', '000016.SH', '000300.SH', '000905.SH', '000852.SH', '399001.SZ', '399006.SZ']},
    'convertible_bond': {'name': '可转债池', 'description': '用于可转债策略、股债联动和风险偏好分析；如果本机 QMT sector 不支持会显示 EMPTY/FAILED。', 'aliases': ['可转债', '沪深转债', '转债', '债券']},
    'sector_index': {'name': '行业/板块指数池', 'description': '用于行业轮动、行业暴露、板块热度和风格归因分析；不同 QMT 版本 sector 名称可能不同。', 'aliases': ['行业指数', '申万行业指数', '中证行业指数', '概念指数', '板块指数']},
}

GROUP_FILES = {key: CONSOLE / 'market' / f'qmt_universe_{key}.json' for key in GROUP_DEFS}
TIME_KEYS = {'time', 'datetime', 'updated_at', 'updatedAt', 'timestamp', 'stime', 'date', 'tradeDate', 'index'}
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
    sector_results = [_call_sector(xtdata, sector) for sector in definition.get('aliases', [])]
    symbols: list[str] = []
    seen: set[str] = set()
    for symbol in _dedupe_symbols(definition.get('fixedSymbols') or []):
        seen.add(symbol)
        symbols.append(symbol)
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
    requested = body.get('groups') or list(GROUP_DEFS.keys())
    if isinstance(requested, str):
        requested = [requested]
    groups = [g for g in requested if g in GROUP_DEFS]
    if not groups:
        groups = list(GROUP_DEFS.keys())
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


def _first_array(obj: Any) -> list[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for value in obj.values():
            arr = _first_array(value)
            if arr:
                return arr
    return []


def _count_records(data: Any) -> int:
    if isinstance(data, dict):
        for key in ('symbols', 'groups', 'data', 'rows', 'bars', 'snapshots'):
            value = data.get(key)
            if isinstance(value, list):
                return len(value)
    arr = _first_array(data)
    return len(arr)


def _parse_time_ms(value: Any) -> int | None:
    if value in (None, ''):
        return None
    raw = str(value).strip()
    if not raw or '*' in raw:
        return None
    digits = re.sub(r'\.0+$', '', raw)
    try:
        if re.fullmatch(r'\d{13}', digits):
            return int(digits)
        if re.fullmatch(r'\d{10}', digits):
            return int(digits) * 1000
        if re.fullmatch(r'\d{14}', digits):
            dt = datetime(int(digits[0:4]), int(digits[4:6]), int(digits[6:8]), int(digits[8:10]), int(digits[10:12]), int(digits[12:14]))
            return int(dt.timestamp() * 1000)
        if re.fullmatch(r'\d{8}', digits):
            dt = datetime(int(digits[0:4]), int(digits[4:6]), int(digits[6:8]))
            return int(dt.timestamp() * 1000)
        return int(datetime.fromisoformat(raw.replace('Z', '+00:00')).timestamp() * 1000)
    except Exception:
        return None


def _fmt_ms(ms: int | None) -> str:
    return datetime.fromtimestamp(ms / 1000).isoformat(timespec='seconds') if ms is not None else ''


def _walk_times(obj: Any, out: list[int], depth: int = 0) -> None:
    if depth > 6:
        return
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in TIME_KEYS:
                ms = _parse_time_ms(value)
                if ms is not None:
                    out.append(ms)
            if isinstance(value, (dict, list)):
                _walk_times(value, out, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:5000]:
            _walk_times(item, out, depth + 1)


def _time_range(data: Any, data_type: str) -> tuple[str, str, str]:
    if data_type in {'标的列表', '配置', 'QMT列表同步结果', 'QMT真实列表'}:
        return '', '', '不适用（列表/配置数据）'
    times: list[int] = []
    _walk_times(data, times)
    if not times:
        return '', '', '未识别到时间字段'
    start = min(times)
    end = max(times)
    return _fmt_ms(start), _fmt_ms(end), f'{_fmt_ms(start)} 至 {_fmt_ms(end)}'


def _dataset_row(key: str, name: str, data_type: str, path: Path, note: str = '') -> dict[str, Any]:
    exists = path.exists()
    data = _read_json(path, {}) if exists else {}
    mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec='seconds') if exists else ''
    updated_at = data.get('syncedAt') or data.get('generated_at') or data.get('updatedAt') or mtime if isinstance(data, dict) else mtime
    start_time, end_time, time_range = _time_range(data, data_type) if exists else ('', '', '')
    return {'key': key, 'name': name, 'type': data_type, 'status': 'READY' if exists else 'MISSING', 'recordCount': _count_records(data), 'startTime': start_time, 'endTime': end_time, 'timeRange': time_range, 'updatedAt': updated_at, 'sourcePath': path.as_posix(), 'note': note}


def downloaded_data_status():
    rows = [
        _dataset_row('market_latest', '当前行情缓存', '行情K线/快照', CONSOLE / 'datahub' / 'market_latest.json', '自动刷新行情写入的本地行情缓存'),
        _dataset_row('datahub_symbols', '统一标的缓存', '标的列表', CONSOLE / 'datahub' / 'datahub_symbols.json', 'Data Hub 当前可见标的'),
        _dataset_row('universe_settings', '当前Universe配置', '配置', CONSOLE / 'market' / 'universe_settings.private.json', '自动刷新行情使用的股票池配置'),
        _dataset_row('qmt_universe_sync', 'QMT同步汇总', 'QMT列表同步结果', SYNC_FILE, 'get_stock_list_in_sector 同步汇总'),
    ]
    for key, path in GROUP_FILES.items():
        definition = GROUP_DEFS[key]
        rows.append(_dataset_row(key, definition['name'], 'QMT真实列表', path, definition['description']))
    ready = sum(1 for row in rows if row['status'] == 'READY')
    return payload(status='READY', source='downloaded_data_inventory', data={'rows': rows, 'readyCount': ready, 'totalCount': len(rows), 'generatedAt': _now()})
