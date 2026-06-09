# -*- coding: utf-8 -*-
# qmt_backtest_ma.py
# 只读回测脚本：不连接交易接口，不下单

import json
import os
from xtquant import xtdata


INITIAL_CASH = 100000.0
STOCK_CODE = "510300.SH"   # 先用沪深300ETF做测试
PERIOD = "1d"
START_TIME = "20250101"
END_TIME = "20260609"

FAST_MA = 5
SLOW_MA = 20

COMMISSION_RATE = 0.0001   # 示例佣金，万1，可后续按你的真实佣金调整
MIN_COMMISSION = 5.0
STAMP_TAX_SELL = 0.0005    # A股卖出印花税示例，ETF通常不收，后续可按品种区分
LOT_SIZE = 100             # A股一手100股，ETF也按100份


def calc_ma(values, window):
    result = []
    for i in range(len(values)):
        if i + 1 < window:
            result.append(None)
        else:
            result.append(sum(values[i + 1 - window:i + 1]) / window)
    return result


def max_drawdown(equity_curve):
    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def main():
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

    fast = calc_ma(closes, FAST_MA)
    slow = calc_ma(closes, SLOW_MA)

    cash = INITIAL_CASH
    position = 0
    trades = []
    equity_curve = []

    for i in range(len(dates)):
        date = str(dates[i])
        price = closes[i]

        # 每日权益
        equity = cash + position * price
        equity_curve.append(equity)

        if fast[i] is None or slow[i] is None:
            continue

        # 简单策略：
        # 快线 > 慢线，满仓买入
        # 快线 < 慢线，清仓卖出
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

        elif fast[i] < slow[i] and position > 0:
            amount = position * price
            commission = max(amount * COMMISSION_RATE, MIN_COMMISSION)

            # 这里为了示例按股票卖出印花税计算；如果只测ETF，后续可改为0
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

    final_equity = cash + position * closes[-1]
    profit = final_equity - INITIAL_CASH
    profit_rate = profit / INITIAL_CASH
    dd = max_drawdown(equity_curve)

    result = {
        "stock_code": STOCK_CODE,
        "period": PERIOD,
        "start_time": START_TIME,
        "end_time": END_TIME,
        "initial_cash": INITIAL_CASH,
        "final_equity": final_equity,
        "profit": profit,
        "profit_rate": profit_rate,
        "max_drawdown": dd,
        "trade_count": len(trades),
        "fast_ma": FAST_MA,
        "slow_ma": SLOW_MA,
        "trades": trades
    }

    out_path = r"D:\AI\qmt\backtest_results\backtest-result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=== 回测完成 ===")
    print("标的:", STOCK_CODE)
    print("初始资金:", INITIAL_CASH)
    print("最终权益:", round(final_equity, 2))
    print("收益:", round(profit, 2))
    print("收益率:", round(profit_rate * 100, 2), "%")
    print("最大回撤:", round(dd * 100, 2), "%")
    print("交易次数:", len(trades))
    print("结果文件:", out_path)
    print("注意：本脚本只做本地回测，没有执行任何实盘交易。")


if __name__ == "__main__":
    main()