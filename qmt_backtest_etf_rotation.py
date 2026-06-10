# -*- coding: utf-8 -*-
"""Read-only historical backtest for the ETF rotation candidate selector."""
from __future__ import print_function

import csv
import json
import os
from datetime import datetime, timedelta

from data_tools.etf_universe import load_etf_universe, load_rotation_config
from data_tools.etf_rotation_selector import fetch_market_data, score_etf


def max_drawdown(values):
    peak, result = values[0], 0.0
    for value in values:
        peak = max(peak, value)
        result = max(result, (peak - value) / peak if peak else 0.0)
    return result


def _is_rebalance_date(dates, index, mode):
    if index == 0 or mode == "daily":
        return True
    current = datetime.strptime(str(dates[index])[:8], "%Y%m%d")
    previous = datetime.strptime(str(dates[index - 1])[:8], "%Y%m%d")
    return current.isocalendar()[0:2] != previous.isocalendar()[0:2]


def backtest_period(dates, closes_by_code, amounts_by_code, rotation, start_time, end_time):
    equity, holdings, records, interval_returns = 1.0, [], [], []
    curve, curve_dates = [equity], [start_time]
    interval_start_equity = equity
    for index in range(61, len(dates)):
        date = str(dates[index])[:8]
        if date < start_time or date > end_time:
            continue

        if holdings:
            daily_returns = []
            for code in holdings:
                previous, current = closes_by_code[code][index - 1], closes_by_code[code][index]
                daily_returns.append(current / previous - 1.0 if previous > 0 else 0.0)
            equity *= 1.0 + sum(daily_returns) / float(len(daily_returns))
        curve.append(equity)
        curve_dates.append(date)

        if not _is_rebalance_date(dates, index, rotation.get("rebalance_mode", "weekly")):
            continue
        if records:
            interval_returns.append(equity / interval_start_equity - 1.0)
        interval_start_equity = equity
        scored = []
        for code in closes_by_code:
            row = score_etf(code, closes_by_code[code][:index + 1], amounts_by_code[code][:index + 1],
                            rotation.get("score_weights"), rotation.get("risk_limits"))
            if row.get("eligible"):
                scored.append(row)
        scored.sort(key=lambda row: row["score"], reverse=True)
        chosen = scored[:max(1, int(rotation.get("top_n", 1)))]
        new_holdings = [row["stock_code"] for row in chosen]
        if new_holdings != holdings:
            records.append({"date": date, "selected_etfs": ",".join(new_holdings),
                            "scores": ",".join(str(row["score"]) for row in chosen), "equity": equity})
        holdings = new_holdings
    if curve and interval_start_equity:
        interval_returns.append(equity / interval_start_equity - 1.0)

    total_return = equity - 1.0
    days = max(1, (datetime.strptime(end_time, "%Y%m%d") - datetime.strptime(start_time, "%Y%m%d")).days)
    annualized = equity ** (365.0 / days) - 1.0 if equity > 0 else -1.0
    wins = [item for item in interval_returns if item > 0]
    annual = {}
    for i in range(1, len(curve)):
        year = curve_dates[i][:4]
        annual.setdefault(year, [curve[i - 1], curve[i]])[1] = curve[i]
    annual_returns = dict((year, values[1] / values[0] - 1.0) for year, values in annual.items())
    return {"start_time": start_time, "end_time": end_time, "total_return": total_return,
            "annualized_return": annualized, "max_drawdown": max_drawdown(curve), "trade_count": len(records),
            "win_rate": len(wins) / float(len(interval_returns)) if interval_returns else 0.0,
            "positive_interval_ratio": len(wins) / float(len(interval_returns)) if interval_returns else 0.0,
            "worst_annual_return": min(annual_returns.values()) if annual_returns else 0.0,
            "annual_returns": annual_returns, "rebalance_records": records}


def _extract(data, codes, field):
    frame = data[field]
    return dict((code, [float(frame.loc[code, col]) for col in list(frame.columns)]) for code in codes)


def main():
    from xtquant import xtdata
    cfg, rotation = load_rotation_config()
    codes = load_etf_universe()
    periods = rotation.get("validation_periods") or cfg.get("ai_iteration", {}).get("validation_periods") or [[rotation.get("lookback_start_time", "20230101"), datetime.now().strftime("%Y%m%d")]]
    earliest = min(period[0] for period in periods)
    latest = max(period[1] for period in periods)
    warmup_start = (datetime.strptime(earliest, "%Y%m%d") - timedelta(days=180)).strftime("%Y%m%d")
    data = fetch_market_data(xtdata, codes, warmup_start, latest)
    dates = list(data["close"].columns)
    closes, amounts = _extract(data, codes, "close"), _extract(data, codes, "amount")
    results = [backtest_period(dates, closes, amounts, rotation, period[0], period[1]) for period in periods]
    output = {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "mode": "READ_ONLY_BACKTEST",
              "rebalance_mode": rotation.get("rebalance_mode", "weekly"), "periods": results,
              "safety_note": "回测只读取历史行情，不执行任何实盘交易。"}
    out_dir = cfg.get("paths", {}).get("backtest_results_dir", "backtest_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "etf_rotation_result.json"), "w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
    fields = ["period_start", "period_end", "date", "selected_etfs", "scores", "equity"]
    with open(os.path.join(out_dir, "etf_rotation_result.csv"), "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for result in results:
            for record in result["rebalance_records"]:
                row = dict(record); row.update({"period_start": result["start_time"], "period_end": result["end_time"]}); writer.writerow(row)
    print("[OK] ETF轮动回测完成，验证区间数: {0}".format(len(results)))


if __name__ == "__main__":
    main()
