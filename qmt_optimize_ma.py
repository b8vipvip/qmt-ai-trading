# -*- coding: utf-8 -*-
# qmt_optimize_ma.py
# 多参数均线策略优化脚本：只读行情 + 本地回测，不下单

import csv
import json
import os
from xtquant import xtdata


INITIAL_CASH = 100000.0
STOCK_CODE = "510300.SH"   # 先用沪深300ETF测试
PERIOD = "1d"
START_TIME = "20250101"
END_TIME = "20260609"

# ETF一般无卖出印花税；如果以后测普通股票，可改为 0.0005
COMMISSION_RATE = 0.0001
MIN_COMMISSION = 5.0
STAMP_TAX_SELL = 0.0
LOT_SIZE = 100

FAST_LIST = [3, 5, 8, 10, 13, 20]
SLOW_LIST = [15, 20, 30, 40, 60, 90, 120]

OUT_DIR = r"D:\AI\qmt\backtest_results"
RESULT_JSON = os.path.join(OUT_DIR, "optimize-result.json")
RESULT_CSV = os.path.join(OUT_DIR, "optimize-result.csv")
BEST_JSON = os.path.join(OUT_DIR, "best-result.json")


def calc_ma(values, window):
    result = []
    for i in range(len(values)):
        if i + 1 < window:
            result.append(None)
        else:
            result.append(sum(values[i + 1 - window:i + 1]) / window)
    return result


def calc_max_drawdown(equity_curve):
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]
    max_dd = 0.0

    for value in equity_curve:
        if value > peak:
            peak = value
        if peak > 0:
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd

    return max_dd


def run_backtest(dates, closes, fast_ma, slow_ma):
    fast = calc_ma(closes, fast_ma)
    slow = calc_ma(closes, slow_ma)

    cash = INITIAL_CASH
    position = 0
    trades = []
    equity_curve = []

    for i in range(len(dates)):
        date = str(dates[i])
        price = float(closes[i])

        # 先记录每日权益
        equity = cash + position * price
        equity_curve.append(equity)

        if fast[i] is None or slow[i] is None:
            continue

        # 快线上穿慢线，买入
        if fast[i] > slow[i] and position == 0:
            max_shares = int(cash / price / LOT_SIZE) * LOT_SIZE

            if max_shares > 0:
                amount = max_shares * price
                commission = max(amount * COMMISSION_RATE, MIN_COMMISSION)
                total_cost = amount + commission

                if total_cost <= cash:
                    cash -= total_cost
                    position += max_shares
                    trades.append({
                        "date": date,
                        "side": "buy",
                        "price": price,
                        "volume": max_shares,
                        "amount": amount,
                        "commission": commission,
                        "cash_after": cash
                    })

        # 快线跌破慢线，卖出
        elif fast[i] < slow[i] and position > 0:
            amount = position * price
            commission = max(amount * COMMISSION_RATE, MIN_COMMISSION)
            stamp_tax = amount * STAMP_TAX_SELL

            cash += amount - commission - stamp_tax

            trades.append({
                "date": date,
                "side": "sell",
                "price": price,
                "volume": position,
                "amount": amount,
                "commission": commission,
                "stamp_tax": stamp_tax,
                "cash_after": cash
            })

            position = 0

    final_equity = cash + position * float(closes[-1])
    profit = final_equity - INITIAL_CASH
    profit_rate = profit / INITIAL_CASH
    max_dd = calc_max_drawdown(equity_curve)

    buy_count = len([t for t in trades if t["side"] == "buy"])
    sell_count = len([t for t in trades if t["side"] == "sell"])

    return {
        "stock_code": STOCK_CODE,
        "period": PERIOD,
        "start_time": START_TIME,
        "end_time": END_TIME,
        "fast_ma": fast_ma,
        "slow_ma": slow_ma,
        "initial_cash": INITIAL_CASH,
        "final_equity": final_equity,
        "profit": profit,
        "profit_rate": profit_rate,
        "max_drawdown": max_dd,
        "trade_count": len(trades),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "position_left": position,
        "trades": trades
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("=== 下载历史K线 ===")
    xtdata.download_history_data(STOCK_CODE, PERIOD, START_TIME, END_TIME)

    print("=== 读取历史K线 ===")
    data = xtdata.get_market_data(
        field_list=["close"],
        stock_list=[STOCK_CODE],
        period=PERIOD,
        start_time=START_TIME,
        end_time=END_TIME,
        count=-1,
        dividend_type="front",
        fill_data=True
    )

    close_df = data["close"]
    dates = list(close_df.columns)
    closes = [float(close_df.loc[STOCK_CODE, d]) for d in dates]

    print("K线数量:", len(closes))
    print("开始优化参数...")

    results = []

    for fast_ma in FAST_LIST:
        for slow_ma in SLOW_LIST:
            if fast_ma >= slow_ma:
                continue

            result = run_backtest(dates, closes, fast_ma, slow_ma)
            results.append(result)

            print(
                "fast={0}, slow={1}, 收益率={2:.2f}%, 回撤={3:.2f}%, 交易次数={4}".format(
                    fast_ma,
                    slow_ma,
                    result["profit_rate"] * 100,
                    result["max_drawdown"] * 100,
                    result["trade_count"]
                )
            )

    # 排序逻辑：收益率高优先，回撤低次之，交易次数太少/太多都要后续人工判断
    results_sorted = sorted(
        results,
        key=lambda x: (x["profit_rate"], -x["max_drawdown"]),
        reverse=True
    )

    best = results_sorted[0] if results_sorted else None

    with open(RESULT_JSON, "w", encoding="utf-8") as f:
        json.dump(results_sorted, f, ensure_ascii=False, indent=2)

    with open(BEST_JSON, "w", encoding="utf-8") as f:
        json.dump(best, f, ensure_ascii=False, indent=2)

    with open(RESULT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank",
            "stock_code",
            "fast_ma",
            "slow_ma",
            "profit_rate",
            "max_drawdown",
            "trade_count",
            "final_equity",
            "profit"
        ])

        for idx, r in enumerate(results_sorted, 1):
            writer.writerow([
                idx,
                r["stock_code"],
                r["fast_ma"],
                r["slow_ma"],
                round(r["profit_rate"] * 100, 4),
                round(r["max_drawdown"] * 100, 4),
                r["trade_count"],
                round(r["final_equity"], 2),
                round(r["profit"], 2)
            ])

    print("\n=== 优化完成 ===")

    if best:
        print("最佳参数:")
        print("fast_ma:", best["fast_ma"])
        print("slow_ma:", best["slow_ma"])
        print("最终权益:", round(best["final_equity"], 2))
        print("收益:", round(best["profit"], 2))
        print("收益率:", round(best["profit_rate"] * 100, 2), "%")
        print("最大回撤:", round(best["max_drawdown"] * 100, 2), "%")
        print("交易次数:", best["trade_count"])

    print("\n结果文件:")
    print(RESULT_JSON)
    print(RESULT_CSV)
    print(BEST_JSON)
    print("\n注意：本脚本只做本地回测，没有执行任何实盘交易。")


if __name__ == "__main__":
    main()