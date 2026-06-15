# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import json
import os
import socket
import tempfile
import unittest
import urllib.error

from ai_tools.ai_api_logger import log_ai_api_call
from ai_tools.ai_provider_pool import AIProviderPool
from ai_tools.ai_router_client import AIRouterClient, classify_error


class AIProviderPoolTest(unittest.TestCase):
    def pool(self, values):
        return AIProviderPool(config_path=os.path.join(tempfile.gettempdir(), "missing-provider-file.json"), environ=values)

    def test_env_single_provider_single_model(self):
        pool = self.pool({"AI_PROVIDER_1_BASE_URL": " https://one.test/v1/ ", "AI_PROVIDER_1_API_KEY": "secret", "AI_PROVIDER_1_MODELS": " model-a "})
        self.assertEqual(pool.providers[0]["name"], "provider_1")
        self.assertEqual(pool.providers[0]["base_url"], "https://one.test/v1")
        self.assertEqual([m for _, m in pool.candidates()], ["model-a"])

    def test_env_single_provider_multiple_models(self):
        pool = self.pool({"AI_PROVIDER_1_NAME": "one", "AI_PROVIDER_1_BASE_URL": "https://one.test/v1", "AI_PROVIDER_1_API_KEY": "secret", "AI_PROVIDER_1_MODELS": "a, b, ,c"})
        self.assertEqual(pool.providers[0]["models"], ["a", "b", "c"])

    def test_env_multiple_providers_and_globals(self):
        values = {"AI_PROVIDER_1_BASE_URL": "https://one.test/v1", "AI_PROVIDER_1_API_KEY": "one", "AI_PROVIDER_1_MODELS": "a,b", "AI_PROVIDER_2_BASE_URL": "https://two.test/v1", "AI_PROVIDER_2_API_KEY": "two", "AI_PROVIDER_2_MODELS": "c", "AI_TIMEOUT_SECONDS": "12", "AI_COOLDOWN_SECONDS": "34", "AI_MAX_RETRIES": "2"}
        pool = self.pool(values)
        self.assertEqual([p["name"] for p in pool.providers], ["provider_1", "provider_2"])
        self.assertEqual([m for _, m in pool.candidates()], ["a", "b", "c"])
        self.assertEqual((pool.providers[0]["timeout_seconds"], pool.max_retries), (12.0, 2))

    def test_missing_api_key_skips_provider(self):
        pool = self.pool({"AI_PROVIDER_1_BASE_URL": "https://one.test/v1", "AI_PROVIDER_1_MODELS": "a", "AI_PROVIDER_2_BASE_URL": "https://two.test/v1", "AI_PROVIDER_2_API_KEY": "two", "AI_PROVIDER_2_MODELS": "b"})
        self.assertEqual([p["name"] for p in pool.providers], ["provider_2"])

    def test_legacy_openai_environment_compatibility(self):
        pool = self.pool({"OPENAI_API_KEY": "secret", "OPENAI_BASE_URL": "https://legacy.test/v1", "OPENAI_MODEL": "legacy-model"})
        self.assertEqual([(p["name"], m) for p, m in pool.candidates()], [("legacy-openai", "legacy-model")])

    def test_error_classification(self):
        for code, expected in [(401, "http_401"), (403, "http_403"), (429, "http_429"), (500, "http_5xx"), (599, "http_5xx")]:
            exc = urllib.error.HTTPError("url", code, "error", {}, io.BytesIO(b"detail"))
            self.assertEqual(classify_error(exc), (expected, code))
        self.assertEqual(classify_error(socket.timeout()), ("timeout", None))
        self.assertEqual(classify_error(urllib.error.URLError(socket.timeout())), ("timeout", None))

    def test_log_and_router_do_not_contain_api_key(self):
        directory = tempfile.mkdtemp(); path = os.path.join(directory, "calls.jsonl"); secret = "super-secret-api-key"
        log_ai_api_call({"provider": "p", "model": "m", "success": False, "error_message": "safe", "api_key": secret}, path=path)
        records = []; pool = self.pool({"AI_PROVIDER_1_BASE_URL": "https://one.test/v1", "AI_PROVIDER_1_API_KEY": secret, "AI_PROVIDER_1_MODELS": "a", "AI_MAX_RETRIES": "0"})
        def fail(request, timeout=None): raise urllib.error.URLError("exposed " + secret)
        with self.assertRaises(RuntimeError) as caught: AIRouterClient(pool=pool, logger=records.append, opener=fail).chat("system", "user")
        with open(path, "r", encoding="utf-8") as handle: logged = handle.read()
        self.assertNotIn(secret, logged + json.dumps(records) + str(caught.exception))
        self.assertNotIn("api_key", logged)


if __name__ == "__main__": unittest.main()
