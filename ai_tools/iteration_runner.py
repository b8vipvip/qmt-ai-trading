# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime

from ai_tools.common import ensure_dir, load_json, save_json


FORBIDDEN_COMMAND_TEXT = ["order_stock", "cancel_order_stock", "live_trading_enabled=true"]


def run_command(command, cwd, log_path):
    text = " ".join(command).lower()
    for forbidden in FORBIDDEN_COMMAND_TEXT:
        if forbidden in text:
            raise RuntimeError("拒绝执行包含禁止内容的命令: {0}".format(forbidden))
    with open(log_path, "a", encoding="utf-8") as log_handle:
        log_handle.write("[RUN] {0}\n".format(" ".join(command)))
        result = subprocess.run(command, cwd=cwd, stdout=log_handle, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        raise RuntimeError("命令执行失败，退出码 {0}: {1}".format(result.returncode, " ".join(command)))


def copy_json_results(source_dir, output_dir):
    count = 0
    if not os.path.exists(source_dir):
        return count
    for name in os.listdir(source_dir):
        if name.lower().endswith(".json") and not name.startswith("ai-analysis"):
            source = os.path.join(source_dir, name)
            if os.path.isfile(source):
                shutil.copy2(source, os.path.join(output_dir, name))
                count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="安全 AI 策略多轮迭代，仅回测和 dry-run")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--rounds", type=int, default=None)
    args = parser.parse_args()
    cfg = load_json(args.config)
    if bool(cfg.get("live_trading_enabled")):
        raise RuntimeError("拒绝运行：live_trading_enabled 必须保持 false")
    ai_cfg = cfg.get("ai_iteration", {})
    rounds = args.rounds or int(ai_cfg.get("rounds", 1))
    if rounds < 1:
        raise RuntimeError("迭代轮数必须大于 0")

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    runs_dir = ensure_dir(os.path.join(root_dir, ai_cfg.get("runs_dir", "runs")))
    strategies_dir = ensure_dir(os.path.join(root_dir, ai_cfg.get("strategies_dir", "strategies")))
    source_results = cfg.get("paths", {}).get("backtest_results_dir", os.path.join(root_dir, "backtest_results"))
    backtest_script = ai_cfg.get("backtest_script", "qmt_backtest_ma.py")
    best_candidates = []

    for index in range(1, rounds + 1):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run_dir = ensure_dir(os.path.join(runs_dir, "run_{0}_round_{1}".format(stamp, index)))
        log_path = os.path.join(run_dir, "iteration.log")
        run_command([sys.executable, backtest_script], root_dir, log_path)
        if copy_json_results(source_results, run_dir) == 0:
            raise RuntimeError("回测完成但未在结果目录发现 JSON: {0}".format(source_results))
        run_command([sys.executable, "-m", "ai_tools.analyze_backtest", "--input-dir", run_dir], root_dir, log_path)
        strategy_name = "ai_strategy_{0}_round_{1}.py".format(stamp, index)
        run_command([
            sys.executable, "-m", "ai_tools.generate_strategy", "--analysis",
            os.path.join(run_dir, "ai-analysis.json"), "--output-dir", strategies_dir, "--name", strategy_name
        ], root_dir, log_path)
        strategy_path = os.path.join(strategies_dir, strategy_name)
        shutil.copy2(strategy_path, os.path.join(run_dir, strategy_name))
        run_command([
            sys.executable, "-m", "ai_tools.optimize_strategy", "--strategy", strategy_path,
            "--config", args.config, "--output-dir", run_dir
        ], root_dir, log_path)
        best_path = os.path.join(run_dir, "best-result.json")
        best = load_json(best_path)
        best["run_dir"] = run_dir
        best["strategy_path"] = strategy_path
        best_candidates.append(best)
        print("[OK] 第 {0} 轮完成: {1}".format(index, run_dir))

    best_candidates.sort(key=lambda item: float(item["score"]), reverse=True)
    save_json(os.path.join(runs_dir, "best-result.json"), best_candidates[0])
    print("[OK] AI 策略迭代完成，最优结果已保存。")
    print("[WARN] 全流程只读取历史行情、回测并生成 dry-run 信号，不执行实盘交易。")


if __name__ == "__main__":
    main()
