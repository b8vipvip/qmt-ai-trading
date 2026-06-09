# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import json
import os
import re
from datetime import datetime

from ai_tools.ai_client import AIClient
from ai_tools.common import ensure_dir, validate_strategy_source


SYSTEM_PROMPT = """你是 A 股量化研究助手。只生成用于历史回测和 dry-run 信号的 Python 3.6 兼容策略。
禁止导入或调用任何交易、下单、撤单接口，禁止网络、文件、进程操作。只返回一个 Python 代码块。
策略必须定义 PARAM_GRID、backtest(dates, closes, params) 和 generate_signal(dates, closes, params)。
backtest 必须返回包含 profit_rate、max_drawdown、trade_count 的字典；信号只能是 BUY_SIGNAL、SELL_SIGNAL、HOLD。"""


def extract_code(text):
    match = re.search(r"```(?:python)?\s*(.*?)```", text, re.I | re.S)
    return match.group(1).strip() + "\n" if match else text.strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="根据分析报告生成安全的研究策略")
    parser.add_argument("--analysis", default="backtest_results/ai-analysis.json")
    parser.add_argument("--output-dir", default="strategies")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    with open(args.analysis, "r", encoding="utf-8") as handle:
        analysis = json.load(handle)
    prompt = "请根据以下回测分析生成一个简洁、可解释、降低过拟合风险的新策略：\n" + json.dumps(
        analysis, ensure_ascii=False, indent=2
    )
    source = extract_code(AIClient().chat(SYSTEM_PROMPT, prompt, temperature=0.1))
    validate_strategy_source(source)

    output_dir = ensure_dir(args.output_dir)
    name = args.name or "ai_strategy_{0}.py".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
    if not name.endswith(".py"):
        name += ".py"
    path = os.path.join(output_dir, os.path.basename(name))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("# -*- coding: utf-8 -*-\n")
        handle.write("# AI-generated research strategy. Backtest and dry-run signals only.\n")
        handle.write(source)
    print("[OK] 已生成并通过安全检查: {0}".format(path))
    print("[WARN] 生成策略仅可用于回测和 dry-run 信号。")


if __name__ == "__main__":
    main()
