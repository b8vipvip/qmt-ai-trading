from pathlib import Path


def _frontend_text():
    return Path('local_console_app_stage87/index.html').read_text(encoding='utf-8') + Path('local_console_app_stage87/app.js').read_text(encoding='utf-8') + Path('local_console_app_stage87/styles.css').read_text(encoding='utf-8')


def test_frontend_contains_xtdata_live_human_readable_sections_and_no_dangerous_entries():
    text = _frontend_text()
    for term in ['xtdata 只读行情工作台','顶部状态总览','行情控制区','行情摘要卡片','K 线数据表','诊断信息','高级调试：查看原始 JSON','安全边界提示']:
        assert term in text
    for term in ['真实 xtdata 行情','Sandbox 模拟行情','MiniQMT 已连接','只读安全：未接交易接口','安全边界异常，请停止使用并检查配置']:
        assert term in text
    for flag in ['read_only=true','no_xttrader=true','no_order_submitted=true','no_account_query=true','allow_order_submit=false','allow_xttrader=false']:
        assert flag in text
    for bad in ['一键下单','自动买入','自动卖出','账户查询按钮','持仓查询按钮','资金查询按钮','实盘交易']:
        assert bad not in text


def test_frontend_manual_confirmation_controls_and_relative_fetch_params():
    text = Path('local_console_app_stage87/app.js').read_text(encoding='utf-8')
    for token in ['xtLiveConfirm', '人工确认：我确认只启用 xtdata 只读行情', '标的输入框', '周期选择', 'K线数量选择', '启用真实 xtdata 只读行情', '关闭真实行情，回到 Sandbox', '获取快照', '获取K线']:
        assert token in text
    for token in ['510300.SH,510500.SH,588000.SH', '1m', '5m', '15m', '1d', '20', '60', '120', '250']:
        assert token in text
    for param in ['enable_xtdata', 'allow_import_xtdata', 'allow_real_market_data', 'allow_connect_miniqmt', 'read_only', 'allow_xttrader', 'allow_order_submit', 'allow_account_query']:
        assert param in text
    assert "fetch('/api/v1/market/xtdata-live/status" not in text
    assert '127.0.0.1' not in text


def test_console_bars_endpoint_with_mock_dataframe_does_not_return_raw_dataframe(monkeypatch):
    import json
    import sys
    import types
    from io import BytesIO
    from tests.test_xtdata_live_readonly_stage87 import _install_fake_pandas_numpy
    from qmt_ai_trading.console_api.api_server import make_handler
    pd, _np = _install_fake_pandas_numpy(monkeypatch)

    fake_xtdata = types.SimpleNamespace(
        get_market_data_ex=lambda *a, **k: {'510300.SH': pd.DataFrame({'time': [pd.Timestamp('2026-06-22')], 'open': [1], 'high': [2], 'low': [1], 'close': [2], 'volume': [3], 'amount': [4]})},
    )
    monkeypatch.setitem(sys.modules, 'xtquant', types.SimpleNamespace(xtdata=fake_xtdata))

    Handler = make_handler()
    req = Handler.__new__(Handler)
    req.command = 'GET'
    req.path = '/api/v1/market/xtdata-live/bars?symbol=510300.SH&period=1d&limit=20&enable_xtdata=true&allow_import_xtdata=true&allow_real_market_data=true&allow_connect_miniqmt=true&allow_xttrader=true&allow_order_submit=true&allow_account_query=true'
    req.request_version = 'HTTP/1.1'
    req.headers = {}
    req.rfile = BytesIO()
    req.wfile = BytesIO()
    req.send_response = lambda code, message=None: setattr(req, 'code', code)
    req.send_header = lambda *a, **k: None
    req.end_headers = lambda: None
    req.do_GET()
    body = req.wfile.getvalue().decode('utf-8')
    data = json.loads(body)
    assert req.code == 200
    assert data['ok'] is True
    assert isinstance(data['bars']['bars'], list)
    assert data['bars']['bars'][0]['time'] == '2026-06-22'
    assert 'DataFrame' not in body
    assert data['bars']['allow_xttrader'] is False
