from pathlib import Path
from qmt_ai_trading.market_gateway import XtDataAdapterConfig
from qmt_ai_trading.market_gateway.xtdata_safety import evaluate_xtdata_safety, scan_import_guard

def test_safety_gate_blocks_enabled_and_real_data_flags():
    report = evaluate_xtdata_safety(XtDataAdapterConfig(enabled=True, allow_real_market_data=True, allow_import_xtdata=True, allow_connect_miniqmt=True, allow_xttrader=True))
    assert report['safety_status'] == 'BLOCKED'
    assert report['requires_human_review'] is True
    names = {i['name'] for i in report['issues']}
    assert {'enabled','allow_real_market_data','allow_import_xtdata','allow_connect_miniqmt','allow_xttrader'} <= names
    assert report['dry_run'] is True and report['read_only'] is True

def test_safety_gate_blocks_dangerous_terms_but_not_plain_xtdata():
    assert evaluate_xtdata_safety(text='xtdata boundary only')['safety_status'] == 'PASS'
    report = evaluate_xtdata_safety(text='XtQuantTrader place_order query_account')
    assert report['safety_status'] == 'BLOCKED'

def test_stage85_source_has_no_forbidden_imports():
    report = scan_import_guard([Path('qmt_ai_trading/market_gateway'), Path('scripts/run_xtdata_boundary_stage85.py')])
    assert report['status'] == 'PASS'
    assert report['xtdata_imported'] is False

def test_validate_stage85_is_read_only():
    text = Path('scripts/validate_stage85.ps1').read_text(encoding='utf-8')
    assert 'Set-Content' not in text and 'Add-Content' not in text
    assert 'Tee-Object -FilePath' not in text and 'Out-File' not in text
    assert '>>' not in text and ' > ' not in text
    assert 'install_run_qmt_tasks_logging.ps1' not in text
    assert 'sync_all.ps1' not in text
