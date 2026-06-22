from pathlib import Path
import inspect
import qmt_ai_trading.console_api.api_server as api_server
from qmt_ai_trading.console_api.task_registry import get_task

def test_xtdata_enable_frontend_contains_required_sections_and_no_forbidden_ui_terms():
    text=Path('local_console_app_stage86/index.html').read_text(encoding='utf-8')+'\n'+Path('local_console_app_stage86/app.js').read_text(encoding='utf-8')
    for token in ['xtdata 启用确认','xtdata 启用请求状态','环境检测结果','人工确认 checklist','配置审计表','安全阻断原因','sandbox fallback 状态','下一阶段计划','安全边界说明','enable_xtdata=false','real_market_data=false','mini_qmt_connected=false','xtdata_imported=false','read_only=true','dry_run=true','requires_human_confirmation=true','manual_confirmation_completed=false','allow_xttrader=false']:
        assert token in text
    for forbidden in ['一键启用真实行情','已连接真实行情','已连接 MiniQMT','实盘交易','一键下单','自动买入','自动卖出','查询账户','调用 xttrader']:
        assert forbidden not in text

def test_xtdata_enable_api_routes_and_task_registered():
    src=inspect.getsource(api_server)
    for route in ['/api/v1/market/xtdata-enable/context','/api/v1/market/xtdata-enable/request','/api/v1/market/xtdata-enable/environment','/api/v1/market/xtdata-enable/checklist','/api/v1/market/xtdata-enable/audit','/api/v1/market/xtdata-enable/decision','/api/v1/market/xtdata-enable/report']:
        assert route in src
    assert get_task('xtdata_enable_dry_run') is not None
