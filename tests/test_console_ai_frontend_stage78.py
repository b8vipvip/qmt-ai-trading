from pathlib import Path
ROOT=Path('local_console_app_stage77')
def read(n): return (ROOT/n).read_text(encoding='utf-8')
def test_frontend_ai_menu_and_inputs():
    html=read('index.html'); js=read('app.js')
    for x in ['AI 模型配置','Base URL','API Key','查询可用模型','模型多选列表']:
        assert x in html+js
    assert 'type="password"' in js and '1000 字' in js and '3000 字' in js and '5000 字' in js
def test_app_calls_ai_api_and_no_key_localstorage_or_danger():
    js=read('app.js')
    assert '/api/v1' in js and '/ai/models/discover' in js and '/ai/models/stress-test' in js
    assert 'localStorage' not in js
    for bad in ['xttrader','XtQuantTrader','order_stock','place_order','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','自动 approve']:
        assert bad not in js
def test_stage78_chinese_no_mojibake_and_no_live_fetch():
    text=read('app.js')+read('index.html')
    assert '模型用途映射区' in text and '锟' not in text and '�' not in text
    for bad in ["fetch('/trade')",'fetch("/trade")',"fetch('/account')",'fetch("/account")',"fetch('/approve')",'fetch("/approve")']:
        assert bad not in text
