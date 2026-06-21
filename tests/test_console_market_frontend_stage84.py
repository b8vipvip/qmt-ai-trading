from pathlib import Path
import inspect
import qmt_ai_trading.console_api.api_server as api_server
from qmt_ai_trading.console_api.task_registry import get_task

def test_market_frontend_contains_required_sections_and_no_forbidden_ui_terms():
    text=Path('local_console_app_stage84/index.html').read_text(encoding='utf-8')+'\n'+Path('local_console_app_stage84/app.js').read_text(encoding='utf-8')
    for token in ['行情回放','Sandbox 行情网关状态','Provider 类型显示','标的列表','行情快照表','K线数据表','Replay Bus 状态','Replay Event 时间线','数据质量报告','安全边界说明','GET /api/v1/market/sandbox/replay/latest','sandbox=true','read_only=true','not_live_trading=true','no_qmt_trader_api=true','no_order_submitted=true']:
        assert token in text
    for forbidden in ['真实行情已接入','实盘交易','一键下单','自动买入','自动卖出','查询账户','查询持仓','调用 xttrader']:
        assert forbidden not in text

def test_market_api_routes_and_task_registered():
    src=inspect.getsource(api_server)
    for route in ['/api/v1/market/sandbox/context','/api/v1/market/sandbox/symbols','/api/v1/market/sandbox/snapshots','/api/v1/market/sandbox/bars','/api/v1/market/sandbox/replay/latest','/api/v1/market/sandbox/quality/latest','/api/v1/market/sandbox/report/latest']:
        assert route in src
    assert get_task('market_replay_sandbox') is not None

def test_validate_stage84_is_read_only():
    text=Path('scripts/validate_stage84.ps1').read_text(encoding='utf-8')
    assert 'install_run_qmt_tasks_logging.ps1' not in text
    assert 'sync_all.ps1' not in text
    assert 'Tee-Object -FilePath' not in text and 'Out-File' not in text
    assert 'Set-Content' not in text and 'Add-Content' not in text
