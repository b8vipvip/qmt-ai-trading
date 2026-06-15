# -*- coding: utf-8 -*-
"""Load OpenAI-compatible providers without persisting or displaying secrets."""
from __future__ import print_function

import json
import os
import time

from ai_tools.ai_client import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AIProviderPool(object):
    def __init__(self, config_path=None, environ=None, now_func=None):
        load_dotenv()
        self.environ = environ if environ is not None else os.environ
        self.config_path = config_path or os.path.join(ROOT_DIR, "ai_providers.local.json")
        self.now_func = now_func or time.time
        self._cooldowns = {}
        self.providers = self._load()

    def _load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle).get("providers", [])
        else:
            raw = [{
                "name": "legacy-openai", "enabled": True,
                "base_url": self.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "api_key_env": "OPENAI_API_KEY",
                "models": [self.environ.get("OPENAI_MODEL", "gpt-4.1-mini")],
                "timeout_seconds": 120, "cooldown_seconds": 300
            }]
        providers = []
        for item in raw:
            if not item.get("enabled", True):
                continue
            key_env = item.get("api_key_env", "")
            api_key = self.environ.get(key_env, "")
            if not api_key:
                continue
            models = [model for model in item.get("models", []) if model]
            if not models:
                continue
            providers.append({
                "name": item.get("name", "unnamed"),
                "base_url": item.get("base_url", "").rstrip("/"),
                "api_key_env": key_env,
                "api_key": api_key,
                "models": models,
                "timeout_seconds": float(item.get("timeout_seconds", 60)),
                "cooldown_seconds": float(item.get("cooldown_seconds", 300))
            })
        return providers

    def candidates(self):
        now = self.now_func()
        result = []
        for provider in self.providers:
            for model in provider["models"]:
                if self._cooldowns.get((provider["name"], model), 0) <= now and self._cooldowns.get((provider["name"], None), 0) <= now:
                    result.append((provider, model))
        return result

    def cooldown(self, provider_name, model=None, seconds=300):
        self._cooldowns[(provider_name, model)] = self.now_func() + seconds

    def cooldown_candidate(self, provider, model=None):
        self.cooldown(provider["name"], model, provider["cooldown_seconds"])
