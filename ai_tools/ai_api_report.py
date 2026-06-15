# -*- coding: utf-8 -*-
"""Build provider/model stability reports from AI API call metadata."""
from __future__ import print_function

import csv
import json
import os

from ai_tools.ai_api_logger import DEFAULT_LOG_PATH, ROOT_DIR

FIELDS = ["provider", "model", "calls", "successes", "success_rate", "average_latency_seconds", "http_429", "http_401", "http_403", "http_5xx", "timeout", "http_error", "url_error", "response_error", "last_success_time", "last_failure_time"]


def build_report(path=DEFAULT_LOG_PATH):
    groups = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                try: row = json.loads(line)
                except ValueError: continue
                key = (row.get("provider", ""), row.get("model", ""))
                item = groups.setdefault(key, {name: 0 for name in ["calls", "successes", "http_429", "http_401", "http_403", "http_5xx", "timeout", "http_error", "url_error", "response_error"]})
                item["provider"], item["model"] = key
                item["calls"] += 1; item["latency_total"] = item.get("latency_total", 0) + float(row.get("latency_seconds", 0))
                if row.get("success"):
                    item["successes"] += 1; item["last_success_time"] = row.get("time", "")
                else:
                    item["last_failure_time"] = row.get("time", "")
                error_type = row.get("error_type")
                if error_type in item: item[error_type] += 1
    result = []
    for item in groups.values():
        item["success_rate"] = round(100.0 * item["successes"] / item["calls"], 2)
        item["average_latency_seconds"] = round(item.pop("latency_total", 0) / item["calls"], 3)
        item.setdefault("last_success_time", ""); item.setdefault("last_failure_time", "")
        result.append(item)
    return sorted(result, key=lambda x: (x["provider"], x["model"]))


def write_report(rows, output_dir=None):
    output_dir = output_dir or os.path.join(ROOT_DIR, "logs")
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    with open(os.path.join(output_dir, "ai_api_report.json"), "w", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, "ai_api_report.csv"), "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)


def main():
    rows = build_report(); write_report(rows)
    if not rows: print("[WARN] 暂无 AI API 调用日志")
    for row in rows: print("[OK] {0}/{1}: calls={2}, success_rate={3}%, avg={4}s, errors=401:{5}/403:{6}/429:{7}/5xx:{8}/timeout:{9}".format(row["provider"], row["model"], row["calls"], row["success_rate"], row["average_latency_seconds"], row["http_401"], row["http_403"], row["http_429"], row["http_5xx"], row["timeout"]))

if __name__ == "__main__": main()
