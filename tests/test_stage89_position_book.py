from qmt_ai_trading.paper_trading.position_book import ShadowPositionBook
from qmt_ai_trading.paper_trading.models import PaperFill

def test_position_book_updates_cash_and_position():
    b=ShadowPositionBook(100000,['510300.SH']); b.apply_fill(PaperFill('f','o','510300.SH','buy',100,4.0,'t','FILLED'),0.25); p=b.portfolio({'510300.SH':4.1})
    assert p.paper_cash==99600 and p.paper_position_value==410 and p.positions[0]['quantity']==100

def test_position_book_ignores_hold_no_fill():
    b=ShadowPositionBook(100000,['588000.SH']); b.apply_fill(PaperFill('f','o','588000.SH','hold',100,2.0,'t','NO_FILL'),0); p=b.portfolio({'588000.SH':2.0})
    assert p.paper_cash==100000 and p.paper_position_value==0 and p.positions==[]
