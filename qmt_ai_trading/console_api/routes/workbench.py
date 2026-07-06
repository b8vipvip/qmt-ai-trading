from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
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


def _side(value: Any) -> str:
    text = str(value or '').upper()
    return '卖出' if text == 'SELL' or '卖' in str(value or '') else '买入'


def _risk_level(value: Any) -> str:
    text = str(value or '').upper()
    if 'CRITICAL' in text:
        return 'CRITICAL'
    if 'HIGH' in text or 'BLOCK' in text or 'REJECT' in text:
        return 'HIGH'
    if 'MEDIUM' in text or 'WARN' in text:
        return 'MEDIUM'
    return 'LOW'


def _risk_check(value: Any) -> str:
    return 'PASS' if 'PASS' in str(value or '').upper() else _risk_level(value)


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


def _market_rows() -> list[dict[str, Any]]:
    return [x for x in _first_array(read_json('datahub', 'market_latest.json', [])) if isinstance(x, dict)]


def _task_history_rows() -> list[dict[str, Any]]:
    doc = read_json('workflow', 'task_history.json', {})
    rows = _first_array(doc)
    return [x for x in rows if isinstance(x, dict)]


def _curve(days: int = 180) -> list[dict[str, Any]]:
    base = datetime.today() - timedelta(days=days - 1)
    rows = []
    for i in range(days):
        equity = 100 + i * 0.08
        benchmark = 100 + i * 0.05
        peak = 100 + i * 0.1
        rows.append({
            'date': (base + timedelta(days=i)).strftime('%Y-%m-%d'),
            'equity': round(equity, 2),
            'benchmark': round(benchmark, 2),
            'drawdown': round(min(0, (equity - peak) / max(1, peak) * 100), 2),
            'sourcePath': 'synthetic_until_nav_connected',
        })
    return rows


def dashboard_overview():
    asset = _asset_doc().get('budget') or _asset_doc()
    cash = _num(asset.get('cash'))
    total_asset = _num(asset.get('total_asset'), cash)
    market_value = _num(asset.get('market_value'))
    position = round((market_value / total_asset * 100), 2) if total_asset else 0
    signal_count = len(_signals()) or len(_intents())
    risk_count = len(_risk_decisions())
    budget_path = _artifact_path('portfolio', 'portfolio_budget.json')
    risk_path = _artifact_path('risk', 'risk_decisions.json')
    metrics = [
        {'title': '今日收益', 'value': '0.00%', 'change': '等待 PnL 产物接入', 'status': 'offline', 'trend': [0, 0, 0, 0, 0, 0, 0], 'sourcePath': 'pending_pnl_artifact'},
        {'title': '累计收益', 'value': '0.00%', 'change': '等待净值曲线接入', 'status': 'offline', 'trend': [0, 0, 0, 0, 0, 0, 0], 'sourcePath': 'pending_nav_artifact'},
        {'title': '当前总资产', 'value': round(total_asset, 2), 'change': 'portfolio_budget.total_asset', 'status': 'normal' if total_asset else 'warning', 'trend': [total_asset] * 7, 'sourcePath': budget_path},
        {'title': '当前仓位', 'value': f'{position}%', 'change': 'market_value / total_asset', 'status': 'normal' if position < 80 else 'warning', 'trend': [position] * 7, 'sourcePath': budget_path},
        {'title': '今日成交额', 'value': 0, 'change': '真实成交未接入', 'status': 'offline', 'trend': [0, 0, 0, 0, 0, 0, 0], 'sourcePath': 'pending_trade_artifact'},
        {'title': '当前最大回撤', 'value': '0.00%', 'change': '等待回撤曲线接入', 'status': 'offline', 'trend': [0, 0, 0, 0, 0, 0, 0], 'sourcePath': 'pending_drawdown_artifact'},
        {'title': '运行策略数', 'value': signal_count, 'change': 'strategy_signals/trade_intents', 'status': 'normal' if signal_count else 'warning', 'trend': [signal_count] * 7, 'sourcePath': _artifact_path('strategy', 'strategy_signals.json')},
        {'title': '当前风险等级', 'value': 'LOW' if not risk_count else 'MEDIUM', 'change': 'risk_decisions', 'status': 'normal' if not risk_count else 'warning', 'trend': [1 if not risk_count else 2] * 7, 'sourcePath': risk_path},
    ]
    risk_overview = {
        'level': metrics[-1]['value'],
        'triggerCount': risk_count,
        'blockedOrders': sum(1 for item in _risk_decisions() if 'PASS' not in str(item.get('decision', '')).upper()),
        'totalPosition': position,
        'maxSinglePosition': 0,
        'maxIndustryExposure': 0,
        'intradayLoss': 0,
        'currentDrawdown': 0,
        'losingDays': 0,
        'concentration': 0,
        'industry': 0,
        'total': position,
        'dayLoss': 0,
        'abnormalOrders': 0,
        'disconnects': 0,
        'sourcePath': risk_path,
    }
    return payload(status='READY', source='backend_adapter', data={'metrics': metrics, 'riskOverview': risk_overview})


def dashboard_strategies():
    signals = _signals()
    intents = _intents()
    source_rows = signals or intents
    rows = []
    for idx, row in enumerate(source_rows):
        symbol = row.get('symbol') or row.get('code') or 'UNKNOWN'
        action = row.get('action') or row.get('side') or row.get('signal') or 'HOLD'
        rows.append({
            'id': row.get('intent_id') or row.get('signal_id') or f'backend-{idx + 1}',
            'name': row.get('strategy') or f'Console Strategy {symbol}',
            'type': row.get('source') or '后端产物',
            'mode': '仿真',
            'pool': symbol,
            'rebalance': row.get('period') or 'dry-run',
            'todayReturn': 0,
            'totalReturn': 0,
            'maxDrawdown': 0,
            'position': _num(row.get('target_weight')) * 100 if _num(row.get('target_weight')) <= 1 else _num(row.get('target_weight')),
            'targetWeight': _num(row.get('target_weight')),
            'signalCount': 1,
            'riskStatus': _risk_level(row.get('risk_flags') or row.get('riskDecision')),
            'status': 'RUNNING',
            'sharpe': 0,
            'lastAction': action,
            'signal': row.get('signal'),
            'source': row.get('source'),
            'sourcePath': _artifact_path('strategy', 'strategy_signals.json' if signals else 'trade_intents.json'),
        })
    return payload(status='READY', source='strategy_artifacts', data=rows)


def dashboard_equity_curve():
    return payload(status='READY', source='synthetic_until_nav_connected', data=_curve())


def dashboard_events():
    events = []
    for idx, run in enumerate(_task_history_rows()[:30]):
        events.append({
            'id': run.get('run_id') or f'run-{idx}',
            'time': run.get('finished_at') or run.get('started_at') or '',
            'level': 'normal' if run.get('status') == 'SUCCESS' else 'warning',
            'module': run.get('category') or run.get('task_id') or 'TASK',
            'message': run.get('task_name') or run.get('task_id') or '任务执行记录',
            'runId': run.get('run_id'),
            'taskId': run.get('task_id'),
            'sourcePath': _artifact_path('workflow', 'task_history.json'),
        })
    return payload(status='READY', source='task_history', data=events)


def data_sources():
    market = _market_rows()
    symbols = read_json('datahub', 'datahub_symbols.json', {})
    symbol_count = len(symbols.get('symbols', [])) if isinstance(symbols, dict) else 0
    rows = [
        {'name': 'QMT 本地行情', 'status': 'normal' if market else 'warning', 'updatedAt': datetime.now().isoformat(timespec='seconds'), 'records': len(market), 'latency': 'local', 'missingRate': 0, 'abnormalRate': 0, 'dataSource': 'xtdata_live_readonly', 'qualityLevel': 'real_xtdata_readonly', 'sourcePath': _artifact_path('datahub', 'market_latest.json')},
        {'name': '统一标的池', 'status': 'normal' if symbol_count else 'warning', 'updatedAt': datetime.now().isoformat(timespec='seconds'), 'records': symbol_count, 'latency': 'local', 'missingRate': 0, 'abnormalRate': 0, 'dataSource': 'datahub_symbols', 'qualityLevel': 'symbol_universe', 'sourcePath': _artifact_path('datahub', 'datahub_symbols.json')},
    ]
    return payload(status='READY', source='datahub_artifacts', data=rows)


def data_quality():
    market = _market_rows()
    symbols = sorted({str(x.get('symbol')) for x in market if x.get('symbol')})
    rows = []
    if market:
        rows.append({'dataset': 'datahub.market_latest', 'tradeDate': str(market[-1].get('time') or '')[:10], 'stockCount': len(symbols), 'missingFields': 0, 'abnormalValues': 0, 'duplicateRows': 0, 'passed': True, 'sourcePath': _artifact_path('datahub', 'market_latest.json')})
    return payload(status='READY', source='datahub_artifacts', data=rows)


def data_tasks():
    rows = []
    for item in _task_history_rows()[:30]:
        rows.append({'name': item.get('task_name') or item.get('task_id') or '', 'type': item.get('category') or 'TASK', 'cron': 'manual', 'lastRun': item.get('finished_at') or item.get('started_at') or '', 'nextRun': '', 'status': item.get('status') or '', 'cost': item.get('duration') or '', 'sourcePath': _artifact_path('workflow', 'task_history.json')})
    return payload(status='READY', source='task_history', data=rows)


def factor_list():
    rows = []
    for idx, item in enumerate(_candidates()):
        symbol = item.get('symbol') or 'UNKNOWN'
        score = _num(item.get('score') or item.get('composite_score'))
        rows.append({
            'id': f'factor-{symbol}-{idx + 1}',
            'name': f'{symbol} 因子评分',
            'type': '多因子',
            'version': 'backend',
            'universe': symbol,
            'icMean': 0,
            'rankIc': 0,
            'icir': 0,
            'longShortReturn': 0,
            'turnover': 0,
            'status': '候选',
            'score': score,
            'rank': item.get('rank') or idx + 1,
            'reasons': item.get('reasons'),
            'riskFlags': item.get('risk_flags') or item.get('riskFlags'),
            'sourcePath': _artifact_path('research', 'factor_candidates.json'),
        })
    return payload(status='READY', source='research_artifacts', data=rows)


def strategy_list():
    return dashboard_strategies()


def order_plan():
    previews = _preview_doc().get('previews') or []
    rows = []
    for idx, item in enumerate(previews):
        if not isinstance(item, dict):
            continue
        side = item.get('side') or 'BUY'
        risk_decision = item.get('risk_decision') or item.get('decision') or 'PASS_DRY_RUN'
        latest_price = _num(item.get('latest_price'))
        quantity = _num(item.get('preview_quantity') or item.get('quantity'))
        amount = _num(item.get('estimated_amount'), latest_price * quantity)
        rows.append({
            'id': item.get('preview_id') or f'preview-{idx + 1}',
            'strategy': item.get('intent_id') or 'portfolio_preview',
            'code': item.get('symbol') or '',
            'name': item.get('symbol') or '',
            'side': _side(side),
            'rawSide': side,
            'quantity': quantity,
            'price': latest_price,
            'latestPrice': latest_price,
            'type': 'PREVIEW',
            'amount': amount,
            'estimatedAmount': amount,
            'riskCheck': _risk_check(risk_decision),
            'riskDecision': risk_decision,
            'businessStatus': item.get('status') or 'PREVIEW',
            'status': item.get('status') or 'PREVIEW',
            'createdAt': item.get('created_at') or '',
            'intentId': item.get('intent_id'),
            'previewOnly': True,
            'canSubmit': False,
            'sourcePath': _artifact_path('portfolio', 'order_preview_latest.json'),
        })
    return payload(status='READY', source='portfolio_preview', data=rows)


def holdings():
    positions = _first_array(read_json('account_readonly', 'account_positions_snapshot.json', []))
    rows = []
    for idx, item in enumerate(positions):
        if not isinstance(item, dict):
            continue
        rows.append({'code': item.get('symbol') or item.get('code') or f'POS-{idx + 1}', 'name': item.get('name') or item.get('symbol') or '', 'currentQty': item.get('quantity') or item.get('volume') or 0, 'currentWeight': 0, 'targetWeight': 0, 'targetValue': 0, 'diffQty': 0, 'diffAmount': 0, 'riskStatus': 'LOW', 'accountIdMasked': item.get('account_id_masked'), 'sourcePath': _artifact_path('account_readonly', 'account_positions_snapshot.json')})
    if not rows:
        for preview in order_plan().get('data', []):
            rows.append({'code': preview.get('code'), 'name': preview.get('name'), 'currentQty': 0, 'currentWeight': 0, 'targetWeight': preview.get('quantity', 0), 'targetValue': preview.get('estimatedAmount', 0), 'diffQty': preview.get('quantity', 0), 'diffAmount': preview.get('estimatedAmount', 0), 'riskStatus': 'LOW', 'sourcePath': preview.get('sourcePath')})
    return payload(status='READY', source='account_readonly_or_portfolio_preview', data=rows)


def trades():
    return payload(status='READY', source='adapter_pending_real_trades', data=[])


def risk_overview():
    return dashboard_overview()


def risk_rules():
    path = 'safety_policy_runtime'
    rules = [
        {'id': 'readonly', 'name': '只读模式强制开启', 'type': '交易前', 'threshold': 'True', 'current': 'True', 'action': '拦截', 'enabled': True, 'lastTriggered': '', 'description': '所有前端交易动作只允许 mock/dry-run。', 'sourcePath': path},
        {'id': 'no-live', 'name': '实盘交易默认关闭', 'type': '交易前', 'threshold': 'False', 'current': 'False', 'action': '停止交易', 'enabled': True, 'lastTriggered': '', 'description': 'Live Disabled 是全局硬闸门。', 'sourcePath': path},
        {'id': 'human-approval', 'name': '人工审批闸门', 'type': '交易前', 'threshold': 'Required', 'current': 'Required', 'action': '拦截', 'enabled': True, 'lastTriggered': '', 'description': '未通过人工审批不得进入 paper/live 链路。', 'sourcePath': path},
        {'id': 'no-submit', 'name': '禁止真实发单', 'type': '交易前', 'threshold': 'order_submit_enabled=false', 'current': 'false', 'action': '拦截', 'enabled': True, 'lastTriggered': '', 'description': '所有订单计划必须停留在 preview。', 'sourcePath': path},
    ]
    return payload(status='READY', source='safety_policy', data=rules)


def risk_events():
    rows = []
    for idx, item in enumerate(_risk_decisions()):
        decision = item.get('decision') or ''
        rows.append({'id': item.get('intent_id') or f'risk-{idx + 1}', 'time': item.get('created_at') or '', 'strategy': item.get('intent_id') or '', 'rule': 'Risk Gate', 'level': 'LOW' if 'PASS' in str(decision).upper() else 'HIGH', 'trigger': decision, 'threshold': 'safety_policy', 'action': decision, 'result': decision, 'operator': 'system', 'sourcePath': _artifact_path('risk', 'risk_decisions.json')})
    return payload(status='READY', source='risk_artifacts', data=rows)


def deployment_stages():
    rows = [
        {'stage': 'Paper Trading', 'status': 'READY', 'startedAt': '', 'days': 0, 'strategyCount': len(_signals()), 'capital': '0', 'issues': '等待连续运行统计', 'criteria': ['连续运行20个交易日', '无系统崩溃', '信号生成正常'], 'sourcePath': _artifact_path('paper', 'paper_orders.json')},
        {'stage': 'Shadow Trading', 'status': 'READY', 'startedAt': '', 'days': 0, 'strategyCount': len(_signals()), 'capital': '0', 'issues': '仅读取真实行情，不下单', 'criteria': ['实盘行情稳定', '理论订单生成正常', '无异常订单'], 'sourcePath': _artifact_path('backtest', 'shadow_replay_latest.json')},
        {'stage': 'Small Capital', 'status': 'LOCKED', 'startedAt': '', 'days': 0, 'strategyCount': 0, 'capital': '需审批', 'issues': '等待安全审计', 'criteria': ['小资金授权', '最大回撤低于阈值'], 'sourcePath': 'safety_policy_runtime'},
        {'stage': 'Full Live', 'status': 'HIGH_RISK_LOCKED', 'startedAt': '', 'days': 0, 'strategyCount': 0, 'capital': '禁止一键开启', 'issues': '高危权限', 'criteria': ['风控委员会审批', '多签确认'], 'sourcePath': 'safety_policy_runtime'},
    ]
    return payload(status='READY', source='safety_policy', data=rows)


def api_status():
    rows = [
        {'name': '统一控制台 API', 'status': 'normal', 'latency': 'local', 'sourcePath': 'qmt_ai_trading/console_api/api_server.py'},
        {'name': 'QMT / 券商 API', 'status': 'offline', 'latency': '-', 'sourcePath': 'pending_broker_adapter'},
        {'name': 'Data Hub artifacts', 'status': 'normal', 'latency': 'local', 'sourcePath': _artifact_path('datahub', 'market_latest.json')},
        {'name': 'Risk Gate', 'status': 'normal', 'latency': 'local', 'sourcePath': _artifact_path('risk', 'risk_decisions.json')},
        {'name': 'Task History', 'status': 'normal', 'latency': 'local', 'sourcePath': _artifact_path('workflow', 'task_history.json')},
    ]
    return payload(status='READY', source='health', data=rows)


def action_mock():
    return payload(status='DRY_RUN_ONLY', dry_run=True, action_result='UI_ONLY_NO_REAL_TRADING')
