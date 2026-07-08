from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from qmt_ai_trading.common.json_safe import json_safe

from .common import CONSOLE, payload, read_json

CLEAN_ROOT = CONSOLE / 'data_cleaning'
QUALITY_ROOT = CONSOLE / 'data_quality'
CLEANED_ROOT = CLEAN_ROOT / 'cleaned'
REPORT_FILE = QUALITY_ROOT / 'cleaning_report.json'
ROWS_FILE = QUALITY_ROOT / 'quality_rows.json'
ISSUES_FILE = QUALITY_ROOT / 'quality_issues.json'
RUNS_FILE = QUALITY_ROOT / 'cleaning_runs.json'

REQUIRED_FIELDS = ('open', 'high', 'low', 'close')
TIME_KEYS = ('time', 'datetime', 'updated_at', 'updatedAt', 'timestamp', 'stime', 'date', 'tradeDate', 'index')
PRICE_KEYS = {
    'open': ('open', 'openPrice'),
    'high': ('high', 'highPrice'),
    'low': ('low', 'lowPrice'),
    'close': ('close', 'latest', 'price', 'lastPrice'),
    'pre_close': ('pre_close', 'preClose', 'last_close', 'lastClose'),
    'volume': ('volume', 'vol'),
    'amount': ('amount', 'turnover'),
}


def _now() -> str:
    return datetime.now().isoformat(timespec='seconds')


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception:
        return default
    return default


def _write_json(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(data), ensure_ascii=False, indent=2), encoding='utf-8')
    return path.as_posix()


def _first_array(obj: Any) -> list[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ('rows', 'bars', 'data', 'items', 'records', 'latest', 'snapshots'):
            value = obj.get(key)
            if isinstance(value, list):
                return value
        for value in obj.values():
            arr = _first_array(value)
            if arr:
                return arr
    return []


def _normalize_symbol(value: Any) -> str:
    raw = str(value or '').strip().upper().replace(' ', '')
    if not raw:
        return ''
    prefix = re.fullmatch(r'(SH|SZ|BJ)[\.:-]?(\d{6})', raw)
    suffix = re.fullmatch(r'(\d{6})[\.:-]?(SH|SZ|BJ)', raw)
    if prefix:
        return f'{prefix.group(2)}.{prefix.group(1)}'
    if suffix:
        return f'{suffix.group(1)}.{suffix.group(2)}'
    if re.fullmatch(r'\d{6}', raw):
        if raw.startswith(('5', '6', '9')):
            return raw + '.SH'
        if raw.startswith(('0', '1', '2', '3')):
            return raw + '.SZ'
        if raw.startswith(('4', '8')):
            return raw + '.BJ'
    return raw if re.fullmatch(r'\d{6}\.(SH|SZ|BJ)', raw) else ''


def _num(value: Any) -> float | None:
    try:
        if value in (None, ''):
            return None
        number = float(value)
        if number != number:
            return None
        return number
    except Exception:
        return None


def _pick_num(row: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key in row:
            num = _num(row.get(key))
            if num is not None:
                return num
    return None


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


def _row_time_ms(row: dict[str, Any]) -> int | None:
    for key in TIME_KEYS:
        if key in row:
            ms = _parse_time_ms(row.get(key))
            if ms is not None:
                return ms
    return None


def _issue(dataset: str, symbol: str, time_text: str, level: str, typ: str, message: str, source_path: str) -> dict[str, Any]:
    return {
        'id': f'{dataset}-{symbol}-{time_text}-{typ}-{abs(hash(message)) % 100000}',
        'dataset': dataset,
        'symbol': symbol or '-',
        'time': time_text or '-',
        'level': level,
        'type': typ,
        'message': message,
        'sourcePath': source_path,
    }


def _source_files() -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    latest_path = CONSOLE / 'datahub' / 'market_latest.json'
    if latest_path.exists():
        sources.append({'dataset': '当前行情缓存', 'layer': 'latest_cache', 'period': 'unknown', 'path': latest_path, 'kind': 'latest'})
    history_root = CONSOLE / 'market_history'
    if history_root.exists():
        for path in history_root.rglob('*.json'):
            if path.name == 'history_download_result.json':
                continue
            rel = path.relative_to(history_root)
            parts = rel.parts
            period = parts[0] if len(parts) >= 1 else 'unknown'
            layer = parts[1] if len(parts) >= 2 else 'unknown'
            sources.append({'dataset': f'历史行情/{period}/{layer}', 'layer': layer, 'period': period, 'path': path, 'kind': 'history'})
    return sources


def _standardize_rows(source: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    path = Path(source['path'])
    doc = _read_json(path, {})
    rows = _first_array(doc)
    source_symbol = _normalize_symbol(doc.get('symbol')) if isinstance(doc, dict) else ''
    period = str(doc.get('period') or source.get('period') or 'unknown') if isinstance(doc, dict) else str(source.get('period') or 'unknown')
    dataset = str(source.get('dataset') or path.name)
    issues: list[dict[str, Any]] = []
    cleaned: list[dict[str, Any]] = []
    seen: dict[tuple[str, str, str], int] = {}
    stats = {'input': 0, 'cleaned': 0, 'missing': 0, 'abnormal': 0, 'duplicate': 0, 'dropped': 0}

    for idx, item in enumerate(rows):
        if not isinstance(item, dict):
            stats['dropped'] += 1
            issues.append(_issue(dataset, '', '', 'ERROR', 'ROW_TYPE', '行不是对象，已丢弃', path.as_posix()))
            continue
        stats['input'] += 1
        symbol = _normalize_symbol(item.get('symbol') or item.get('code') or item.get('ts_code') or source_symbol)
        ms = _row_time_ms(item)
        time_text = _fmt_ms(ms)
        missing_fields: list[str] = []
        if not symbol:
            missing_fields.append('symbol')
        if ms is None:
            missing_fields.append('datetime')
        values: dict[str, float | None] = {field: _pick_num(item, PRICE_KEYS[field]) for field in PRICE_KEYS}
        for field in REQUIRED_FIELDS:
            if values[field] is None:
                missing_fields.append(field)
        if missing_fields:
            stats['missing'] += len(missing_fields)
            stats['dropped'] += 1
            issues.append(_issue(dataset, symbol, time_text, 'ERROR', 'MISSING_FIELD', '缺失字段：' + ', '.join(missing_fields), path.as_posix()))
            continue

        open_p = values['open'] or 0
        high = values['high'] or 0
        low = values['low'] or 0
        close = values['close'] or 0
        volume = values['volume'] if values['volume'] is not None else 0
        amount = values['amount'] if values['amount'] is not None else 0
        abnormal_messages: list[str] = []
        if min(open_p, high, low, close) <= 0:
            abnormal_messages.append('OHLC 存在非正价格')
        if high < low:
            abnormal_messages.append('high < low')
        if high >= low and (open_p < low or open_p > high or close < low or close > high):
            abnormal_messages.append('open/close 超出 high-low 区间')
        if volume < 0 or amount < 0:
            abnormal_messages.append('成交量/成交额为负')
        pre_close = values['pre_close']
        if pre_close and pre_close > 0:
            pct = abs(close / pre_close - 1)
            if pct > 0.5:
                abnormal_messages.append('相对昨收跳变超过 50%，需确认复权/除权/异常行情')
        if abnormal_messages:
            stats['abnormal'] += len(abnormal_messages)
            issues.append(_issue(dataset, symbol, time_text, 'WARNING', 'ABNORMAL_VALUE', '；'.join(abnormal_messages), path.as_posix()))

        key = (symbol, period, time_text)
        row = {
            'symbol': symbol,
            'datetime': time_text,
            'date': time_text[:10],
            'period': period,
            'open': open_p,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'amount': amount,
            'pre_close': pre_close,
            'sourcePath': path.as_posix(),
            'cleanedAt': _now(),
            'readOnly': True,
        }
        if key in seen:
            stats['duplicate'] += 1
            issues.append(_issue(dataset, symbol, time_text, 'WARNING', 'DUPLICATE', '重复记录：symbol + period + datetime，已保留最后一条', path.as_posix()))
            cleaned[seen[key]] = row
        else:
            seen[key] = len(cleaned)
            cleaned.append(row)
    stats['cleaned'] = len(cleaned)
    return cleaned, issues, stats


def _write_cleaned(source: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ''
    first = rows[0]
    symbol = str(first.get('symbol') or 'UNKNOWN')
    period = str(first.get('period') or source.get('period') or 'unknown')
    layer = str(source.get('layer') or 'unknown')
    out = CLEANED_ROOT / period / layer / f'{symbol}.json'
    times = [_parse_time_ms(row.get('datetime')) for row in rows]
    times = [t for t in times if t is not None]
    doc = {
        'symbol': symbol,
        'period': period,
        'layer': layer,
        'recordCount': len(rows),
        'startTime': _fmt_ms(min(times)) if times else '',
        'endTime': _fmt_ms(max(times)) if times else '',
        'rows': rows,
        'cleanedAt': _now(),
        'readOnly': True,
        'noAccountQuery': True,
        'noOrderSubmitted': True,
    }
    return _write_json(out, doc)


def _row_from_dataset(dataset: str, period: str, layer: str, cleaned: list[dict[str, Any]], issues: list[dict[str, Any]], stats: dict[str, int], cleaned_path: str, source_path: str) -> dict[str, Any]:
    symbols = sorted({str(row.get('symbol')) for row in cleaned if row.get('symbol')})
    times = [_parse_time_ms(row.get('datetime')) for row in cleaned]
    times = [t for t in times if t is not None]
    errors = [x for x in issues if x.get('level') == 'ERROR']
    warnings = [x for x in issues if x.get('level') == 'WARNING']
    passed = not errors and stats.get('cleaned', 0) > 0
    status = 'PASS' if passed and not warnings else ('WARN' if not errors and warnings else 'FAIL')
    latest = _fmt_ms(max(times)) if times else ''
    return {
        'dataset': dataset,
        'period': period,
        'layer': layer,
        'tradeDate': latest[:10],
        'startTime': _fmt_ms(min(times)) if times else '',
        'endTime': latest,
        'timeRange': f'{_fmt_ms(min(times))} 至 {latest}' if times else '',
        'stockCount': len(symbols),
        'recordCount': stats.get('cleaned', 0),
        'inputRows': stats.get('input', 0),
        'missingFields': stats.get('missing', 0),
        'abnormalValues': stats.get('abnormal', 0),
        'duplicateRows': stats.get('duplicate', 0),
        'droppedRows': stats.get('dropped', 0),
        'passed': passed,
        'status': status,
        'sourcePath': source_path,
        'cleanedPath': cleaned_path,
    }


def run_data_cleaning(body: dict[str, Any] | None = None):
    body = body or {}
    mode = str(body.get('mode') or 'full_pipeline')
    sources = _source_files()
    rows: list[dict[str, Any]] = []
    all_issues: list[dict[str, Any]] = []
    cleaned_file_count = 0
    total_cleaned = 0
    started_at = _now()

    for source in sources:
        cleaned, issues, stats = _standardize_rows(source)
        cleaned_path = _write_cleaned(source, cleaned)
        if cleaned_path:
            cleaned_file_count += 1
        total_cleaned += len(cleaned)
        all_issues.extend(issues)
        rows.append(_row_from_dataset(str(source['dataset']), str(source.get('period') or 'unknown'), str(source.get('layer') or 'unknown'), cleaned, issues, stats, cleaned_path, Path(source['path']).as_posix()))

    errors = sum(1 for x in all_issues if x.get('level') == 'ERROR')
    warnings = sum(1 for x in all_issues if x.get('level') == 'WARNING')
    passed = sum(1 for row in rows if row.get('status') == 'PASS')
    failed = sum(1 for row in rows if row.get('status') == 'FAIL')
    warn = sum(1 for row in rows if row.get('status') == 'WARN')
    symbols = sorted({sym for row in rows for sym in []})
    for row in rows:
        pass
    overview = {
        'status': 'PASS' if rows and not errors else ('WARN' if rows and warnings and not errors else ('FAIL' if errors else 'NO_DATA')),
        'mode': mode,
        'datasetCount': len(rows),
        'passedCount': passed,
        'failedCount': failed,
        'warningCount': warn,
        'recordCount': total_cleaned,
        'symbolCount': sum(int(row.get('stockCount') or 0) for row in rows),
        'issueCount': len(all_issues),
        'errorCount': errors,
        'warningIssueCount': warnings,
        'cleanedFileCount': cleaned_file_count,
        'startedAt': started_at,
        'finishedAt': _now(),
        'sourcePath': REPORT_FILE.as_posix(),
        'readOnly': True,
        'noAccountQuery': True,
        'noOrderSubmitted': True,
    }
    run = {
        'runId': datetime.now().strftime('%Y%m%d%H%M%S'),
        'name': '数据清洗流水线',
        'mode': mode,
        'status': overview['status'],
        'startedAt': started_at,
        'finishedAt': overview['finishedAt'],
        'datasetCount': len(rows),
        'recordCount': total_cleaned,
        'issueCount': len(all_issues),
        'cleanedFileCount': cleaned_file_count,
        'sourcePath': REPORT_FILE.as_posix(),
    }
    old_runs = _read_json(RUNS_FILE, [])
    if not isinstance(old_runs, list):
        old_runs = []
    runs = [run] + old_runs[:19]

    report = {'overview': overview, 'rows': rows, 'issues': all_issues[:5000], 'runs': runs, 'updatedAt': _now()}
    _write_json(REPORT_FILE, report)
    _write_json(ROWS_FILE, rows)
    _write_json(ISSUES_FILE, all_issues[:5000])
    _write_json(RUNS_FILE, runs)
    return payload(status=overview['status'], source='data_cleaning_pipeline', data=report)


def _empty_status() -> dict[str, Any]:
    return {
        'overview': {'status': 'NO_DATA', 'datasetCount': 0, 'passedCount': 0, 'failedCount': 0, 'warningCount': 0, 'recordCount': 0, 'symbolCount': 0, 'issueCount': 0, 'sourcePath': REPORT_FILE.as_posix()},
        'rows': [],
        'issues': [],
        'runs': [],
        'updatedAt': '',
    }


def cleaning_status():
    report = _read_json(REPORT_FILE, {})
    if not isinstance(report, dict) or not report:
        report = _empty_status()
    return payload(status='READY', source='data_cleaning_report', data=report)


def quality_overview():
    report = _read_json(REPORT_FILE, {})
    if isinstance(report, dict) and report.get('overview'):
        return payload(status='READY', source='data_cleaning_report', data=report['overview'])
    return payload(status='READY', source='data_cleaning_report', data=_empty_status()['overview'])


def data_quality_rows():
    rows = _read_json(ROWS_FILE, [])
    if not isinstance(rows, list):
        rows = []
    return payload(status='READY', source='data_cleaning_quality_rows', data=rows)


def quality_issues():
    issues = _read_json(ISSUES_FILE, [])
    if not isinstance(issues, list):
        issues = []
    return payload(status='READY', source='data_cleaning_quality_issues', data=issues)


def cleaning_runs():
    runs = _read_json(RUNS_FILE, [])
    if not isinstance(runs, list):
        runs = []
    return payload(status='READY', source='data_cleaning_runs', data=runs)
