# -*- coding: utf-8 -*-
"""Generate research-only ETF rotation explanations; never places orders."""
from __future__ import print_function

import json
import sys

from ai_tools.ai_router_client import AIRouterClient

SYSTEM_PROMPT = "你是 ETF 轮动研究分析助手。只分析 ETF 轮动结果、市场环境和风险提示；不得输出实盘下单建议，不得绕过 dry-run 或 safety guard。"


def explain_rotation(rotation_data, client=None):
    client = client or AIRouterClient()
    prompt = "请输出 ETF 轮动研究分析：\n" + json.dumps(rotation_data, ensure_ascii=False, indent=2)
    return client.chat(SYSTEM_PROMPT, prompt, temperature=0.2, task="ai_rotation_explainer")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "signals/selected_etf.json"
    with open(path, "r", encoding="utf-8") as handle: data = json.load(handle)
    print(explain_rotation(data))

if __name__ == "__main__": main()
