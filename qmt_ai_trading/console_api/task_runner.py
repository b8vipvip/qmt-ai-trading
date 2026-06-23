from __future__ import annotations
import json
import uuid
from pathlib import Path
from .models import TaskRun, now_iso
from .task_registry import get_task
from .safety import *
from .artifact_writer import write_task_output_to_console_artifacts


def _bool_value(params, name, default=False):
    value = params.get(name, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _read_console_artifact(module: str, filename: str, default):
    path = Path("artifacts/reports/console") / module / filename
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def _latest_trade_intents():
    data = _read_console_artifact("strategy", "trade_intents.json", {})
    if isinstance(data, dict):
        intents = data.get("trade_intents") or data.get("intents") or []
        return intents if isinstance(intents, list) else []
    return []


def _run_risk_gate_from_latest_intents(params):
    from qmt_ai_trading.risk.factor_strategy_risk_review import review_trade_intents

    intents = _latest_trade_intents()
    decisions = review_trade_intents(intents)
    return {
        "task_id": "risk_gate_dry_run",
        "status": "SUCCESS",
        "source": "artifacts/reports/console/strategy/trade_intents.json",
        "trade_intent_count": len(intents),
        "decision_count": len(decisions),
        "decisions": decisions,
        "blocked_by_risk": any(d.get("decision") != "PASS_DRY_RUN" for d in decisions) or not intents,
        "dry_run": True,
        "read_only": True,
        "live_disabled": True,
        "no_order_submitted": True,
        "no_account_query": True,
        "no_qmt_trader_api": True,
        "auto_approve": False,
    }


def _run_paper_from_latest_risk(params):
    from qmt_ai_trading.paper_trading import run_paper_trading_stage89

    report = run_paper_trading_stage89(
        params.get("repo_root", "."),
        params.get("input_stage", 88),
        params.get("output_dir", "local_console_paper_stage89"),
        True,
        True,
    )
    report.update({
        "task_id": "paper_trading_dry_run",
        "status": "SUCCESS",
        "paper_trading": True,
        "shadow_trading": True,
        "real_order_submitted": False,
        "no_xttrader": True,
        "no_account_query": True,
        "no_order_submitted": True,
        "dry_run": True,
        "read_only": True,
        "not_live_trading": True,
    })
    return report


def _run_unified_factor_strategy(params, task_id='strategy_dry_run_signals'):
    from qmt_ai_trading.research.factor_engine import run_factor_scan
    from qmt_ai_trading.strategies.factor_strategy_engine import build_factor_strategy
    from qmt_ai_trading.risk.factor_strategy_risk_review import review_trade_intents
    from qmt_ai_trading.strategies.strategy_report import build_strategy_report

    scan = run_factor_scan(params)
    built = build_factor_strategy(scan.get('factor_candidates', []), int(params.get('max_positions', 3)))
    decisions = review_trade_intents(built['trade_intents'])
    report = build_strategy_report(built['strategy_signals'], built['trade_intents'], decisions)
    return {
        'task_id': task_id,
        'data_source': scan.get('data_source'),
        'quality_level': scan.get('quality_level'),
        'real_market_data': scan.get('real_market_data', False),
        'sandbox_fallback': scan.get('sandbox_fallback', True),
        'bar_source': scan.get('bar_source'),
        'factor_candidates': scan.get('factor_candidates', []),
        'strategy_signals': built['strategy_signals'],
        'trade_intents': built['trade_intents'],
        'risk_decisions': decisions,
        'strategy_report': report,
        'dry_run': True,
        'read_only': True,
        'no_qmt_trader_api': True,
        'no_account_query': True,
        'no_order_submitted': True,
        'auto_approve': False,
    }


def mock_output(task_id, params):
    if task_id in {'factor_scan', 'factor_research_dry_run', 'etf_rotation_candidates', 'research_score_etf'}:
        from qmt_ai_trading.research.factor_engine import run_factor_scan
        result = run_factor_scan(params)
        result['task_id'] = task_id
        return result
    if task_id in {'strategy_dry_run_signals', 'daily_pipeline_dry_run'}:
        return _run_unified_factor_strategy(params, task_id)
    if task_id == 'agent_research_dry_run':
        from qmt_ai_trading.agents_research import run_agent_research
        return run_agent_research(repo_root=params.get('repo_root', '.'), output_dir=params.get('output_dir', 'local_console_agent_stage81'), mock_agent=params.get('mock_agent', True), real_ai_call=params.get('real_ai_call', False), max_agents=int(params.get('max_agents', 7)), input_source=params.get('input_source', 'stage80'), dry_run=params.get('dry_run', True))
    if task_id == 'backtest_dashboard_dry_run':
        from qmt_ai_trading.backtest_dashboard import run_backtest_dashboard
        report = run_backtest_dashboard(repo_root=params.get('repo_root', '.'), output_dir=params.get('output_dir', 'local_console_backtest_stage82'), backtest_mode=params.get('backtest_mode', 'mock_shadow'))
        return {'task_id': 'backtest_dashboard_dry_run', 'status': 'SUCCESS', 'output_dir': report.get('output_dir', 'local_console_backtest_stage82'), 'report_path': report.get('report_path'), 'dry_run': True, 'not_live_trading': True, 'research_only': True, 'warnings': report.get('warnings', []), 'no_order_submitted': True, 'no_qmt_trader_api': True}
    if task_id == 'monitoring_alert_dry_run':
        from qmt_ai_trading.monitoring import run_monitoring_stage83
        report = run_monitoring_stage83(repo_root=params.get('repo_root', '.'), output_dir=params.get('output_dir', 'local_console_monitoring_stage83'))
        return {'task_id': 'monitoring_alert_dry_run', 'status': 'SUCCESS', 'output_dir': report.get('output_dir'), 'report_path': report.get('report_path'), 'alert_count': report.get('alert_count', 0), 'critical_count': report.get('critical_count', 0), 'circuit_breaker_status': report.get('circuit_breaker_status'), 'dry_run': True, 'not_live_trading': True, 'research_only': True, 'no_real_notification': True, 'warnings': report.get('warnings', [])}
    if task_id == 'market_replay_sandbox':
        from qmt_ai_trading.market_gateway import run_market_gateway_stage84
        report = run_market_gateway_stage84(repo_root=params.get('repo_root', '.'), output_dir=params.get('output_dir', 'local_console_market_stage84'), provider=params.get('provider', 'mock_provider'), symbols=params.get('symbols', ['510300.SH', '510500.SH', '588000.SH']), timeframe=params.get('timeframe', '1d'), limit=int(params.get('limit', 20)), speed=float(params.get('speed', 1.0)))
        return {'task_id': 'market_replay_sandbox', 'status': 'SUCCESS', 'output_dir': report.get('output_dir'), 'report_path': report.get('report_path'), 'provider': report.get('provider'), 'replay_event_count': report.get('replay_event_count', 0), 'symbol_count': report.get('symbol_count', 0), 'sandbox': True, 'read_only': True, 'not_live_trading': True, 'no_qmt_trader_api': True, 'warnings': report.get('warnings', [])}
    if task_id == 'xtdata_boundary_dry_run':
        from qmt_ai_trading.market_gateway import run_xtdata_boundary_stage85
        report = run_xtdata_boundary_stage85(repo_root=params.get('repo_root', '.'), output_dir=params.get('output_dir', 'local_console_xtdata_stage85'), enabled=params.get('enabled', False), dry_run=params.get('dry_run', True), read_only=params.get('read_only', True), allow_import_xtdata=params.get('allow_import_xtdata', False), allow_connect_miniqmt=params.get('allow_connect_miniqmt', False), allow_real_market_data=params.get('allow_real_market_data', False), sandbox_fallback=params.get('sandbox_fallback', True))
        return {'task_id': 'xtdata_boundary_dry_run', 'status': 'SUCCESS', 'output_dir': report.get('output_dir'), 'report_path': report.get('report_path'), 'enabled': report.get('enabled', False), 'dry_run': report.get('dry_run', True), 'read_only': report.get('read_only', True), 'xtdata_imported': False, 'mini_qmt_connected': False, 'real_market_data': False, 'sandbox_fallback': report.get('sandbox_fallback', True), 'safety_status': report.get('safety_status'), 'warnings': report.get('warnings', [])}
    if task_id == 'xtdata_enable_dry_run':
        from qmt_ai_trading.market_gateway import run_xtdata_enable_stage86
        report = run_xtdata_enable_stage86(repo_root=params.get('repo_root', '.'), output_dir=params.get('output_dir', 'local_console_xtdata_enable_stage86'), enable_xtdata=params.get('enable_xtdata', False), connect_miniqmt=params.get('connect_miniqmt', False), enable_real_market_data=params.get('enable_real_market_data', False), dry_run=params.get('dry_run', True), read_only=params.get('read_only', True), requires_human_confirmation=params.get('requires_human_confirmation', True))
        return {'task_id': 'xtdata_enable_dry_run', 'status': 'SUCCESS', 'output_dir': report.get('output_dir'), 'report_path': report.get('report_path'), 'decision': report.get('decision'), 'enable_xtdata': False, 'real_market_data': False, 'mini_qmt_connected': False, 'xtdata_imported': False, 'dry_run': True, 'read_only': True, 'requires_human_review': True, 'warnings': report.get('warnings', [])}
    if task_id == 'xtdata_live_readonly_smoke':
        from qmt_ai_trading.market_gateway import run_xtdata_live_stage87
        warnings = []
        for forbidden in ('allow_xttrader', 'allow_order_submit', 'allow_account_query'):
            if params.get(forbidden) is True:
                warnings.append(f'{forbidden}=true is not accepted; forced to false for read-only xtdata mode')
        report = run_xtdata_live_stage87(repo_root=params.get('repo_root', '.'), output_dir=params.get('output_dir', 'local_console_xtdata_live_stage87'), enabled=params.get('enable_xtdata', False), allow_import_xtdata=params.get('allow_import_xtdata', False), allow_real_market_data=params.get('allow_real_market_data', False), allow_connect_miniqmt=params.get('allow_connect_miniqmt', False), read_only=True, allow_xttrader=False, allow_account_query=False, allow_order_submit=False, symbols=params.get('symbols', ['510300.SH', '510500.SH', '588000.SH']), period=params.get('period', '1d'), limit=int(params.get('limit', 20)))
        report.update({'read_only': True, 'allow_xttrader': False, 'allow_order_submit': False, 'allow_account_query': False, 'no_xttrader': True, 'no_order_submitted': True, 'no_account_query': True})
        if warnings:
            report['warnings'] = list(report.get('warnings', [])) + warnings
        return report
    if task_id == 'stage88_real_data_dry_run':
        from qmt_ai_trading.datahub.datahub_report import run_stage88_datahub
        from qmt_ai_trading.research.stage88_real_cache_factors import write_research
        from qmt_ai_trading.strategies.stage88_dry_run import write_strategy
        from qmt_ai_trading.risk.stage88_risk_gate import write_risk
        symbols = params.get('symbols', ['510300.SH', '510500.SH', '588000.SH', '159915.SZ', '512100.SH'])
        if isinstance(symbols, str):
            symbols = [x.strip() for x in symbols.split(',') if x.strip()]
        dh = run_stage88_datahub(params.get('repo_root', '.'), 'local_console_datahub_stage88', symbols, params.get('period', '1d'), int(params.get('limit', 120)), enable_xtdata=params.get('enable_xtdata', False), allow_import_xtdata=params.get('allow_import_xtdata', False), allow_real_market_data=params.get('allow_real_market_data', False), allow_connect_miniqmt=params.get('allow_connect_miniqmt', False))
        rs = write_research(params.get('repo_root', '.'))
        st = write_strategy(params.get('repo_root', '.'))
        rk = write_risk(params.get('repo_root', '.'))
        return {'task_id': 'stage88_real_data_dry_run', 'status': 'SUCCESS', 'datahub': dh, 'research': rs, 'strategy': st, 'risk': rk, 'dry_run': True, 'read_only': True, 'not_live_trading': True, 'no_xttrader': True, 'no_order_submitted': True, 'no_account_query': True, 'requires_human_approval': True}
    if task_id == 'paper_trading_dry_run':
        return _run_paper_from_latest_risk(params)

    if task_id == 'xttrader_boundary_dry_run':
        from qmt_ai_trading.trading_gateway import run_xttrader_boundary_stage90
        return run_xttrader_boundary_stage90(params.get('repo_root', '.'), params.get('input_stage', 89), params.get('output_dir', 'local_console_xttrader_stage90'), True, True)
    if task_id == 'account_readonly_dry_run':
        from qmt_ai_trading.trading_gateway.account_readonly_report import run_account_readonly_stage91
        warnings = []
        if _bool_value(params, 'allow_order_submit', False):
            warnings.append('allow_order_submit=true is not accepted; forced to false for account read-only mode')
        if _bool_value(params, 'allow_order_cancel', False):
            warnings.append('allow_order_cancel=true is not accepted; forced to false for account read-only mode')
        if warnings:
            report = {'ok': False, 'status': 'BLOCKED_BY_SAFETY', 'error_message': 'Account readonly task is read-only; order submit/cancel permissions are forbidden'}
        elif all(_bool_value(params, name, False) for name in ['enable_account_readonly', 'allow_import_xttrader', 'allow_connect_trade_session', 'allow_account_query', 'allow_position_query', 'manual_confirmed']) and _bool_value(params, 'dry_run', True) and _bool_value(params, 'read_only', True):
            from qmt_ai_trading.console_api.account_readonly_runtime import run_account_readonly_subprocess
            report = run_account_readonly_subprocess(params.get('repo_root', '.'), params)
        else:
            report = run_account_readonly_stage91(params.get('repo_root', '.'), params.get('output_dir', 'local_console_account_stage91'), _bool_value(params, 'enable_account_readonly', False), _bool_value(params, 'allow_import_xttrader', False), _bool_value(params, 'allow_connect_trade_session', False), _bool_value(params, 'allow_account_query', False), _bool_value(params, 'allow_position_query', False), _bool_value(params, 'manual_confirmed', False), _bool_value(params, 'dry_run', True), _bool_value(params, 'read_only', True))
        report.update({'allow_order_submit': False, 'allow_order_cancel': False, 'order_submit_enabled': False, 'order_cancel_enabled': False, 'real_order_submitted': False})
        if warnings:
            report['warnings'] = warnings
        return report
    if task_id == 'workflow_dry_run_check':
        from qmt_ai_trading.console_api.workflow_console import write_workflow_outputs
        return write_workflow_outputs(params.get('repo_root', '.'), params.get('output_dir', 'local_console_workflow_stage87'))
    if task_id == 'risk_gate_dry_run':
        return _run_risk_gate_from_latest_intents(params)
    if task_id == 'factor_strategy_dry_run':
        return _run_unified_factor_strategy(params, task_id)
    base = {'mode': 'dry-run/shadow', 'no_trade_authorization': True, 'read_only': True, 'params': params}
    if task_id in {'ai_model_discovery', 'ai_model_stress_test', 'ai_model_usage_draft'}:
        base.update({'ai_provider_task': True, 'local_api_only': True, 'trade_chain': False, 'note': 'AI Provider 白名单任务，仅调用本地 Console API，不进入交易链路'})
    elif task_id == 'market_snapshot_readonly':
        base.update({'symbol': params.get('symbol', '510300.SH'), 'source': 'local readonly/mock', 'ohlcv': {'open': 3.91, 'high': 3.96, 'low': 3.88, 'close': 3.94, 'volume': 1200000}, 'quality': 'OK'})
    elif task_id.startswith('agent_'):
        base.update({'advice': 'HOLD', 'confidence': 0.62, 'reasons': ['结构化建议，仅供人工复核'], 'risk_flags': ['实盘关闭', '不得自动下单']})
    elif 'risk' in task_id or 'blockers' in task_id:
        base.update({'blocked': True, 'blockers': ['实盘未启用', '缺少人工审批', '仅 dry-run']})
    elif 'backtest' in task_id or 'replay' in task_id:
        base.update({'total_return': 0.032, 'max_drawdown': 0.041, 'win_rate': 0.55, 'trade_count': 12})
    else:
        base.update({'candidates': [{'symbol': '510300.SH', 'rank': 1, 'score': 82, 'reasons': ['动量稳定'], 'risk_flags': ['dry-run']}], 'signals': [{'symbol': '159915.SZ', 'signal': 'HOLD', 'trade_intent': 'DRY_RUN_ONLY'}]})
    return base


def run_task(task_id, params, store):
    assert_safe_task_id(task_id); assert_safe_task_params(params)
    task = get_task(task_id)
    if not task:
        raise ConsoleSafetyError('未知任务，不在白名单')
    assert_task_allowed(task); assert_no_forbidden_live_task(task)
    run = TaskRun(str(uuid.uuid4()), task.task_id, task.title_zh, task.category, 'RUNNING', {**task.default_params, **params}, now_iso())
    store.add(run); run.logs.append('任务已通过白名单与安全边界校验'); run.logs.append('以 dry-run / shadow / read-only 模式执行')
    run.output = mock_output(task_id, run.params)
    written = write_task_output_to_console_artifacts(task_id, run.output)
    if written:
        run.output_artifacts = sorted(set(list(task.output_artifacts) + written))
        run.logs.append(f'统一控制台产物已更新：{len(written)} 个文件')
    else:
        run.output_artifacts = task.output_artifacts
        run.logs.append('该任务暂无统一控制台产物映射，仅保留任务输出')
    run.status = 'SUCCESS'; run.finished_at = now_iso(); run.logs.append('任务完成：未下单、未查账户、未自动批准')
    return run
