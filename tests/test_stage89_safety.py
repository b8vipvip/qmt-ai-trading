from pathlib import Path
BAD=['from xtquant import xttrader','from xtquant.xttrader import XtQuantTrader','order_stock','place_order','execute_order','cancel_order']
def test_stage89_paper_sources_do_not_use_forbidden_trading_calls():
    text='\n'.join(p.read_text(encoding='utf-8') for p in Path('qmt_ai_trading/paper_trading').glob('*.py'))
    assert not any(b in text for b in BAD)
