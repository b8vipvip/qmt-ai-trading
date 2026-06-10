# -*- coding: utf-8 -*-
"""Classify the broad market regime from index K-lines; never connects to trading APIs."""
from __future__ import print_function

import os
import sys

if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime

from data_tools.etf_universe import load_rotation_config


def classify_index(code, closes):
    if len(closes) < 60:
        return {"stock_code": code, "valid": False, "reason": "历史数据不足60日"}
    last = float(closes[-1])
    ma20 = sum(closes[-20:]) / 20.0
    ma60 = sum(closes[-60:]) / 60.0
    return {"stock_code": code, "valid": True, "last_close": last, "ma20": ma20, "ma60": ma60,
            "above_ma20": last > ma20, "above_ma60": last > ma60}


def classify_market(index_rows):
    valid = [row for row in index_rows if row.get("valid")]
    if not valid:
        return "unknown"
    bullish_points = sum((1 if row["above_ma20"] else 0) + (1 if row["above_ma60"] else 0) for row in valid)
    ratio = bullish_points / float(len(valid) * 2)
    if ratio >= 2.0 / 3.0:
        return "bullish"
    if ratio <= 1.0 / 3.0:
        return "bearish"
    return "sideways"


def analyze_market_regime(xtdata, index_codes, start_time, end_time=""):
    rows = []
    for code in index_codes:
        xtdata.download_history_data(code, "1d", start_time, end_time)
    data = xtdata.get_market_data(field_list=["close"], stock_list=index_codes, period="1d", start_time=start_time,
                                  end_time=end_time, count=-1, dividend_type="front", fill_data=False)
    for code in index_codes:
        try:
            closes = [float(data["close"].loc[code, col]) for col in list(data["close"].columns)]
            rows.append(classify_index(code, closes))
        except Exception as exc:
            rows.append({"stock_code": code, "valid": False, "reason": "行情读取失败: {0}".format(exc)})
    return {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "mode": "READ_ONLY",
            "market_regime": classify_market(rows), "indexes": rows,
            "safety_note": "市场环境模块只读取行情，不执行交易。"}


def main():
    from xtquant import xtdata
    cfg, rotation = load_rotation_config()
    codes = rotation.get("market_regime_indexes") or []
    if not codes:
        raise RuntimeError("[ERROR] market_regime_indexes 为空。")
    result = analyze_market_regime(xtdata, codes, rotation.get("lookback_start_time", "20230101"))
    signals_dir = cfg.get("paths", {}).get("signals_dir", "signals")
    os.makedirs(signals_dir, exist_ok=True)
    path = os.path.join(signals_dir, "market_regime.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print("[OK] 市场环境: {0}，输出: {1}".format(result["market_regime"], path))


if __name__ == "__main__":
    main()
