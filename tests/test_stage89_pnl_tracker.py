from qmt_ai_trading.paper_trading.position_book import ShadowPositionBook
from qmt_ai_trading.paper_trading.pnl_tracker import compute_pnl

def test_pnl_tracker_computes_return():
    p=ShadowPositionBook(100000).portfolio({}); pnl=compute_pnl(p,100000)
    assert pnl.daily_pnl==0 and pnl.max_drawdown==0
