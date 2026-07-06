from __future__ import annotations

from .common import payload, read_json
from . import workbench


def backtest_tasks():
    replay = read_json('backtest', 'shadow_replay_latest.json', {})
    task = {
        'id': 'shadow-replay-latest',
        'name': 'Shadow Replay 最新回放',
        'strategy': 'console_shadow_replay',
        'universe': 'backend_artifacts',
        'range': replay.get('range', '') if isinstance(replay, dict) else '',
        'capital': 0,
        'rebalance': 'artifact',
        'status': replay.get('status', 'DATA_MISSING') if isinstance(replay, dict) else 'DATA_MISSING',
        'createdAt': replay.get('created_at', '') if isinstance(replay, dict) else '',
        'cost': '',
    }
    return payload(status='READY', source='backtest_artifacts', data=[task] if task['status'] != 'DATA_MISSING' else [])


def backtest_report():
    return payload(status='READY', source='synthetic_until_backtest_report_connected', data={'curve': workbench._curve(), 'metrics': {}})


def monitoring_realtime():
    return payload(status='READY', source='adapter', data={'curve': workbench._curve(60), 'holdings': [], 'orders': [], 'signals': workbench._signals(), 'latency': {'api': 'local'}})


def monitoring_attribution():
    return payload(status='READY', source='adapter', data=[])


def monitoring_execution_quality():
    return payload(status='READY', source='adapter', data={})


def monitoring_daily_review():
    events = workbench.dashboard_events().get('data', [])
    return payload(status='READY', source='task_history', data={'events': events, 'trades': [], 'summary': '已接入当前 API 进程任务历史；收益归因、成交质量等待后端模块接入。'})
