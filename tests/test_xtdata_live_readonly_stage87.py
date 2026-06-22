from qmt_ai_trading.market_gateway import XtDataLiveReadOnlyConfig, XtDataLiveReadOnlyProvider

def test_default_fallback_is_safe():
    cfg = XtDataLiveReadOnlyConfig()
    assert cfg.enabled is False
    assert cfg.allow_import_xtdata is False
    provider = XtDataLiveReadOnlyProvider(cfg)
    status = provider.get_status()
    assert status['status'] == 'FALLBACK_TO_SANDBOX'
    assert status['real_market_data'] is False
    assert status['sandbox_fallback'] is True
    assert status['read_only'] is True
    assert status['no_xttrader'] is True
    assert status['no_order_submitted'] is True
    assert status['no_account_query'] is True

def test_snapshots_and_bars_fallback():
    p = XtDataLiveReadOnlyProvider()
    assert p.get_snapshot(['510300.SH'])['snapshots']
    assert p.get_bars('510300.SH','1d',3)['bars']


def test_enabled_params_use_real_xtdata_provider(monkeypatch):
    import sys, types
    fake_xtdata = types.SimpleNamespace(
        get_full_tick=lambda symbols: {symbols[0]: {'lastPrice': 3.14}},
        get_market_data=lambda *a, **k: {'close': [3.14]},
    )
    fake_pkg = types.SimpleNamespace(xtdata=fake_xtdata)
    monkeypatch.setitem(sys.modules, 'xtquant', fake_pkg)
    cfg = XtDataLiveReadOnlyConfig(
        enabled=True,
        allow_import_xtdata=True,
        allow_real_market_data=True,
        allow_connect_miniqmt=True,
        symbols=['510300.SH'],
        limit=20,
    )
    provider = XtDataLiveReadOnlyProvider(cfg)
    status = provider.get_status()
    assert status['real_market_data'] is True
    assert status['sandbox_fallback'] is False
    assert status['xtdata_imported'] is True
    assert status['mini_qmt_connected'] is True
    assert status['no_xttrader'] is True
    assert provider.get_snapshot(['510300.SH'])['real_market_data'] is True
    assert provider.get_bars('510300.SH', '1d', 20)['real_market_data'] is True
