# -*- coding: utf-8 -*-
"""Backward-compatible entry point for the AI provider/model router."""
from __future__ import print_function

import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_dotenv(path=None):
    path = path or os.path.join(ROOT_DIR, ".env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


class AIClient(object):
    def __init__(self, api_key=None, base_url=None, model=None, timeout=120):
        load_dotenv()
        from ai_tools.ai_provider_pool import AIProviderPool
        from ai_tools.ai_router_client import AIRouterClient
        environ = dict(os.environ)
        if api_key is not None: environ["OPENAI_API_KEY"] = api_key
        if base_url is not None: environ["OPENAI_BASE_URL"] = base_url
        if model is not None: environ["OPENAI_MODEL"] = model
        pool = AIProviderPool(environ=environ)
        if pool.providers and timeout is not None:
            pool.providers[0]["timeout_seconds"] = timeout
        self.router = AIRouterClient(pool=pool)

    def chat(self, system_prompt, user_prompt, temperature=0.2, task="default"):
        return self.router.chat(system_prompt, user_prompt, temperature=temperature, task=task)
