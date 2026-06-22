from pathlib import Path
from qmt_ai_trading.trading_gateway import run_xttrader_boundary_stage90

def test_frontend_has_boundary_copy(tmp_path):
    run_xttrader_boundary_stage90('.', 89, 'local_console_xttrader_stage90', True, True)
    html = Path('local_console_app_stage90/index.html').read_text(encoding='utf-8')
    assert 'xttrader 边界' in html
    assert '交易接口边界' in html
    assert '查看订单预览' in html
    for bad in ['一键下单','立即买入','立即卖出','查询真实账户','查询真实持仓']:
        assert bad not in html
