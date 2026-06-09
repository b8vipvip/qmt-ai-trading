# -*- coding: utf-8 -*-
"""Minimal OpenAI-compatible client for QMT Python 3.6.

Credentials are read only from process environment or a local .env file.
"""
from __future__ import print_function

import json
import os
import urllib.error
import urllib.request


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
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


class AIClient(object):
    def __init__(self, api_key=None, base_url=None, model=None, timeout=120):
        load_dotenv()
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        self.timeout = timeout
        if not self.api_key:
            raise RuntimeError("缺少 OPENAI_API_KEY，请在本地 .env 或环境变量中配置")

    def chat(self, system_prompt, user_prompt, temperature=0.2):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"},
            method="POST"
        )
        try:
            response = urllib.request.urlopen(request, timeout=self.timeout)
            body = response.read().decode("utf-8")
            data = json.loads(body)
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError("AI API 请求失败 HTTP {0}: {1}".format(exc.code, detail[:500]))
        except (urllib.error.URLError, KeyError, ValueError) as exc:
            raise RuntimeError("AI API 请求失败: {0}".format(exc))
