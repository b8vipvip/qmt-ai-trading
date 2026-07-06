from __future__ import annotations

from datetime import datetime
from typing import Any

from .common import CONSOLE, payload, read_json


def _artifact_path(module: str, name: str) -> str:
    return (CONSOLE / module / name).as_posix()


def _first_array(obj: Any) -> list[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for value in obj.values():
            arr = _first_array(value)
            if arr:
                return arr
    return []


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ''):
            return default
        return float(value)
    except Exception:
        return default


def _market_rows() -> list[dict[str, Any]]:
    data = read_json('datahub', 'market_latest.json', {})
    return [row for row in _first_array(data) if isinstance(row, dict)]


def _symbols() -> list[str]:
    data = read_json('datahub', 'datahub_symbols.json', {'symbols': []})
    if isinstance(data, dict) and isinstance(data.get('symbols'), list):
        return [str(x) for x in data.get('symbols', [])]
    return []


def market_quotes():
    rows = []
    for idx, item in enumerate(_market_rows()):
        symbol = item.get('symbol') or item.get('code') or item.get('ts_code') or item.get('ticker') or f'ROW-{idx + 1}'
        latest = _num(item.get('latest') or item.get('price') or item.get('close') or item.get('lastPrice'))
        pre_close = _num(item.get('pre_close') or item.get('preClose') or item.get('last_close') or item.get('close'), latest)
        change = latest - pre_close if latest and pre_close else 0
        change_pct = round(change / pre_close * 100, 4) if pre_close else 0
        rows.append({
            'id': str(symbol),
            'symbol': str(symbol),
            'name': item.get('name') or item.get('stock_name') or str(symbol),
            'time': item.get('time') or item.get('datetime') or item.get('updated_at') or '',
            'open': _num(item.get('open')),
            'high': _num(item.get('high')),
            'low': _num(item.get('low')),
            'close': _num(item.get('close'), latest),
            'latest': latest,
            'preClose': pre_close,
            'change': round(change, 4),
            'changePct': change_pct,
            'volume': _num(item.get('volume') or item.get('vol')),
            'amount': _num(item.get('amount') or item.get('turnover')),
            'status': 'NORMAL' if symbol else 'INVALID',
            'source': item.get('source') or 'datahub.market_latest',
            'sourcePath': _artifact_path('datahub', 'market_latest.json'),
        })
    return payload(status='READY', source='datahub_market_latest', generated_at=datetime.now().isoformat(timespec='seconds'), data=rows)


def market_summary():
    quotes = market_quotes().get('data', [])
    symbols = _symbols()
    up = sum(1 for row in quotes if _num(row.get('changePct')) > 0)
    down = sum(1 for row in quotes if _num(row.get('changePct')) < 0)
    flat = max(0, len(quotes) - up - down)
    return payload(status='READY', source='datahub_market_latest', data={
        'quoteCount': len(quotes),
        'symbolCount': len(symbols),
        'upCount': up,
        'downCount': down,
        'flatCount': flat,
        'latestTime': max([str(row.get('time') or '') for row in quotes], default=''),
        'sourcePath': _artifact_path('datahub', 'market_latest.json'),
    })
