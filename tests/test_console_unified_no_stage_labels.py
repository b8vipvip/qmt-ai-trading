from pathlib import Path
from qmt_ai_trading.console_api.api_server import make_handler
from scripts import run_console_api

def test_frontend_has_no_stage_labels():
    text='\n'.join(p.read_text(encoding='utf-8') for p in Path('local_console_app').glob('*.*'))
    for label in ['Stage77','Stage88','Stage91','/api/v1/stage88','BACKEND_MISSING']:
        assert label not in text

def test_default_static_dir_is_unified():
    text=Path('scripts/run_console_api.py').read_text(encoding='utf-8')
    assert "default='local_console_app'" in text

def test_health_service_source():
    text=Path('qmt_ai_trading/console_api/api_server.py').read_text(encoding='utf-8')
    assert "'service':'unified_local_console'" in text
