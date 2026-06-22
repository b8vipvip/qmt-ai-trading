from __future__ import annotations
from .models import PaperOrder, PaperFill
from .input_loader import latest_price
FIXED_TIME="2026-06-22T00:00:00+00:00"
def is_allowed(decision:dict)->bool: return decision.get("allowed") is True or str(decision.get("decision","")).upper().startswith("APPROVED")
class PaperBroker:
    def __init__(self): self.orders=[]; self.fills=[]
    def submit_paper_order(self,intent,risk_decision):
        allowed=is_allowed(risk_decision); sym=intent.get("symbol",""); oid=f"paper-{intent.get('intent_id',sym)}"
        side=str(intent.get("side","buy")).lower()
        status="SKIPPED" if side=="hold" else ("PENDING" if allowed else "REJECTED")
        reason="策略建议 HOLD" if side=="hold" else ("" if allowed else "; ".join(risk_decision.get("reject_reasons") or risk_decision.get("reasons") or ["Risk Gate rejected"]))
        order=PaperOrder(oid,intent.get("intent_id",oid),sym,side,int(intent.get("quantity",0)),float(intent.get("intent_price",0) or intent.get("price",0) or 0),float(intent.get("target_weight",0) or 0),risk_decision,status,reason)
        self.orders.append(order); return order
    def simulate_fill(self,order,market_data):
        if str(order.side).lower()=="hold" or order.fill_status in {"SKIPPED","NO_ACTION"}:
            order.fill_status="SKIPPED"
            return None
        if order.fill_status=="REJECTED":
            fill=PaperFill(f"fill-{order.order_id}",order.order_id,order.symbol,order.side,0,0.0,FIXED_TIME,"REJECTED",order.reject_reason)
        else:
            price=latest_price(market_data,order.symbol); order.simulated_fill_price=price; order.fill_status="FILLED"
            fill=PaperFill(f"fill-{order.order_id}",order.order_id,order.symbol,order.side,order.quantity,price,FIXED_TIME,"FILLED","")
        self.fills.append(fill); return fill
    def list_orders(self): return self.orders
    def list_fills(self): return self.fills
