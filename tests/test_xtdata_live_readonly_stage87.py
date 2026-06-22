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
