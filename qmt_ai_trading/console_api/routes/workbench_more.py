from __future__ import annotations

from .common import payload, read_json
from . import workbench


def risk_overview():
    overview = workbench.dashboard_overview().get('data', {})
    return payload(status='READY', source='backend_adapter', data=overview.get('riskOverview', {}))


def order_plan():
    rows = []
    for row in workbench.order_plan().get('data', []):
        raw_side = row.get('side')
        risk_text = str(row.get('riskDecision') or row.get('riskCheck') or '')
        rows.append({
            **row,
            'side': '卖出' if str(raw_side).upper() == 'SELL' else '买入',
            'rawSide': raw_side,
            'riskCheck': 'PASS' if 'PASS' in risk_text.upper() else 'LOW',
            'riskDecision': risk_text,
            'businessStatus': row.get('status') or '',
            'previewOnly': True,
        })
    return payload(status='READY', source='portfolio_preview', data=rows)


def _latest_backtest_task():
    replay = read_json('backtest', 'shadow_replay_latest.json', {})
    return {
        'id': 'shadow-replay-latest',
        'name': 'Shadow Replay latest',
        'strategy': 'console_shadow_replay',
        'universe': 'backend_artifacts',
        'range': replay.get('range', '') if isinstance(replay, dict) else '',
        'capital': 0,
        'rebalance': 'artifact',
        'status': replay.get('status', 'DATA_MISSING') if isinstance(replay, dict) else 'DATA_MISSING',
        'createdAt': replay.get('created_at', '') if isinstance(replay, dict) else '',
        'cost': '',
    }


def backtest_tasks():
    task = _latest_backtest_task()
    return payload(status='READY', source='backtest_artifacts', data=[task] if task['status'] != 'DATA_MISSING' else [])


def backtest_report():
    task = _latest_backtest_task()
    data = {'task': task, 'curve': workbench._curve(), 'metrics': {'annualReturn': 0, 'maxDrawdown': 0, 'sharpe': 0, 'calmar': 0, 'winRate': 0, 'profitLossRatio': 0, 'turnover': 0, 'trades': 0, 'excessReturn': 0}, 'positions': [], 'trades': []}
    return payload(status='READY', source='synthetic_until_backtest_report_connected', data=data)


def monitoring_realtime():
    return payload(status='READY', source='adapter', data={'curve': workbench._curve(60), 'holdings': [], 'orders': [], 'signals': workbench._signals(), 'latency': {'api': 'local'}})


def monitoring_attribution():
    return payload(status='READY', source='adapter', data=[])


def monitoring_execution_quality():
    return payload(status='READY', source='adapter', data={})


def monitoring_daily_review():
    events = workbench.dashboard_events().get('data', [])
    return payload(status='READY', source='task_history', data={'events': events, 'trades': [], 'summary': 'Task history is connected. Attribution and execution quality will be connected later.'})
