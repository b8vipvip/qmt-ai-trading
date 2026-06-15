# -*- coding: utf-8 -*-
"""Load OpenAI-compatible providers from one local .env without exposing secrets."""
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
        self.timeout_seconds = self._number("AI_TIMEOUT_SECONDS", 60)
        self.cooldown_seconds = self._number("AI_COOLDOWN_SECONDS", 300)
        self.max_retries = max(0, int(self._number("AI_MAX_RETRIES", 1)))
        self.providers = self._load()

    def _number(self, name, default):
        try:
            return float(self.environ.get(name, default))
        except (TypeError, ValueError):
            return float(default)

    def _load(self):
        if self.environ.get("AI_PROVIDER_1_BASE_URL", "").strip():
            return self._load_env_providers()
        legacy = self._load_legacy_provider()
        if legacy:
            return legacy
        return self._load_json_providers()

    def _load_env_providers(self):
        providers = []
        index = 1
        while True:
            prefix = "AI_PROVIDER_{0}_".format(index)
            base_url = self.environ.get(prefix + "BASE_URL", "").strip()
            if not base_url:
                break
            api_key = self.environ.get(prefix + "API_KEY", "").strip()
            models = [item.strip() for item in self.environ.get(prefix + "MODELS", "").split(",") if item.strip()]
            if api_key and models:
                providers.append(self._provider(
                    self.environ.get(prefix + "NAME", "").strip() or "provider_{0}".format(index),
                    base_url, api_key, models, prefix + "API_KEY"))
            index += 1
        return providers

    def _load_legacy_provider(self):
        api_key = self.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            return []
        base_url = self.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        model = self.environ.get("OPENAI_MODEL", "gpt-4.1-mini").strip()
        if not base_url or not model:
            return []
        return [self._provider("legacy-openai", base_url, api_key, [model], "OPENAI_API_KEY")]

    def _load_json_providers(self):
        if not os.path.exists(self.config_path):
            return []
        with open(self.config_path, "r", encoding="utf-8") as handle:
            raw = json.load(handle).get("providers", [])
        providers = []
        for item in raw:
            if not item.get("enabled", True):
                continue
            key_env = item.get("api_key_env", "")
            api_key = self.environ.get(key_env, "").strip()
            models = [model.strip() for model in item.get("models", []) if model and model.strip()]
            if api_key and item.get("base_url", "").strip() and models:
                providers.append(self._provider(item.get("name", "unnamed"), item["base_url"], api_key, models, key_env,
                                                item.get("timeout_seconds"), item.get("cooldown_seconds")))
        return providers

    def _provider(self, name, base_url, api_key, models, key_env, timeout=None, cooldown=None):
        return {"name": name, "base_url": base_url.rstrip("/"), "api_key_env": key_env,
                "api_key": api_key, "models": models,
                "timeout_seconds": float(timeout if timeout is not None else self.timeout_seconds),
                "cooldown_seconds": float(cooldown if cooldown is not None else self.cooldown_seconds)}

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
