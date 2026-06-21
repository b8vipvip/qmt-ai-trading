from pathlib import Path
from qmt_ai_trading.console_api.task_registry import get_task
from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore


def test_backtest_task_registered_and_returns_contract(tmp_path):
    task=get_task('backtest_dashboard_dry_run')
    assert task and task.category=='BACKTEST'
    run=run_task('backtest_dashboard_dry_run', {'repo_root':'.','output_dir':'out'}, TaskStore())
    assert run.status=='SUCCESS'
    for k in ['task_id','status','output_dir','report_path','dry_run','not_live_trading','research_only','warnings']:
        assert k in run.output


def test_frontend_backtest_page_contains_sections_and_safety():
    text=Path('local_console_app_stage82/app.js').read_text(encoding='utf-8')
    for s in ['回测分析','回测总览卡片','数据源状态卡片','Shadow Replay 结果表','TradeIntent 回测映射表','RiskDecision 回测映射表','Agent 观点 vs 回测表现对比区','组合归因区','风险提示区','报告中心跳转','dry_run=true','not_live_trading=true','research_only=true','no_order_submitted=true','no_qmt_trader_api=true','requires_risk_gate=true','requires_human_approval=true']:
        assert s in text
    forbidden=['一键实盘','一键下单','自动买入','自动卖出','批准交易','绕过风控','live execute','execute order']
    low=text.lower()
    assert not any(x.lower() in low for x in forbidden)


def test_api_server_has_backtest_routes():
    text=Path('qmt_ai_trading/console_api/api_server.py').read_text(encoding='utf-8')
    for route in ['/api/v1/backtest/context','/api/v1/backtest/shadow-replay/latest','/api/v1/backtest/performance/latest','/api/v1/backtest/attribution/latest','/api/v1/backtest/agent-comparison/latest','/api/v1/backtest/report/latest']:
        assert route in text
