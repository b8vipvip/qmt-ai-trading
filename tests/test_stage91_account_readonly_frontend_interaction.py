from pathlib import Path

def test_frontend_uses_refresh_not_parallel_asset_positions():
    html=Path('local_console_app_stage91/index.html').read_text(encoding='utf-8')
    assert '/api/v1/account-readonly/refresh' in html
    assert '正在启动隔离只读查询进程' in html
    assert '查询模式：隔离子进程，只读，查询后自动释放连接' in html
    assert 'Promise.all([refreshStatus(),refreshAssetOnly(),refreshPositionsOnly()])' not in html
