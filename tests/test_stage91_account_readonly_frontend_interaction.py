from pathlib import Path

def test_frontend_uses_refresh_not_parallel_asset_positions():
    html=Path('local_console_app_stage91/index.html').read_text(encoding='utf-8')
    assert '/api/v1/account-readonly/refresh' in html
    assert '正在启动隔离子进程进行账户/持仓只读查询，请稍等' in html
    assert '查询模式：隔离子进程，只读，查询后自动释放连接' in html
    assert 'Promise.all([refreshStatus(),refreshAssetOnly(),refreshPositionsOnly()])' not in html


def test_frontend_messages_for_refresh_states():
    html=Path('local_console_app_stage91/index.html').read_text(encoding='utf-8')
    assert "method:'POST'" in html
    assert 'enable_account_readonly' in html
    assert '正在启动隔离子进程进行账户/持仓只读查询，请稍等' in html
    assert '本地 API 白名单未放行账户只读 refresh，请先修复后端白名单。' in html
    assert '查询超时，请确认 MiniQMT 已登录交易账号，或重启 API 后重试。' in html
    assert "data.status==='SUBPROCESS_TIMEOUT'" in html
