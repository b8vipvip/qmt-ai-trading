from qmt_ai_trading.trading_gateway import XtTraderBoundaryAdapter, XtTraderBoundaryConfig

def test_order_preview_statuses():
    a = XtTraderBoundaryAdapter(XtTraderBoundaryConfig())
    assert a.build_order_preview({"order_id":"1","side":"hold","quantity":0}, {"allowed":True})["preview_status"] == "NO_ACTION"
    assert a.build_order_preview({"order_id":"2","side":"buy","quantity":100}, {"allowed":False})["preview_status"] == "REJECTED_BY_RISK"
    p = a.build_order_preview({"order_id":"3","side":"buy","quantity":100,"price":2}, {"allowed":True,"decision":"APPROVED_DRY_RUN"})
    assert p["preview_status"] == "READY_FOR_MANUAL_REVIEW"
    assert p["submit_enabled"] is False
    assert p["real_order_submitted"] is False
