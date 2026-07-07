from __future__ import annotations

from dataclasses import asdict
from typing import Any
from .common import CONSOLE, payload, read_json
from . import workbench_api_config


def _artifact_path(module: str, name: str) -> str:
    return (CONSOLE / module / name).as_posix()


def _first_array(obj: Any) -> list[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ('records', 'items', 'rows', 'data', 'news', 'fundamentals', 'latest'):
            if isinstance(obj.get(key), list):
                return obj[key]
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


def _configs_for(*purposes: str) -> list[dict[str, Any]]:
    rows = []
    for cfg in workbench_api_config._load():
        cfg_purposes = workbench_api_config._normalize_purposes(cfg)
        if 'all' in cfg_purposes or any(p in cfg_purposes for p in purposes):
            rows.append(cfg)
    return rows


def fundamental_sources():
    configs = _configs_for('fundamental')
    rows = []
    for cfg in configs:
        rows.append({
            'name': cfg.get('name') or cfg.get('id'),
            'status': 'READY' if cfg.get('enabled') else 'DISABLED',
            'updatedAt': cfg.get('updatedAt') or '',
            'records': 0,
            'latency': 'configured',
            'coverage': 0,
            'missingRate': 0,
            'provider': cfg.get('provider'),
            'sourcePath': workbench_api_config.CONFIG_FILE.as_posix(),
        })
    return payload(status='READY', source='api_config_store', data=rows)


def fundamental_records():
    doc = read_json('datahub', 'fundamental_latest.json', {})
    rows = []
    for idx, item in enumerate(_first_array(doc)):
        if not isinstance(item, dict):
            continue
        symbol = item.get('symbol') or item.get('ts_code') or item.get('code') or f'ROW-{idx + 1}'
        rows.append({
            'symbol': str(symbol),
            'name': item.get('name') or item.get('stock_name') or str(symbol),
            'reportDate': item.get('reportDate') or item.get('report_date') or item.get('ann_date') or '',
            'pe': _num(item.get('pe') or item.get('pe_ttm')),
            'pb': _num(item.get('pb')),
            'roe': _num(item.get('roe') or item.get('roe_dt')),
            'revenueGrowth': _num(item.get('revenueGrowth') or item.get('revenue_growth')),
            'netProfitGrowth': _num(item.get('netProfitGrowth') or item.get('netprofit_growth')),
            'status': 'READY',
            'sourcePath': _artifact_path('datahub', 'fundamental_latest.json'),
        })
    return payload(status='READY', source='fundamental_artifacts', data=rows)


def news_items():
    doc = read_json('datahub', 'news_latest.json', {})
    rows = []
    for idx, item in enumerate(_first_array(doc)):
        if not isinstance(item, dict):
            continue
        rows.append({
            'id': item.get('id') or item.get('news_id') or f'news-{idx + 1}',
            'time': item.get('time') or item.get('datetime') or item.get('publish_time') or '',
            'type': item.get('type') or item.get('category') or 'NEWS',
            'title': item.get('title') or item.get('content') or '',
            'symbols': ','.join(item.get('symbols') or []) if isinstance(item.get('symbols'), list) else str(item.get('symbols') or item.get('symbol') or ''),
            'sentiment': item.get('sentiment') or 'UNKNOWN',
            'impact': item.get('impact') or 'UNKNOWN',
            'source': item.get('source') or item.get('provider') or '',
            'sourcePath': _artifact_path('datahub', 'news_latest.json'),
        })
    return payload(status='READY', source='news_artifacts', data=rows)


def quality_overview():
    datasets = [
        ('行情', 'datahub', 'market_latest.json'),
        ('基本面', 'datahub', 'fundamental_latest.json'),
        ('公告新闻', 'datahub', 'news_latest.json'),
    ]
    dataset_count = 0
    record_count = 0
    warning_count = 0
    for _, module, name in datasets:
        rows = _first_array(read_json(module, name, {}))
        if rows:
            dataset_count += 1
            record_count += len(rows)
        else:
            warning_count += 1
    summary = {'datasetCount': dataset_count, 'passedCount': dataset_count, 'failedCount': 0, 'warningCount': warning_count, 'recordCount': record_count, 'symbolCount': 0, 'sourcePath': CONSOLE.as_posix()}
    return payload(status='READY', source='quality_adapter', data=summary)


def task_catalog():
    try:
        from qmt_ai_trading.console_api.task_registry import list_tasks
        tasks = [asdict(t) for t in list_tasks()]
    except Exception:
        tasks = []
    return payload(status='READY', source='task_registry', data=tasks)
