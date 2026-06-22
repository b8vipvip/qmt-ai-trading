from qmt_ai_trading.console_api.routes.common import CONSOLE, read_json

def test_routes_read_unified_console_artifact_root_only():
    assert str(CONSOLE).replace('\\','/') == 'artifacts/reports/console'
    data=read_json('datahub','missing.json',{})
    assert data['source_path'].startswith('artifacts/reports/console/datahub/')
    assert 'local_console_' not in data['source_path']
