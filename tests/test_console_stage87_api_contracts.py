from pathlib import Path
from qmt_ai_trading.console_api.api_server import make_handler

JS = Path('local_console_app_stage87/app.js').read_text(encoding='utf-8')
API_SERVER = Path('qmt_ai_trading/console_api/api_server.py').read_text(encoding='utf-8')


def test_all_fetch_calls_use_relative_paths():
    assert 'fetch("http://127.0.0.1' not in JS
    assert "fetch('http://127.0.0.1" not in JS
    assert 'fetch(url)' in JS
    assert "fetch('/api/v1/tasks/run'" in JS


def test_new_readonly_api_contracts_are_registered():
    make_handler('local_console_app_stage87')
    for route in [
        '/api/v1/factor/context',
        '/api/v1/factor/candidates/latest',
        '/api/v1/factor/report/latest',
        '/api/v1/backtest/report/latest',
        '/api/v1/backtest/performance/latest',
        '/api/v1/monitoring/alerts/latest',
        '/api/v1/monitoring/system-health/latest',
        '/api/v1/market/sandbox/report/latest',
        '/api/v1/market/sandbox/snapshots',
        '/api/v1/xtdata/boundary/report',
        '/api/v1/xtdata-enable/report',
        '/api/v1/xtdata-live/status',
        '/api/v1/xtdata-live/snapshots',
        '/api/v1/artifacts/migration/report',
        '/api/v1/artifacts/registry',
    ]:
        assert route in API_SERVER


def test_no_unexplained_placeholder_text_remains_in_stage87_html():
    html = Path('local_console_app_stage87/index.html').read_text(encoding='utf-8')
    assert '因子列表表格 / 因子配置面板' not in html
    assert '当前页面：仅占位' in JS
