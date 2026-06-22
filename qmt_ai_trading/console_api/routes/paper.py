from .common import payload, read_json
def status(): return payload(status='READY_EMPTY', report=read_json('paper','paper_trading_report.json',{}))
def orders(): return payload(orders=read_json('paper','paper_orders.json',{'orders':[]}).get('orders',[]))
def positions(): return payload(positions=read_json('paper','shadow_positions.json',{'positions':[]}).get('positions',[]))
def pnl(): return payload(pnl=read_json('paper','shadow_pnl.json',{}))
