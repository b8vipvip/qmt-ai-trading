from pathlib import Path

def test_api_server_has_no_runtime_stage_paths():
    text=Path('qmt_ai_trading/console_api/api_server.py').read_text(encoding='utf-8')
    assert 'local_console_' not in text
    assert 'stage88' not in text.lower() and 'stage91' not in text.lower()

def test_routes_common_has_no_legacy_runtime_fallback():
    text=Path('qmt_ai_trading/console_api/routes/common.py').read_text(encoding='utf-8')
    assert 'LEGACY' not in text
    assert 'local_console_' not in text
