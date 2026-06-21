from __future__ import annotations
import json, time, urllib.request, urllib.error
from .safety import assert_provider_request_allowed
class ProviderClient:
    def __init__(self, base_url:str, api_key:str='', timeout_seconds:int=60):
        self.base_url=assert_provider_request_allowed(base_url); self.api_key=api_key or ''; self.timeout=timeout_seconds
    def request_json(self, method:str, url:str, payload:dict|None=None):
        data=json.dumps(payload,ensure_ascii=False).encode('utf-8') if payload is not None else None
        headers={'Content-Type':'application/json'}
        if self.api_key: headers['Authorization']='Bearer '+self.api_key
        req=urllib.request.Request(url, data=data, headers=headers, method=method)
        started=time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw=resp.read().decode('utf-8'); return resp.status, json.loads(raw or '{}'), int((time.perf_counter()-started)*1000)
        except urllib.error.HTTPError as e:
            raw=e.read().decode('utf-8','replace') if e.fp else ''; return e.code, {'error':raw[:500]}, int((time.perf_counter()-started)*1000)
