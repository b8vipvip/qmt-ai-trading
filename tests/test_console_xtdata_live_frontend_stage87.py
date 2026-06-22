from pathlib import Path

def test_frontend_contains_xtdata_live_sections_and_no_trade_words():
    text = Path('local_console_app_stage87/index.html').read_text(encoding='utf-8')
    for term in ['xtdata 只读行情','xtdata 连接状态','MiniQMT 状态','当前 provider','行情 snapshot 表格','K线 bars 表格','sandbox fallback 状态','禁止交易项检查']:
        assert term in text
    for flag in ['read_only=true','no_xttrader=true','no_order_submitted=true','no_account_query=true','allow_order_submit=false','allow_xttrader=false']:
        assert flag in text
    for bad in ['一键下单','自动买入','自动卖出','查询账户','查询持仓','查询资金','撤单','实盘交易']:
        assert bad not in text
