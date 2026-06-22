from .common import payload, SAFETY
def status(): return payload(status='DISABLED_FOR_SAFETY', safety=SAFETY, live_trading_enabled=False, allow_xttrader=False, allow_order_submit=False, allow_order_cancel=False)
def live(): return payload(status='DISABLED', feature_status='DISABLED_FOR_SAFETY', live_trading_enabled=False, allow_order_submit=False, allow_order_cancel=False, allow_xttrader=False, message='Live trading is disabled by default')
