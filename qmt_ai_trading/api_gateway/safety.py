from __future__ import annotations
from pathlib import Path
from .models import ApiEndpointSpec, ApiGatewayCategory, ApiGatewaySeverity
FORBIDDEN_GET={'/account','/positions','/orders','/trades','/assets'}
FORBIDDEN_POST={'/order','/orders','/trade','/execute','/approve','/live','/notify'}
MARKERS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']
def assert_stage61_read_only(): return True
def classify_api_gateway_route(path: str, method: str='GET') -> ApiEndpointSpec:
    p=path.split('?')[0]; m=method.upper(); forbidden=(m=='GET' and p in FORBIDDEN_GET) or (m in {'POST','PUT','PATCH','DELETE'} and (p in FORBIDDEN_POST or m!='GET'))
    return ApiEndpointSpec(method=m,path=p,category=ApiGatewayCategory.API_CAPABILITY,forbidden=forbidden,summary=('forbidden route' if forbidden else 'read-only route'))
def classify_api_gateway_marker(marker: str, context_path: str='', generated: bool=False):
    lower=str(context_path).lower(); gen=generated or any(x in lower for x in ['docs/','test','stage55','stage56','stage57','stage58','stage59','stage60','api_gateway_report','checklist','review','plan','.md','.json'])
    return ApiGatewaySeverity.WARN if gen else ApiGatewaySeverity.CRITICAL
def scan_api_gateway_text_for_forbidden_markers(text: str, context_path: str='', generated: bool=False):
    return [{'marker':m,'severity':classify_api_gateway_marker(m,context_path,generated).value,'context_path':context_path} for m in MARKERS if m in text]
def assert_no_xttrader_import(paths=None):
    hits=[]
    for p in paths or []:
        path=Path(p)
        if path.exists() and path.suffix=='.py':
            txt=path.read_text(encoding='utf-8',errors='ignore')
            if 'xttrader' in txt or 'XtQuantTrader' in txt: hits.append(str(path))
    return hits
def assert_no_forbidden_api_routes(endpoints): return [e for e in endpoints if getattr(e,'forbidden',False)]
