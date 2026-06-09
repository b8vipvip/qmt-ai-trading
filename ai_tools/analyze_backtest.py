# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import json
import os
import statistics

from ai_tools.common import ensure_dir, save_json


def find_results(input_dir):
    results = []
    for name in sorted(os.listdir(input_dir)):
        if not name.lower().endswith(".json") or name.startswith("ai-analysis"):
            continue
        path = os.path.join(input_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                value = json.load(handle)
            items = value if isinstance(value, list) else [value]
            for item in items:
                if isinstance(item, dict) and "profit_rate" in item:
                    copied = dict(item)
                    copied["source_file"] = name
                    results.append(copied)
        except (ValueError, OSError):
            continue
    return results


def analyze(results):
    if not results:
        raise RuntimeError("未找到包含 profit_rate 的回测 JSON 结果")
    rates = [float(x.get("profit_rate", 0)) for x in results]
    drawdowns = [float(x.get("max_drawdown", 0)) for x in results]
    trades = [int(x.get("trade_count", 0)) for x in results]
    positive = len([x for x in rates if x > 0])
    avg_rate = sum(rates) / len(rates)
    std_rate = statistics.pstdev(rates) if len(rates) > 1 else 0.0
    positive_ratio = float(positive) / len(rates)
    risks = []
    if len(results) < 3:
        risks.append("有效验证区间少于 3 个，样本外证据不足")
    if positive_ratio < 0.6:
        risks.append("正收益区间占比低于 60%，年度/区间稳定性不足")
    if std_rate > max(abs(avg_rate), 0.01):
        risks.append("区间收益波动大于平均收益，可能依赖特定行情")
    if min(trades) < 5:
        risks.append("部分区间交易次数少于 5 次，统计可信度较低")
    if max(drawdowns) > 0.25:
        risks.append("最大回撤超过 25%，风险较高")
    if not risks:
        risks.append("未发现明显规则型过拟合信号，仍需样本外和仿真验证")
    level = "high" if len(risks) >= 3 else ("medium" if len(risks) >= 2 else "low")
    return {
        "sample_count": len(results),
        "average_profit_rate": avg_rate,
        "best_profit_rate": max(rates),
        "worst_profit_rate": min(rates),
        "profit_rate_stddev": std_rate,
        "average_max_drawdown": sum(drawdowns) / len(drawdowns),
        "worst_max_drawdown": max(drawdowns),
        "average_trade_count": float(sum(trades)) / len(trades),
        "positive_period_ratio": positive_ratio,
        "annual_stability": "stable" if positive_ratio >= 0.7 and std_rate <= max(abs(avg_rate), 0.01) else "unstable",
        "overfitting_risk": level,
        "risk_findings": risks,
        "safety_note": "仅分析历史回测，不执行任何交易。"
    }


def render_text(report):
    lines = [
        "AI 策略回测分析（规则型初筛）",
        "样本数: {0}".format(report["sample_count"]),
        "平均收益率: {0:.2f}%".format(report["average_profit_rate"] * 100),
        "最差收益率: {0:.2f}%".format(report["worst_profit_rate"] * 100),
        "最差最大回撤: {0:.2f}%".format(report["worst_max_drawdown"] * 100),
        "平均交易次数: {0:.2f}".format(report["average_trade_count"]),
        "正收益区间占比: {0:.2f}%".format(report["positive_period_ratio"] * 100),
        "年度/区间稳定性: {0}".format(report["annual_stability"]),
        "过拟合风险: {0}".format(report["overfitting_risk"]),
        "风险提示:"
    ]
    lines.extend(["- " + item for item in report["risk_findings"]])
    lines.append("安全说明: " + report["safety_note"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="分析本地回测结果，不执行交易")
    parser.add_argument("--input-dir", default="backtest_results")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    output_dir = ensure_dir(args.output_dir or args.input_dir)
    report = analyze(find_results(args.input_dir))
    save_json(os.path.join(output_dir, "ai-analysis.json"), report)
    with open(os.path.join(output_dir, "ai-analysis.txt"), "w", encoding="utf-8") as handle:
        handle.write(render_text(report))
    print("[OK] 回测分析已保存到: {0}".format(output_dir))
    print("[WARN] 该分析仅用于研究，不构成投资建议，不执行实盘交易。")


if __name__ == "__main__":
    main()
