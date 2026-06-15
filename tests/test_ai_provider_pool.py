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
from ai_tools.ai_router_client import classify_error
from ai_tools.ai_router_client import AIRouterClient


class AIProviderPoolTest(unittest.TestCase):
    def make_config(self):
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        json.dump({"providers": [
            {"name": "active", "enabled": True, "base_url": "https://example.com/v1",
             "api_key_env": "ACTIVE_KEY", "models": ["model-a", "model-b"]},
            {"name": "disabled", "enabled": False, "base_url": "https://disabled.example/v1",
             "api_key_env": "DISABLED_KEY", "models": ["model-c"]}
        ]}, handle)
        handle.close()
        return handle.name

    def test_reads_config_and_skips_disabled_provider(self):
        path = self.make_config()
        try:
            pool = AIProviderPool(config_path=path, environ={"ACTIVE_KEY": "secret", "DISABLED_KEY": "other"})
            self.assertEqual([p["name"] for p in pool.providers], ["active"])
            self.assertEqual([model for _, model in pool.candidates()], ["model-a", "model-b"])
        finally:
            os.unlink(path)

    def test_missing_key_is_skipped_without_leaking_key_name(self):
        path = self.make_config()
        try:
            pool = AIProviderPool(config_path=path, environ={})
            self.assertEqual(pool.providers, [])
            self.assertNotIn("ACTIVE_KEY", repr(pool.providers))
        finally:
            os.unlink(path)

    def test_error_classification(self):
        for code, expected in [(401, "http_401"), (403, "http_403"), (429, "http_429"), (503, "http_5xx")]:
            exc = urllib.error.HTTPError("url", code, "error", {}, io.BytesIO(b"detail"))
            self.assertEqual(classify_error(exc), (expected, code))
        self.assertEqual(classify_error(socket.timeout()), ("timeout", None))
        self.assertEqual(classify_error(urllib.error.URLError(socket.timeout())), ("timeout", None))

    def test_log_does_not_contain_api_key(self):
        directory = tempfile.mkdtemp()
        path = os.path.join(directory, "calls.jsonl")
        secret = "super-secret-api-key"
        log_ai_api_call({"provider": "p", "model": "m", "success": False,
                         "error_message": "safe error", "api_key": secret}, path=path)
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        self.assertNotIn(secret, content)
        self.assertNotIn("api_key", content)

    def test_router_redacts_key_from_failure_log(self):
        path = self.make_config()
        records = []
        try:
            pool = AIProviderPool(config_path=path, environ={"ACTIVE_KEY": "secret-value"})
            def failing_opener(request, timeout=None):
                raise urllib.error.URLError("request exposed secret-value")
            router = AIRouterClient(pool=pool, logger=records.append, opener=failing_opener)
            with self.assertRaises(RuntimeError) as caught:
                router.chat("system", "user")
            self.assertNotIn("secret-value", str(caught.exception))
            self.assertTrue(records)
            self.assertNotIn("secret-value", json.dumps(records))
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
