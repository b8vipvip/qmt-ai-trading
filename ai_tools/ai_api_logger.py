# -*- coding: utf-8 -*-
"""JSONL logger for AI API metadata. Never records credentials or prompts."""
from __future__ import print_function

import datetime
import json
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOG_PATH = os.path.join(ROOT_DIR, "logs", "ai_api_calls.jsonl")


def log_ai_api_call(record, path=None):
    path = path or DEFAULT_LOG_PATH
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent)
    safe = {
        "time": record.get("time") or datetime.datetime.utcnow().isoformat() + "Z",
        "task": record.get("task", "default"), "provider": record.get("provider", ""),
        "model": record.get("model", ""), "success": bool(record.get("success")),
        "status_code": record.get("status_code"), "error_type": record.get("error_type", ""),
        "error_message": str(record.get("error_message", ""))[:300],
        "latency_seconds": round(float(record.get("latency_seconds", 0)), 3),
        "input_chars": int(record.get("input_chars", 0)), "output_chars": int(record.get("output_chars", 0))
    }
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(safe, ensure_ascii=False) + "\n")
