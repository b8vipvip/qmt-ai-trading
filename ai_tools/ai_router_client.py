# -*- coding: utf-8 -*-
"""Failover router for OpenAI-compatible chat completion APIs."""
from __future__ import print_function

import json
import socket
import time
import urllib.error
import urllib.request

from ai_tools.ai_api_logger import log_ai_api_call
from ai_tools.ai_provider_pool import AIProviderPool


def classify_error(exc):
    if isinstance(exc, urllib.error.HTTPError):
        code = exc.code
        if code == 401: return "http_401", code
        if code == 403: return "http_403", code
        if code == 429: return "http_429", code
        if 500 <= code <= 599: return "http_5xx", code
        return "http_error", code
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "timeout", None
    if isinstance(exc, urllib.error.URLError):
        if isinstance(getattr(exc, "reason", None), socket.timeout):
            return "timeout", None
        return "url_error", None
    return "response_error", None


class AIRouterClient(object):
    def __init__(self, pool=None, logger=None, opener=None):
        self.pool = pool or AIProviderPool()
        self.logger = logger or log_ai_api_call
        self.opener = opener or urllib.request.urlopen
        if not self.pool.providers:
            raise RuntimeError("没有可用的 AI API 供应商；请配置本地密钥环境变量")

    def chat(self, system_prompt, user_prompt, temperature=0.2, task="default"):
        failures = []
        skipped_providers = set()
        input_chars = len(system_prompt) + len(user_prompt)
        for provider, model in self.pool.candidates():
            if provider["name"] in skipped_providers:
                continue
            attempts = self.pool.max_retries + 1
            for attempt in range(attempts):
                started = time.time()
                try:
                    output = self._request(provider, model, system_prompt, user_prompt, temperature)
                    self._log(task, provider, model, True, None, "", "", started, input_chars, len(output))
                    return output
                except Exception as exc:
                    error_type, status = classify_error(exc)
                    message = self._error_message(exc)
                    if provider["api_key"]:
                        message = message.replace(provider["api_key"], "[REDACTED]")
                    self._log(task, provider, model, False, status, error_type, message, started, input_chars, 0)
                    failures.append("{0}/{1}: {2} ({3})".format(provider["name"], model, error_type, message[:120]))
                    if error_type in ("http_401", "http_403"):
                        self.pool.cooldown_candidate(provider, None)
                        skipped_providers.add(provider["name"])
                        break
                    if error_type == "http_429":
                        self.pool.cooldown_candidate(provider, model)
                        break
                    if error_type not in ("timeout", "http_5xx") or attempt == attempts - 1:
                        break
        raise RuntimeError("所有 AI API provider/model 调用均失败: " + "; ".join(failures))

    def _request(self, provider, model, system_prompt, user_prompt, temperature):
        payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": temperature}
        request = urllib.request.Request(provider["base_url"] + "/chat/completions", data=json.dumps(payload).encode("utf-8"), headers={"Authorization": "Bearer " + provider["api_key"], "Content-Type": "application/json"}, method="POST")
        response = self.opener(request, timeout=provider["timeout_seconds"])
        data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _error_message(exc):
        if isinstance(exc, urllib.error.HTTPError):
            try: return exc.read().decode("utf-8", "replace")[:300]
            except Exception: pass
        return str(exc)[:300]

    def _log(self, task, provider, model, success, status, error_type, message, started, input_chars, output_chars):
        self.logger({"task": task, "provider": provider["name"], "model": model, "success": success, "status_code": status, "error_type": error_type, "error_message": message, "latency_seconds": time.time() - started, "input_chars": input_chars, "output_chars": output_chars})
