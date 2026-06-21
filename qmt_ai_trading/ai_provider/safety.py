from __future__ import annotations
import json, re
from urllib.parse import urlparse
class AiProviderSafetyError(ValueError): pass
ALLOWED_TEST_SIZES={1000,3000,5000}; MAX_MODELS=5; MAX_REQUESTS=15
PRIVATE_PREFIXES=('10.','192.168.')
def mask_api_key(api_key:str|None)->str:
    if not api_key: return ''
    s=str(api_key)
    if len(s)<=8: return s[:1]+'***'+s[-1:]
    return s[:4]+'***'+s[-4:]
def assert_safe_base_url(base_url:str):
    if not isinstance(base_url,str) or not base_url.strip(): raise AiProviderSafetyError('base_url 不能为空')
    b=base_url.strip()
    low=b.lower()
    if low.startswith('file://') or re.match(r'^[a-zA-Z]:[\\/]', b) or b.startswith(('/', '\\')): raise AiProviderSafetyError('禁止 file:// 或本地文件路径')
    u=urlparse(b)
    if u.scheme not in {'https','http'}: raise AiProviderSafetyError('base_url 必须是 https 或本地 http')
    host=(u.hostname or '').lower()
    if u.scheme=='http' and host not in {'127.0.0.1','localhost'}: raise AiProviderSafetyError('http 仅允许 127.0.0.1/localhost')
    if host.startswith(PRIVATE_PREFIXES) or re.match(r'^172\.(1[6-9]|2\d|3[01])\.',host): raise AiProviderSafetyError('禁止内网扫描地址')
    return b.rstrip('/')
def assert_no_localhost_sensitive_redirect(base_url:str): return assert_safe_base_url(base_url)
def assert_provider_request_allowed(base_url:str): return assert_safe_base_url(base_url)
def assert_no_api_key_in_text(text:str, api_key:str|None=None):
    if api_key and api_key in (text or ''): raise AiProviderSafetyError('报告中包含明文 API Key')
def assert_no_api_key_in_report(report, api_key:str|None=None): assert_no_api_key_in_text(json.dumps(report,ensure_ascii=False), api_key)
def assert_safe_test_sizes(test_sizes):
    sizes=[int(x) for x in (test_sizes or [1000,3000,5000])]
    if not sizes or any(x not in ALLOWED_TEST_SIZES for x in sizes): raise AiProviderSafetyError('test_sizes 只能是 1000/3000/5000')
    return sizes
def assert_safe_selected_models(models):
    if not isinstance(models,list) or not models: raise AiProviderSafetyError('selected_models 不能为空')
    if len(models)>MAX_MODELS: raise AiProviderSafetyError('selected_models 最多 5 个')
    for m in models:
        if not isinstance(m,str) or not re.fullmatch(r'[\w.\-:/]{1,128}',m): raise AiProviderSafetyError('非法 model_id')
    return models
def assert_stress_test_limits(models,test_sizes):
    ms=assert_safe_selected_models(models); ss=assert_safe_test_sizes(test_sizes)
    if len(ms)*len(ss)>MAX_REQUESTS: raise AiProviderSafetyError('每轮总请求数最多 15')
    return ms,ss
