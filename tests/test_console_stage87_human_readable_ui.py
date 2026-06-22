from pathlib import Path


def test_xtdata_live_page_is_human_readable_not_raw_debug_console():
    app = Path('local_console_app_stage87/app.js').read_text(encoding='utf-8')
    css = Path('local_console_app_stage87/styles.css').read_text(encoding='utf-8')
    for text in ['行情模式', 'MiniQMT', '数据源', '安全状态', '真实 xtdata 行情', 'Sandbox 模拟行情', '只读安全', '当前仅启用 xtdata 只读行情']:
        assert text in app
    assert '<b>${k}</b>' not in app
    assert "fields=['real_market_data'" not in app
    assert 'componentJsonDetails' in app
    assert '<details class="debug-json"' in app


def test_xtdata_live_summary_and_chinese_kline_table_contract():
    app = Path('local_console_app_stage87/app.js').read_text(encoding='utf-8')
    for text in ['最新价 / 收盘价', '涨跌额', '涨跌幅', '成交量', '成交额', '最近行情时间', '数据源：']:
        assert text in app
    for header in ['日期', '时间戳', '开盘', '最高', '最低', '收盘', '涨跌幅', '成交量', '成交额', '数据源']:
        assert f'<th>{header}</th>' in app
    assert '最近 20 根' in app
    assert 'fmtNum' in app and '.toFixed(d)' in app
    assert 'fmtBig' in app and '亿' in app and '万' in app


def test_layout_prevents_page_level_horizontal_scroll_and_supports_components():
    css = Path('local_console_app_stage87/styles.css').read_text(encoding='utf-8')
    app = Path('local_console_app_stage87/app.js').read_text(encoding='utf-8')
    for token in ['overflow-x:hidden', 'position:sticky', 'status-grid', 'summary-grid', 'table-wrap', 'overflow:auto', 'position:sticky;top:0']:
        assert token in css
    for component in ['componentStatusCard', 'componentSafetyBanner', 'xtKTable', 'xtDiagnostics', 'componentJsonDetails', 'componentEmptyState', 'componentBackendMissing']:
        assert component in app
