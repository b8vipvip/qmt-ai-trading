from pathlib import Path
from qmt_ai_trading.market_gateway.xtdata_live_safety import scan_xtdata_live_safety, evaluate_live_config
from qmt_ai_trading.market_gateway import XtDataLiveReadOnlyConfig

def test_forbidden_imports_absent():
    res = scan_xtdata_live_safety([Path('qmt_ai_trading/market_gateway/xtdata_live_provider.py')])
    assert res['safety_status'] == 'PASS'

def test_dangerous_config_blocked():
    res = evaluate_live_config(XtDataLiveReadOnlyConfig(allow_order_submit=True))
    assert res['safety_status'] == 'BLOCKED'
