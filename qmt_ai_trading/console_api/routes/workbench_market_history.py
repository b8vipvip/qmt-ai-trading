from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from qmt_ai_trading.common.json_safe import json_safe
from qmt_ai_trading.market_gateway.xtdata_live_provider import _normalize_bars

from .common import CONSOLE, payload
from . import workbench_market, workbench_market_sync, workbench_system

HISTORY_ROOT = CONSOLE / 'market_history'
RESULT_FILE = HISTORY_ROOT / 'history_download_result.json'

LAYER_PRESETS = {
    'selection_daily': {
        'name': '第一层：全市场日线选股库',
        'description': '用于全市场选股、因子研究、回测、流动性过滤和风险基准。建议覆盖全A、ETF、大盘/基准指数、行业/板块指数，下载5-10年日线。',
        'groups': ['all_a', 'etf', 'broad_market', 'sector_index'],
        'periods': ['1d'],
        'defaultPeriod': '1d',
        'defaultYears': 5,
        'defaultMaxSymbols': 6000,
        'priority': '必须建设',
    },
    'candidate_intraday': {
        'name': '第二层：候选池分钟线',
        'description': '用于盘中择时、买卖点优化、成交量放大和日内风控。只建议对候选池/当前Universe下载，不建议全A分钟线全量铺开。',
        'groups': ['current_universe'],
        'periods': ['60m', '30m', '15m', '5m', '1m'],
        'defaultPeriod': '5m',
        'defaultYears': 1,
        'defaultMaxSymbols': 500,
        'priority': '第二阶段',
    },
    'execution_tick': {
        'name': '第三层：实盘交易池 Tick / Level2',
        'description': '用于实盘执行、滑点、盘口流动性和成交冲击分析。只对持仓、今日交易计划和高优先级监控池订阅/下载。当前只展示规划，避免全市场高频数据压垮本地环境。',
        'groups': ['current_universe'],
        'periods': ['tick', 'level2'],
        'defaultPeriod': 'tick',
        'defaultYears': 0,
        'defaultMaxSymbols': 100,
        'priority': '实盘前建设',
        'plannedOnly': True,
    },
}

PERIOD_DAYS_PER_YEAR = {
    '1d': 250,
    '60m': 250 * 5,
    '30m': 250 * 10,
    '15m': 250 * 20,
    '5m': 250 * 48,
    '1m': 250 * 240,
}


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
    path.write_text(json.dumps(json_safe(data), ensure_ascii=False, indent=2), encoding='utf-8')
    return path.as_posix()


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


def _count_for_period(period: str, years: int) -> int:
    years = max(0, min(15, int(years or 0)))
    if period in ('tick', 'level2'):
        return 0
    return max(1, min(50000, PERIOD_DAYS_PER_YEAR.get(period, 250) * max(1, years)))


def _symbols_from_group(group: str) -> list[str]:
    if group == 'current_universe':
        universe = workbench_market._universe_settings()
        return list(universe.get('symbols') or [])
    path = workbench_market_sync.GROUP_FILES.get(group)
    if path:
        data = _read_json(path, {})
        if isinstance(data, dict) and isinstance(data.get('symbols'), list):
            return list(data.get('symbols') or [])
    definition = workbench_market_sync.GROUP_DEFS.get(group, {})
    return workbench_market_sync._dedupe_symbols(definition.get('fixedSymbols') or [])


def _unique_symbols(groups: list[str]) -> tuple[list[str], dict[str, int]]:
    out: list[str] = []
    seen = set()
    group_counts: dict[str, int] = {}
    for group in groups:
        symbols = _symbols_from_group(group)
        group_counts[group] = len(symbols)
        for symbol in symbols:
            if symbol not in seen:
                seen.add(symbol)
                out.append(symbol)
    return out, group_counts


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


def _bar_time_ms(row: dict[str, Any]) -> int | None:
    for key in ('time', 'datetime', 'updated_at', 'updatedAt', 'timestamp', 'stime', 'date', 'tradeDate', 'index'):
        if key in row:
            ms = _parse_time_ms(row.get(key))
            if ms is not None:
                return ms
    return None


def _fmt_ms(ms: int | None) -> str:
    return datetime.fromtimestamp(ms / 1000).isoformat(timespec='seconds') if ms is not None else ''


def _download_symbol_bars(xtdata: Any, symbol: str, period: str, count: int) -> list[dict[str, Any]]:
    if hasattr(xtdata, 'get_market_data_ex'):
        raw = xtdata.get_market_data_ex([], [symbol], period=period, count=count)
    else:
        raw = xtdata.get_market_data([], [symbol], period=period, count=count)
    rows = _normalize_bars(raw, symbol)
    return [row for row in rows if isinstance(row, dict)]


def _layer_rows() -> list[dict[str, Any]]:
    rows = []
    for key, value in LAYER_PRESETS.items():
        rows.append({'key': key, **value, 'groupLabels': value.get('groups', []), 'periodLabels': value.get('periods', [])})
    return rows


def market_history_status():
    data = _read_json(RESULT_FILE, {})
    if not isinstance(data, dict) or not data:
        data = {'status': 'NOT_DOWNLOADED', 'message': '尚未执行历史行情下载任务', 'runs': [], 'latestRun': None, 'sourcePath': RESULT_FILE.as_posix()}
    return payload(status='READY', source='market_history_download', data={**data, 'layers': _layer_rows()})


def run_market_history_download(body: dict[str, Any] | None = None):
    body = body or {}
    layer_key = str(body.get('layer') or 'selection_daily')
    layer = LAYER_PRESETS.get(layer_key) or LAYER_PRESETS['selection_daily']
    period = str(body.get('period') or layer['defaultPeriod'])
    years = int(body.get('years') or layer['defaultYears'])
    max_symbols = max(1, min(10000, int(body.get('maxSymbols') or layer['defaultMaxSymbols'])))
    groups = body.get('groups') or layer.get('groups') or ['current_universe']
    if isinstance(groups, str):
        groups = [groups]
    groups = [g for g in groups if isinstance(g, str)]

    if layer.get('plannedOnly') or period in {'tick', 'level2'}:
        result = {
            'status': 'PLANNED_ONLY',
            'layer': layer_key,
            'layerName': layer['name'],
            'period': period,
            'years': years,
            'maxSymbols': max_symbols,
            'message': 'Tick / Level2 属于实盘执行层，当前只做规划展示，不执行全市场下载。',
            'generatedAt': _now(),
            'readOnly': True,
            'noXtTrader': True,
            'noOrderSubmitted': True,
        }
        _append_result(result)
        return payload(status='READY', source='market_history_download', data=_read_json(RESULT_FILE, result))

    symbols, group_counts = _unique_symbols(groups)
    selected_symbols = symbols[:max_symbols]
    if not selected_symbols:
        result = {'status': 'FAILED', 'layer': layer_key, 'layerName': layer['name'], 'message': '没有可下载标的。请先同步 QMT 真实列表，或应用一个 Universe。', 'groups': groups, 'groupCounts': group_counts, 'generatedAt': _now(), 'readOnly': True, 'noOrderSubmitted': True}
        _append_result(result)
        return payload(ok=False, status='FAILED', error=result['message'], data=_read_json(RESULT_FILE, result))

    xtdata, import_status = _import_xtdata()
    if xtdata is None:
        result = {'status': 'FAILED', 'layer': layer_key, 'layerName': layer['name'], 'message': f'xtquant.xtdata 导入失败：{import_status}', 'importStatus': import_status, 'groups': groups, 'groupCounts': group_counts, 'symbolCount': len(selected_symbols), 'generatedAt': _now(), 'readOnly': True, 'noOrderSubmitted': True}
        _append_result(result)
        return payload(ok=False, status='FAILED', error=result['message'], data=_read_json(RESULT_FILE, result))

    count = _count_for_period(period, years)
    run_id = datetime.now().strftime('%Y%m%d%H%M%S')
    out_dir = HISTORY_ROOT / period / layer_key
    success = 0
    failed = 0
    total_records = 0
    start_ms: int | None = None
    end_ms: int | None = None
    errors: list[str] = []
    sample_files: list[str] = []

    for symbol in selected_symbols:
        try:
            rows = _download_symbol_bars(xtdata, symbol, period, count)
            times = [_bar_time_ms(row) for row in rows]
            times = [x for x in times if x is not None]
            if times:
                start_ms = min(times) if start_ms is None else min(start_ms, min(times))
                end_ms = max(times) if end_ms is None else max(end_ms, max(times))
            doc = {
                'symbol': symbol,
                'period': period,
                'layer': layer_key,
                'rows': rows,
                'recordCount': len(rows),
                'startTime': _fmt_ms(min(times)) if times else '',
                'endTime': _fmt_ms(max(times)) if times else '',
                'downloadedAt': _now(),
                'source': 'xtdata.get_market_data_ex',
                'readOnly': True,
                'noXtTrader': True,
                'noOrderSubmitted': True,
            }
            path = out_dir / f'{symbol}.json'
            saved = _write_json(path, doc)
            if len(sample_files) < 5:
                sample_files.append(saved)
            total_records += len(rows)
            success += 1
        except Exception as exc:
            failed += 1
            if len(errors) < 20:
                errors.append(f'{symbol}: {type(exc).__name__}: {exc}')

    result = {
        'status': 'READY' if success else 'FAILED',
        'runId': run_id,
        'layer': layer_key,
        'layerName': layer['name'],
        'period': period,
        'years': years,
        'countPerSymbol': count,
        'groups': groups,
        'groupCounts': group_counts,
        'requestedSymbolCount': len(symbols),
        'downloadedSymbolCount': success,
        'failedSymbolCount': failed,
        'recordCount': total_records,
        'startTime': _fmt_ms(start_ms),
        'endTime': _fmt_ms(end_ms),
        'timeRange': f'{_fmt_ms(start_ms)} 至 {_fmt_ms(end_ms)}' if start_ms and end_ms else '',
        'outputDir': out_dir.as_posix(),
        'sampleFiles': sample_files,
        'errors': errors,
        'message': f'{layer["name"]}下载完成：成功 {success} 个标的，失败 {failed} 个，记录 {total_records} 条。',
        'generatedAt': _now(),
        'readOnly': True,
        'noXtTrader': True,
        'noAccountQuery': True,
        'noOrderSubmitted': True,
    }
    _append_result(result)
    return payload(status=result['status'], source='market_history_download', data=_read_json(RESULT_FILE, result))


def _append_result(result: dict[str, Any]) -> None:
    old = _read_json(RESULT_FILE, {})
    runs = old.get('runs') if isinstance(old, dict) and isinstance(old.get('runs'), list) else []
    runs = [result] + runs[:19]
    doc = {'status': result.get('status'), 'message': result.get('message'), 'latestRun': result, 'runs': runs, 'updatedAt': _now(), 'sourcePath': RESULT_FILE.as_posix()}
    _write_json(RESULT_FILE, doc)
