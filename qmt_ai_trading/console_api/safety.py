from __future__ import annotations
import re
from typing import Any
class ConsoleSafetyError(ValueError): pass
FORBIDDEN_MARKERS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','fetch(\'/trade\')','fetch("/trade")','fetch(\'/order\')','fetch("/order")','fetch(\'/approve\')','fetch("/approve")','fetch(\'/account\')','fetch("/account")','fetch(\'/positions\')','fetch("/positions")','fetch(\'/assets\')','fetch("/assets")','fetch(\'/live\')','fetch("/live")','fetch(\'/notify\')','fetch("/notify")']
SENSITIVE=['.env','token','secret','credential','validation_logs','reports/logs','logs/validation_logs']
SHELL=re.compile(r'[;&|`$<>\\]|\b(cmd|powershell|bash|python\s+-c|py\s+-c)\b',re.I)
SAFE_POST_PATHS={
    '/api/v1/tasks/run',
    '/api/v1/ai/models/discover',
    '/api/v1/ai/models/stress-test',
    '/api/v1/ai/model-usage/draft',
    '/api/v1/account-readonly/refresh',
    '/api/v1/frontend/system/api-configs/save',
    '/api/v1/frontend/system/api-configs/test',
    '/api/v1/frontend/system/api-configs/purposes',
    '/api/v1/frontend/system/settings/save',
    '/api/v1/frontend/system/path/open',
    '/api/v1/frontend/system/qmt/test',
    '/api/v1/frontend/system/qmt/scan',
}
def assert_localhost_bind(host:str):
    if host not in {'127.0.0.1','localhost'}: raise ConsoleSafetyError('仅允许绑定 127.0.0.1/localhost，禁止 0.0.0.0 或公网/LAN')
def assert_safe_task_id(task_id:str):
    if not re.fullmatch(r'[a-z][a-z0-9_]{2,64}', task_id or ''): raise ConsoleSafetyError('非法 task_id')
def assert_no_shell_injection(value:Any):
    if isinstance(value,str) and SHELL.search(value): raise ConsoleSafetyError('检测到 shell 注入风险')
    if isinstance(value,dict):
        for k,v in value.items(): assert_no_shell_injection(k); assert_no_shell_injection(v)
    if isinstance(value,(list,tuple)):
        for v in value: assert_no_shell_injection(v)
def assert_no_path_traversal(value:Any):
    if isinstance(value,str) and ('..' in value.replace('\\','/') or value.startswith(('/', '\\'))): raise ConsoleSafetyError('禁止路径穿越或绝对路径')
    if isinstance(value,dict):
        for k,v in value.items(): assert_no_path_traversal(k); assert_no_path_traversal(v)
    if isinstance(value,(list,tuple)):
        for v in value: assert_no_path_traversal(v)
def assert_no_sensitive_path(value:Any):
    s=str(value).lower()
    if any(x in s for x in SENSITIVE): raise ConsoleSafetyError('禁止敏感路径/凭据/原始日志目录')
    if 'market_data/' in s or 'market_data\\' in s: raise ConsoleSafetyError('禁止暴露 market_data 原始目录')
def assert_safe_task_params(params:dict[str,Any]):
    if not isinstance(params,dict): raise ConsoleSafetyError('params 必须是对象')
    for bad in ['command','cmd','shell','script_path','path']:
        if bad in params: raise ConsoleSafetyError(f'禁止前端传入 {bad}')
    assert_no_shell_injection(params); assert_no_path_traversal(params); assert_no_sensitive_path(params)
def assert_task_allowed(task):
    if not getattr(task,'safe_mode',False) or not getattr(task,'dry_run_only',False): raise ConsoleSafetyError('任务未标记为安全 dry-run')
def assert_no_forbidden_live_task(task):
    if not getattr(task,'forbidden_in_live',True): raise ConsoleSafetyError('任务必须禁止实盘模式')
def assert_http_method_allowed(method:str,path:str):
    if method in {'PUT','PATCH','DELETE'}: raise ConsoleSafetyError('禁止 PUT/PATCH/DELETE')
    if method=='POST' and path.split('?',1)[0] not in SAFE_POST_PATHS: raise ConsoleSafetyError('POST 只允许白名单本地 API')
def classify_console_api_marker(text:str):
    return [m for m in FORBIDDEN_MARKERS if m in text]
def scan_console_api_for_forbidden_markers(text:str):
    hits=classify_console_api_marker(text)
    if hits: raise ConsoleSafetyError('发现禁止标记: '+', '.join(hits))
    return []
