from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .common import payload, read_json


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
        return float(value)
    except Exception:
        return default


def _asset_doc() -> dict[str, Any]:
    doc = read_json('portfolio', 'portfolio_budget.json', {})
    return doc if isinstance(doc, dict) else {}


def _preview_doc() -> dict[str, Any]:
    doc = read_json('portfolio', 'order_preview_latest.json', {})
    return doc if isinstance(doc, dict) else {}


def _signals() -> list[dict[str, Any]]:
    return [x for x in _first_array(read_json('strategy', 'strategy_signals.json', [])) if isinstance(x, dict)]


def _intents() -> list[dict[str, Any]]:
    return [x for x in _first_array(read_json('strategy', 'trade_intents.json', [])) if isinstance(x, dict)]


def _risk_decisions() -> list[dict[str, Any]]:
    return [x for x in _first_array(read_json('risk', 'risk_decisions.json', [])) if isinstance(x, dict)]


def _candidates() -> list[dict[str, Any]]:
    return [x for x in _first_array(read_json('research', 'factor_candidates.json', [])) if isinstance(x, dict)]


def _curve(days: int = 180) -> list[dict[str, Any]]:
    base = datetime.today() - timedelta(days=days - 1)
    rows = []
    for i in range(days):
        equity = 100 + i * 0.08
        benchmark = 100 + i * 0.05
        rows.append({'date': (base + timedelta(days=i)).strftime('%Y-%m-%d'), 'equity': round(equity, 2), 'benchmark': round(benchmark, 2), 'drawdown': round(min(0, (equity - (100 + i * 0.1)) / 100 * 100), 2)})
    return rows


def dashboard_overview():
    asset = _asset_doc().get('budget') or {}
    cash = _num(asset.get('cash'))
    total_asset = _num(asset.get('total_asset'), cash)
    market_value = _num(asset.get('market_value'))
    position = round((market_value / total_asset * 100), 2) if total_asset else 0
    metrics = [
        {'title': '今日收益', 'value': '0.00%', 'change': '等待实盘收益接入', 'status': 'offline', 'trend': [0, 0, 0, 0, 0, 0, 0]},
        {'title': '累计收益', 'value': '0.00%', 'change': '等待净值曲线接入', 'status': 'offline', 'trend': [0, 0, 0, 0, 0, 0, 0]},
        {'title': '当前总资产', 'value': round(total_asset, 2), 'change': '来自 portfolio_budget', 'status': 'normal' if total_asset else 'warning', 'trend': [total_asset] * 7},
        {'title': '当前仓位', 'value': f'{position}%', 'change': 'market_value / total_asset', 'status': 'normal' if position < 80 else 'warning', 'trend': [position] * 7},
        {'title': '今日成交额', 'value': 0, 'change': '真实成交未接入', 'status': 'offline', 'trend': [0, 0, 0, 0, 0, 0, 0]},
        {'title': '当前最大回撤', 'value': '0.00%', 'change': '等待回撤曲线接入', 'status': 'offline', 'trend': [0, 0, 0, 0, 0, 0, 0]},
        {'title': '运行策略数', 'value': len(_signals()) or len(_intents()), 'change': '来自 strategy artifacts', 'status': 'normal', 'trend': [len(_signals()) or len(_intents())] * 7},
        {'title': '当前风险等级', 'value': 'LOW' if not _risk_decisions() else 'MEDIUM', 'change': '来自 risk decisions', 'status': 'normal' if not _risk_decisions() else 'warning', 'trend': [1, 1, 1, 1, 1, 1, 1]},
    ]
    risk_overview = {'level': metrics[-1]['value'], 'triggerCount': len(_risk_decisions()), 'blockedOrders': 0, 'totalPosition': position, 'maxSinglePosition': 0, 'maxIndustryExposure': 0, 'intradayLoss': 0, 'currentDrawdown': 0, 'losingDays': 0, 'concentration': 0, 'industry': 0, 'total': position, 'dayLoss': 0, 'abnormalOrders': 0, 'disconnects': 0}
    return payload(status='READY', source='backend_adapter', data={'metrics': metrics, 'riskOverview': risk_overview})


def dashboard_strategies():
    rows = []
    for idx, sig in enumerate(_signals() or _intents()):
        symbol = sig.get('symbol') or sig.get('code') or 'UNKNOWN'
        action = sig.get('action') or sig.get('side') or sig.get('signal') or 'HOLD'
        rows.append({'id': f'backend-{idx+1}', 'name': f'Console Strategy {symbol}', 'type': '后端产物', 'mode': '仿真', 'pool': symbol, 'rebalance': 'dry-run', 'todayReturn': 0, 'totalReturn': 0, 'maxDrawdown': 0, 'position': 0, 'signalCount': 1, 'riskStatus': 'LOW', 'status': 'RUNNING', 'sharpe': 0, 'lastAction': action})
    return payload(status='READY', source='strategy_artifacts', data=rows)


def dashboard_equity_curve():
    return payload(status='READY', source='synthetic_until_nav_connected', data=_curve())


def dashboard_events():
    history = read_json('workflow', 'task_history.json', {})
    events = []
    for idx, run in enumerate(_first_array(history)[:30]):
        if not isinstance(run, dict):
            continue
        events.append({'id': run.get('run_id') or f'run-{idx}', 'time': run.get('finished_at') or run.get('started_at') or '', 'level': 'normal' if run.get('status') == 'SUCCESS' else 'warning', 'module': run.get('category') or run.get('task_id') or 'TASK', 'message': run.get('task_name') or run.get('task_id') or '任务执行记录'})
    return payload(status='READY', source='task_history', data=events)


def data_sources():
    market = read_json('datahub', 'market_latest.json', {})
    symbols = read_json('datahub', 'datahub_symbols.json', {})
    count = len(_first_array(market))
    symbol_count = len(symbols.get('symbols', [])) if isinstance(symbols, dict) else 0
    rows = [
        {'name': 'QMT 本地行情', 'status': 'normal' if count else 'warning', 'updatedAt': datetime.now().isoformat(timespec='seconds'), 'records': count, 'latency': 'local', 'missingRate': 0, 'abnormalRate': 0},
        {'name': '统一标的池', 'status': 'normal' if symbol_count else 'warning', 'updatedAt': datetime.now().isoformat(timespec='seconds'), 'records': symbol_count, 'latency': 'local', 'missingRate': 0, 'abnormalRate': 0},
    ]
    return payload(status='READY', source='datahub_artifacts', data=rows)


def data_quality():
    return payload(status='READY', source='adapter', data=[])


def data_tasks():
    return payload(status='READY', source='adapter', data=[])


def factor_list():
    rows = []
    for idx, item in enumerate(_candidates()):
        symbol = item.get('symbol') or 'UNKNOWN'
        rows.append({'id': f'factor-{idx+1}', 'name': f'{symbol} 因子评分', 'type': '多因子', 'version': 'backend', 'universe': symbol, 'icMean': 0, 'rankIc': 0, 'icir': 0, 'longShortReturn': 0, 'turnover': 0, 'status': '候选'})
    return payload(status='READY', source='research_artifacts', data=rows)


def strategy_list():
    return dashboard_strategies()


def order_plan():
    previews = _preview_doc().get('previews') or []
    rows = []
    for idx, item in enumerate(previews):
        if not isinstance(item, dict):
            continue
        rows.append({'id': item.get('preview_id') or f'preview-{idx+1}', 'strategy': item.get('intent_id') or 'portfolio_preview', 'code': item.get('symbol') or '', 'name': item.get('symbol') or '', 'side': item.get('side') or '买入', 'quantity': item.get('preview_quantity') or item.get('quantity') or 0, 'price': item.get('latest_price') or 0, 'type': 'PREVIEW', 'amount': item.get('estimated_amount') or 0, 'riskCheck': item.get('risk_decision') or 'PASS', 'status': item.get('status') or 'PREVIEW', 'createdAt': item.get('created_at') or ''})
    return payload(status='READY', source='portfolio_preview', data=rows)


def holdings():
    positions = _first_array(read_json('account_readonly', 'account_positions_snapshot.json', []))
    rows = []
    for idx, item in enumerate(positions):
        if not isinstance(item, dict):
            continue
        rows.append({'code': item.get('symbol') or item.get('code') or f'POS-{idx+1}', 'name': item.get('name') or item.get('symbol') or '', 'currentQty': item.get('quantity') or item.get('volume') or 0, 'currentWeight': 0, 'targetWeight': 0, 'targetValue': 0, 'diffQty': 0, 'diffAmount': 0, 'riskStatus': 'LOW'})
    return payload(status='READY', source='account_readonly', data=rows)


def trades():
    return payload(status='READY', source='adapter', data=[])


def risk_overview():
    return dashboard_overview()


def risk_rules():
    rules = [
        {'id': 'readonly', 'name': '只读模式强制开启', 'type': '交易前', 'threshold': 'True', 'current': 'True', 'action': '拦截', 'enabled': True, 'lastTriggered': ''},
        {'id': 'no-live', 'name': '实盘交易默认关闭', 'type': '交易前', 'threshold': 'False', 'current': 'False', 'action': '停止交易', 'enabled': True, 'lastTriggered': ''},
        {'id': 'human-approval', 'name': '人工审批闸门', 'type': '交易前', 'threshold': 'Required', 'current': 'Required', 'action': '拦截', 'enabled': True, 'lastTriggered': ''},
    ]
    return payload(status='READY', source='safety_policy', data=rules)


def risk_events():
    rows = []
    for idx, item in enumerate(_risk_decisions()):
        rows.append({'id': item.get('intent_id') or f'risk-{idx+1}', 'time': item.get('created_at') or '', 'strategy': item.get('intent_id') or '', 'rule': 'Risk Gate', 'level': 'LOW' if item.get('decision') in {'PASS_DRY_RUN', 'PASS'} else 'HIGH', 'trigger': item.get('decision') or '', 'threshold': 'safety_policy', 'action': item.get('decision') or '', 'result': item.get('decision') or '', 'operator': 'system'})
    return payload(status='READY', source='risk_artifacts', data=rows)


def deployment_stages():
    rows = [
        {'stage': 'Paper Trading', 'status': 'READY', 'startedAt': '', 'days': 0, 'strategyCount': len(_signals()), 'capital': '0', 'issues': '等待连续运行统计', 'criteria': ['连续运行20个交易日', '无系统崩溃', '信号生成正常']},
        {'stage': 'Shadow Trading', 'status': 'READY', 'startedAt': '', 'days': 0, 'strategyCount': len(_signals()), 'capital': '0', 'issues': '仅读取真实行情，不下单', 'criteria': ['实盘行情稳定', '理论订单生成正常', '无异常订单']},
        {'stage': 'Small Capital', 'status': 'LOCKED', 'startedAt': '', 'days': 0, 'strategyCount': 0, 'capital': '需审批', 'issues': '等待安全审计', 'criteria': ['小资金授权', '最大回撤低于阈值']},
        {'stage': 'Full Live', 'status': 'HIGH_RISK_LOCKED', 'startedAt': '', 'days': 0, 'strategyCount': 0, 'capital': '禁止一键开启', 'issues': '高危权限', 'criteria': ['风控委员会审批', '多签确认']},
    ]
    return payload(status='READY', source='safety_policy', data=rows)


def api_status():
    rows = [
        {'name': '统一控制台 API', 'status': 'normal', 'latency': 'local'},
        {'name': 'QMT / 券商 API', 'status': 'offline', 'latency': '-'},
        {'name': 'Data Hub artifacts', 'status': 'normal', 'latency': 'local'},
        {'name': 'Risk Gate', 'status': 'normal', 'latency': 'local'},
    ]
    return payload(status='READY', source='health', data=rows)


def action_mock():
    return payload(status='DRY_RUN_ONLY', dry_run=True, action_result='UI_ONLY_NO_REAL_TRADING')
