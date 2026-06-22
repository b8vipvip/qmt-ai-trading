from pathlib import Path
from qmt_ai_trading.market_gateway.xtdata_live_safety import scan_xtdata_live_safety, evaluate_live_config
from qmt_ai_trading.market_gateway import XtDataLiveReadOnlyConfig

def test_forbidden_imports_absent():
    res = scan_xtdata_live_safety([Path('qmt_ai_trading/market_gateway/xtdata_live_provider.py')])
    assert res['safety_status'] == 'PASS'

def test_dangerous_config_blocked():
    res = evaluate_live_config(XtDataLiveReadOnlyConfig(allow_order_submit=True))
    assert res['safety_status'] == 'BLOCKED'


def test_dangerous_runtime_flags_are_forced_off():
    from qmt_ai_trading.console_api.api_server import _xtdata_live_response
    qs = {
        'enable_xtdata': ['true'],
        'allow_import_xtdata': ['false'],
        'allow_xttrader': ['true'],
        'allow_order_submit': ['true'],
        'allow_account_query': ['true'],
    }
    res = _xtdata_live_response(qs, 'status')
    assert res['allow_xttrader'] is False
    assert res['allow_order_submit'] is False
    assert res['allow_account_query'] is False
    assert res['read_only'] is True
    assert res['no_xttrader'] is True
    assert len(res['warnings']) == 3

def test_no_xttrader_or_account_order_calls_in_live_files():
    text = Path('qmt_ai_trading/market_gateway/xtdata_live_provider.py').read_text(encoding='utf-8')
    for bad in ['XtQuantTrader', 'query_account', 'query_position', 'query_order', 'query_trade', 'order_stock', 'place_order', 'execute_order', 'cancel_order']:
        assert bad not in text


def test_live_provider_does_not_import_xttrader(monkeypatch):
    import builtins
    from qmt_ai_trading.market_gateway import XtDataLiveReadOnlyConfig, XtDataLiveReadOnlyProvider

    imported = []
    real_import = builtins.__import__
    def guarded_import(name, *args, **kwargs):
        imported.append(name)
        if 'xttrader' in name.lower():
            raise AssertionError('xttrader must not be imported')
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded_import)
    provider = XtDataLiveReadOnlyProvider(XtDataLiveReadOnlyConfig(enabled=True, allow_import_xtdata=False))
    provider.get_status()
    assert not any('xttrader' in x.lower() for x in imported)
