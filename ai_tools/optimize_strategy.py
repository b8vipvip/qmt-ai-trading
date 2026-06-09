# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import csv
import importlib.util
import itertools
import os

from ai_tools.common import ensure_dir, load_json, save_json, validate_strategy_source


def load_strategy(path):
    with open(path, "r", encoding="utf-8") as handle:
        validate_strategy_source(handle.read())
    spec = importlib.util.spec_from_file_location("safe_research_strategy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not isinstance(getattr(module, "PARAM_GRID", None), dict):
        raise RuntimeError("策略必须定义字典 PARAM_GRID")
    return module


def parameter_sets(grid):
    keys = sorted(grid.keys())
    values = [grid[key] for key in keys]
    for combination in itertools.product(*values):
        yield dict(zip(keys, combination))


def get_close_data(stock_code, period, start_time, end_time):
    from xtquant import xtdata
    xtdata.download_history_data(stock_code, period, start_time, end_time)
    data = xtdata.get_market_data(
        field_list=["close"], stock_list=[stock_code], period=period,
        start_time=start_time, end_time=end_time, count=-1,
        dividend_type="front", fill_data=True
    )
    close_df = data["close"]
    dates = list(close_df.columns)
    return dates, [float(close_df.loc[stock_code, date]) for date in dates]


def score_periods(period_results):
    rates = [float(x["profit_rate"]) for x in period_results]
    drawdowns = [float(x["max_drawdown"]) for x in period_results]
    positive_ratio = float(len([x for x in rates if x > 0])) / len(rates)
    average_rate = sum(rates) / len(rates)
    worst_rate = min(rates)
    worst_drawdown = max(drawdowns)
    score = average_rate + 0.5 * worst_rate + 0.1 * positive_ratio - 0.5 * worst_drawdown
    return {
        "score": score, "average_profit_rate": average_rate, "worst_profit_rate": worst_rate,
        "worst_max_drawdown": worst_drawdown, "positive_period_ratio": positive_ratio
    }


def optimize(strategy, datasets):
    rows = []
    for params in parameter_sets(strategy.PARAM_GRID):
        period_results = []
        for dataset in datasets:
            result = strategy.backtest(dataset["dates"], dataset["closes"], params)
            for key in ["profit_rate", "max_drawdown", "trade_count"]:
                if key not in result:
                    raise RuntimeError("策略 backtest 结果缺少字段: {0}".format(key))
            period_results.append({
                "start_time": dataset["start_time"], "end_time": dataset["end_time"],
                "profit_rate": float(result["profit_rate"]),
                "max_drawdown": float(result["max_drawdown"]),
                "trade_count": int(result["trade_count"])
            })
        summary = score_periods(period_results)
        summary["params"] = params
        summary["period_results"] = period_results
        rows.append(summary)
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows


def write_csv(path, rows):
    param_names = sorted(rows[0]["params"].keys()) if rows else []
    fields = param_names + ["score", "average_profit_rate", "worst_profit_rate", "worst_max_drawdown", "positive_period_ratio"]
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            flat = dict(row["params"])
            for field in fields[len(param_names):]:
                flat[field] = row[field]
            writer.writerow(flat)


def main():
    parser = argparse.ArgumentParser(description="多时间段策略参数优化，仅使用历史行情")
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--output-dir", default="backtest_results")
    args = parser.parse_args()
    cfg = load_json(args.config)
    ai_cfg = cfg.get("ai_iteration", {})
    periods = ai_cfg.get("validation_periods", [])
    if len(periods) < 2:
        raise RuntimeError("ai_iteration.validation_periods 至少需要两个时间段")
    datasets = []
    for item in periods:
        dates, closes = get_close_data(cfg["stock_code"], cfg["period"], item[0], item[1])
        datasets.append({"start_time": item[0], "end_time": item[1], "dates": dates, "closes": closes})
    rows = optimize(load_strategy(args.strategy), datasets)
    output_dir = ensure_dir(args.output_dir)
    save_json(os.path.join(output_dir, "optimize-result.json"), rows)
    write_csv(os.path.join(output_dir, "optimize-result.csv"), rows)
    if rows:
        save_json(os.path.join(output_dir, "best-result.json"), rows[0])
    print("[OK] 多时间段参数优化完成: {0}".format(output_dir))
    print("[WARN] 优化结果仅用于研究和 dry-run，不执行实盘交易。")


if __name__ == "__main__":
    main()
