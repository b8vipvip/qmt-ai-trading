from pathlib import Path
from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore

ROOT = Path(__file__).resolve().parents[1]

def test_frontend_strategy_page_and_safe_fetches():
    html = (ROOT/'local_console_app_stage77/index.html').read_text(encoding='utf-8')
    js = (ROOT/'local_console_app_stage77/app.js').read_text(encoding='utf-8')
    for text in ['总览','行情数据','AI 模型配置','因子研究','选股中心','策略任务','Agent 投研','回测分析','风控中心','报告中心','任务中心','系统设置']:
        assert text in html + js
    for text in ['来自因子研究的候选池','生成 dry-run TradeIntent','TradeIntent 列表','Risk Gate dry-run','阻断原因','mock_data','not_live_trading','跳转到风控中心']:
        assert text in js
    for bad in ['/api/v1/strategy/execute','/api/v1/order','/api/v1/trade','/api/v1/approve','/api/v1/live']:
        assert bad not in js

def test_strategy_api_task_can_return_result_or_empty_state():
    run = run_task('factor_strategy_dry_run', {}, TaskStore())
    assert 'trade_intents' in run.output and 'risk_decisions' in run.output
