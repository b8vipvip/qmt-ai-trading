from qmt_ai_trading.trading_gateway.account_readonly_config import build_account_readonly_config
from qmt_ai_trading.trading_gateway.account_readonly_provider import AccountReadonlyProvider

def params(**extra):
    d={'enable_account_readonly':'true','allow_import_xttrader':'false','allow_connect_trade_session':'true','manual_confirmed':'true','read_only':'true','dry_run':'true'}; d.update(extra); return d

def test_missing_account_returns_specific_error(tmp_path):
    p=tmp_path/'ud'; p.mkdir(); cfg=build_account_readonly_config(tmp_path, {**params(), 'QMT_USERDATA_MINI_PATH':str(p)})
    got=AccountReadonlyProvider(cfg).diagnostics()
    assert got['error_code']=='CONFIG_ERROR_ACCOUNT_ID_MISSING'

def test_missing_path_returns_specific_error(tmp_path):
    cfg=build_account_readonly_config(tmp_path, {**params(), 'QMT_USERDATA_MINI_PATH':str(tmp_path/'missing'), 'QMT_ACCOUNT_ID':'123456789'})
    got=AccountReadonlyProvider(cfg).diagnostics()
    assert got['error_code']=='CONFIG_ERROR_USERDATA_PATH_NOT_EXISTS'

def test_connect_minus_one_includes_diagnostics(tmp_path):
    p=tmp_path/'ud'; p.mkdir(); cfg=build_account_readonly_config(tmp_path, {**params(allow_import_xttrader='true'), 'QMT_USERDATA_MINI_PATH':str(p), 'QMT_ACCOUNT_ID':'123456789'})
    class T:
        def connect(self): return -1
    provider=AccountReadonlyProvider(cfg, trader=T(), account=object())
    got=provider.diagnostics()
    assert got['error_code']=='CONNECT_ERROR'
    assert got['connect_result']==-1
    assert got['userdata_mini_path_exists'] is True
    assert got['account_id_masked']=='12****89'
    assert got['session_id']
