from .common import payload, SAFETY
MODULES=['总览 / 工作流状态','QMT / xtdata 行情状态','Data Hub 行情缓存','Research 因子研究','候选池排名','Agent 投研','Strategy 策略信号','Risk Gate 风控审查','TradeIntent dry-run','Paper Trading / Shadow Replay','Monitoring / Alerts','Human Approval 人工确认','Account Readonly / 持仓只读','Safety / Live Disabled 安全边界']
def bootstrap(): return payload(service='unified_local_console', modules=MODULES, safety=SAFETY)
def status(): return payload(workflow=[{'module':m,'status':'READY_EMPTY','interactive':True,**SAFETY} for m in MODULES])
def feature_matrix(): return payload(features=[{'feature':m,'status':'READY_EMPTY','api':'/api/v1/...','read_only':True,'no_order_submitted':True} for m in MODULES])
