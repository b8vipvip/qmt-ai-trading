from __future__ import annotations

from dataclasses import asdict
from typing import Any
from .common import CONSOLE, payload, read_json
from . import workbench_task_history


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


def fundamental_sources():
    symbols = read_json('datahub', 'datahub_symbols.json', {'symbols': []})
    count = len(symbols.get('symbols', [])) if isinstance(symbols, dict) else 0
    rows = [
        {'name': '财务报表', 'status': 'PENDING', 'updatedAt': '', 'records': 0, 'latency': '-', 'coverage': 0, 'missingRate': 0, 'sourcePath': 'pending_fundamental_financials'},
        {'name': '估值指标', 'status': 'PENDING', 'updatedAt': '', 'records': 0, 'latency': '-', 'coverage': 0, 'missingRate': 0, 'sourcePath': 'pending_fundamental_valuation'},
        {'name': '统一标的基础信息', 'status': 'READY' if count else 'EMPTY', 'updatedAt': '', 'records': count, 'latency': 'local', 'coverage': count, 'missingRate': 0, 'sourcePath': _artifact_path('datahub', 'datahub_symbols.json')},
    ]
    return payload(status='READY', source='fundamental_adapter', data=rows)


def fundamental_records():
    symbols = read_json('datahub', 'datahub_symbols.json', {'symbols': []})
    rows = []
    if isinstance(symbols, dict):
        for idx, symbol in enumerate(symbols.get('symbols', [])[:50]):
            rows.append({'symbol': str(symbol), 'name': str(symbol), 'reportDate': '', 'pe': 0, 'pb': 0, 'roe': 0, 'revenueGrowth': 0, 'netProfitGrowth': 0, 'status': 'SYMBOL_ONLY', 'sourcePath': _artifact_path('datahub', 'datahub_symbols.json'), 'note': '基础财务接口待接入；当前只展示统一标的池。'})
    return payload(status='READY', source='fundamental_adapter', data=rows)


def news_items():
    history = workbench_task_history.dashboard_events().get('data', [])
    rows = []
    for item in history[:30]:
        rows.append({'id': item.get('id'), 'time': item.get('time'), 'type': '系统事件', 'title': item.get('message'), 'symbols': '', 'sentiment': 'NEUTRAL', 'impact': 'LOW', 'source': item.get('module'), 'sourcePath': item.get('sourcePath')})
    return payload(status='READY', source='news_adapter_from_task_history', data=rows)


def quality_overview():
    market = read_json('datahub', 'market_latest.json', {})
    rows = _first_array(market)
    symbols = sorted({str(x.get('symbol')) for x in rows if isinstance(x, dict) and x.get('symbol')})
    summary = {'datasetCount': 1 if rows else 0, 'passedCount': 1 if rows else 0, 'failedCount': 0, 'warningCount': 0 if rows else 1, 'recordCount': len(rows), 'symbolCount': len(symbols), 'sourcePath': _artifact_path('datahub', 'market_latest.json')}
    return payload(status='READY', source='quality_adapter', data=summary)


def task_catalog():
    try:
        from qmt_ai_trading.console_api.task_registry import list_tasks
        tasks = [asdict(t) for t in list_tasks()]
    except Exception:
        tasks = []
    return payload(status='READY', source='task_registry', data=tasks)
