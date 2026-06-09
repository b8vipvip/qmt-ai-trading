# -*- coding: utf-8 -*-
# qmt_test_kline.py
# 只读测试：下载并读取历史K线，不下单

from xtquant import xtdata


def main():
    stocks = ["600000.SH", "000001.SZ", "510300.SH"]
    period = "1d"
    start_time = "20250101"
    end_time = "20260609"

    print("=== 下载历史K线 ===")
    for code in stocks:
        print("download:", code)
        xtdata.download_history_data(code, period, start_time, end_time)

    print("\n=== 读取历史K线 ===")
    data = xtdata.get_market_data(
        field_list=["time", "open", "high", "low", "close", "volume", "amount"],
        stock_list=stocks,
        period=period,
        start_time=start_time,
        end_time=end_time,
        count=-1,
        dividend_type="front",
        fill_data=True
    )

    print("返回字段:", list(data.keys()))

    close_df = data.get("close")
    volume_df = data.get("volume")

    print("\n--- close 最近5列 ---")
    print(close_df.iloc[:, -5:])

    print("\n--- volume 最近5列 ---")
    print(volume_df.iloc[:, -5:])

    print("\n历史K线测试完成，没有执行任何交易。")


if __name__ == "__main__":
    main()