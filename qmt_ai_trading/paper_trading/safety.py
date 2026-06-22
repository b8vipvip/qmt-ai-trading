PARTS=[["from xtquant import ","xttrader"],["from xtquant.","xttrader import ","XtQuantTrader"],["XtQuant","Trader"],["query_","account"],["query_","position"],["query_","order"],["query_","trade"],["order_","stock"],["place_","order"],["execute_","order"],["cancel_","order"],["真实","下单"],["真实","撤单"],["自动 ","approve"]]
def forbidden_terms(): return ["".join(x) for x in PARTS]
def safety_flags():
    from .models import SAFETY_FLAGS
    return dict(SAFETY_FLAGS)
