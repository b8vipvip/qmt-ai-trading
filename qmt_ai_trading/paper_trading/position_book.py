from __future__ import annotations
from .models import ShadowPosition, ShadowPortfolio
class ShadowPositionBook:
    def __init__(self, initial_cash=100000.0, whitelist=None): self.cash=float(initial_cash); self.positions={}; self.whitelist=set(whitelist or [])
    def apply_fill(self, fill, target_weight=0.0):
        if fill.fill_status!="FILLED" or fill.quantity<=0: return
        if self.whitelist and fill.symbol not in self.whitelist: return
        signed=fill.quantity if fill.side.lower()=="buy" else -fill.quantity; cost=signed*fill.simulated_fill_price; self.cash-=cost
        pos=self.positions.get(fill.symbol,{"quantity":0,"cost":0.0,"target_weight":target_weight})
        pos["quantity"]+=signed; pos["cost"]+=cost; pos["target_weight"]=target_weight; self.positions[fill.symbol]=pos
    def portfolio(self, prices):
        out=[]; value=0.0
        for sym,p in sorted(self.positions.items()):
            qty=p["quantity"]; last=float(prices.get(sym,1.0)); pv=round(qty*last, 6); value+=pv; avg=(p["cost"]/qty) if qty else 0.0
            out.append(ShadowPosition(sym,qty,avg,last,p.get("target_weight",0.0),0.0,pv,pv-p.get("cost",0.0)))
        total=self.cash+value
        for pos in out: pos.current_weight=(pos.position_value/total) if total else 0.0
        return ShadowPortfolio(self.cash,value,total,[x.to_dict() for x in out])
