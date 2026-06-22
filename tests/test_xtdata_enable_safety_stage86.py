from pathlib import Path
from qmt_ai_trading.market_gateway import XtDataEnableRequest, audit_xtdata_config
from qmt_ai_trading.market_gateway.xtdata_safety import scan_import_guard

def test_config_audit_blocks_dangerous_config():
    req=XtDataEnableRequest(enable_xtdata=True, enable_real_market_data=True, connect_miniqmt=True, allow_xttrader=True, dry_run=False, read_only=False).to_dict()
    audit=audit_xtdata_config({'allow_import_xtdata':True}, req).to_dict()
    assert audit['decision']=='BLOCKED' and audit['safety_status']=='BLOCKED' and audit['requires_human_review'] is True
    names={f['name'] for f in audit['findings']}; assert {'enabled','allow_real_market_data','allow_connect_miniqmt','allow_xttrader','dry_run','read_only'} <= names

def test_stage86_source_has_no_forbidden_imports():
    report=scan_import_guard([Path('qmt_ai_trading/market_gateway'), Path('scripts/run_xtdata_enable_stage86.py')])
    assert report['status']=='PASS'; assert report['xtdata_imported'] is False

def test_validate_stage86_is_read_only_and_does_not_touch_sync_or_installer():
    text=Path('scripts/validate_stage86.ps1').read_text(encoding='utf-8')
    assert 'Set-Content' not in text and 'Add-Content' not in text
    assert 'Tee-Object -FilePath' not in text and 'Out-File' not in text
    assert '>>' not in text and ' > ' not in text
    assert 'install_run_qmt_tasks_logging.ps1' not in text
    assert 'sync_all.ps1' not in text
