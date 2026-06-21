from pathlib import Path
import inspect
import qmt_ai_trading.console_api.api_server as api_server
from qmt_ai_trading.console_api.task_registry import get_task

def test_xtdata_frontend_contains_required_sections_and_no_forbidden_ui_terms():
    text=Path('local_console_app_stage85/index.html').read_text(encoding='utf-8')+'\n'+Path('local_console_app_stage85/app.js').read_text(encoding='utf-8')
    for token in ['xtdata 边界检查','xtdata adapter 当前状态','配置开关表','Import Guard 检查结果','MiniQMT 连接状态 dry-run','真实行情权限 dry-run','Sandbox fallback 状态','Safety Gate 结果','下一阶段启用清单','安全边界说明','enabled=false','dry_run=true','read_only=true','xtdata_imported=false','mini_qmt_connected=false','real_market_data=false','sandbox_fallback=true','allow_xttrader=false','no_order_submitted=true','no_qmt_trader_api=true']:
        assert token in text
    for forbidden in ['已连接真实行情','已连接实盘','一键启用真实行情','一键下单','自动买入','自动卖出','查询账户','查询持仓','调用 xttrader']:
        assert forbidden not in text

def test_xtdata_api_routes_and_task_registered():
    src=inspect.getsource(api_server)
    for route in ['/api/v1/market/xtdata/context','/api/v1/market/xtdata/config','/api/v1/market/xtdata/import-guard','/api/v1/market/xtdata/capability-probe','/api/v1/market/xtdata/safety','/api/v1/market/xtdata/report']:
        assert route in src
    assert get_task('xtdata_boundary_dry_run') is not None
