from qmt_ai_trading.trading_gateway.models import XtTraderBoundaryConfig
from qmt_ai_trading.trading_gateway.safety import validate_config

def test_safety_blocks_dangerous_config():
    assert validate_config(XtTraderBoundaryConfig(allow_order_submit=True))["status"] == "BLOCKED_BY_SAFETY"
    assert validate_config(XtTraderBoundaryConfig())["status"] == "PASS"
