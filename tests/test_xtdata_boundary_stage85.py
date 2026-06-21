import sys
from pathlib import Path
from qmt_ai_trading.market_gateway import XtDataAdapterConfig, XtDataAdapterBoundary, run_xtdata_boundary_stage85
from qmt_ai_trading.market_gateway.xtdata_safety import scan_import_guard

def test_xtdata_adapter_config_defaults_disabled():
    cfg = XtDataAdapterConfig()
    assert cfg.enabled is False
    assert cfg.dry_run is True
    assert cfg.read_only is True
    assert cfg.sandbox_fallback is True
    assert cfg.allow_import_xtdata is False
    assert cfg.allow_connect_miniqmt is False
    assert cfg.allow_real_market_data is False
    assert cfg.allow_xttrader is False

def test_xtdata_boundary_methods_return_disabled_and_do_not_import():
    before = set(sys.modules)
    adapter = XtDataAdapterBoundary(XtDataAdapterConfig())
    for result in [adapter.probe_import(), adapter.probe_connection(), adapter.get_snapshot(['510300.SH']), adapter.get_bars('510300.SH','1d'), adapter.subscribe(['510300.SH'])]:
        assert result['status'] == 'DISABLED'
        assert result['enabled'] is False
        assert result['dry_run'] is True
        assert result['read_only'] is True
        assert result['xtdata_imported'] is False
        assert result['mini_qmt_connected'] is False
        assert result['real_market_data'] is False
        assert result['sandbox_fallback'] is True
    assert 'xtquant' not in set(sys.modules) - before

def test_import_guard_detects_dangerous_import(tmp_path):
    f = tmp_path / 'bad.py'
    f.write_text('from xtquant import xtdata\n', encoding='utf-8')
    report = scan_import_guard([f])
    assert report['status'] == 'BLOCKED'
    assert report['violations']

def test_stage85_outputs_reports(tmp_path):
    out = tmp_path / 'xtdata'
    report = run_xtdata_boundary_stage85('.', str(out))
    assert report['enabled'] is False
    assert report['xtdata_imported'] is False
    assert report['mini_qmt_connected'] is False
    assert report['real_market_data'] is False
    for name in ['xtdata_adapter_config','xtdata_import_guard_report','xtdata_capability_probe','xtdata_safety_report','xtdata_boundary_report','frontend_xtdata_contract']:
        assert (out / f'{name}.json').exists()
        assert (out / f'{name}.md').exists()
