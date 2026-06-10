# -*- coding: utf-8 -*-
"""Score and select ETF rotation candidates using read-only QMT market data."""
from __future__ import print_function

import os
import sys

if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import json
import math
from datetime import datetime

from data_tools.etf_universe import load_etf_universe, load_rotation_config


DEFAULT_WEIGHTS = {
    "return_5d": 0.15, "return_20d": 0.25, "return_60d": 0.20,
    "ma20_trend": 0.15, "ma60_trend": 0.15, "liquidity": 0.10,
    "drawdown_penalty": -0.20, "volatility_penalty": -0.10
}


def _mean(values):
    return sum(values) / float(len(values)) if values else 0.0


def _return(values, days):
    return values[-1] / values[-1 - days] - 1.0


def calculate_max_drawdown(values):
    peak = values[0]
    result = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            result = max(result, (peak - value) / peak)
    return result


def calculate_volatility(values):
    returns = [values[i] / values[i - 1] - 1.0 for i in range(1, len(values)) if values[i - 1] > 0]
    if len(returns) < 2:
        return 0.0
    avg = _mean(returns)
    variance = sum((item - avg) ** 2 for item in returns) / float(len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252.0)


def _momentum_score(value):
    return max(0.0, min(100.0, 50.0 + value * 200.0))


def score_etf(code, closes, amounts, weights=None, risk_limits=None, name=None):
    """Return a score record, or a skipped record when safety filters fail."""
    weights = dict(DEFAULT_WEIGHTS, **(weights or {}))
    risk_limits = risk_limits or {}
    record = {"stock_code": code, "stock_name": name or code, "eligible": False, "skip_reason": ""}
    if len(closes) < 61 or len(amounts) < 20:
        record["skip_reason"] = "历史数据不足，至少需要61根日K线和20日成交额"
        return record
    recent_closes = closes[-61:]
    recent_amounts = amounts[-20:]
    if any(not math.isfinite(value) or value <= 0 for value in recent_closes):
        record["skip_reason"] = "近61日存在无效价格，数据不足或停牌"
        return record
    if any(not math.isfinite(value) for value in recent_amounts) or amounts[-1] <= 0:
        record["skip_reason"] = "最新交易日无有效成交额，可能停牌"
        return record

    ret5, ret20, ret60 = _return(closes, 5), _return(closes, 20), _return(closes, 60)
    ma20, ma60 = _mean(closes[-20:]), _mean(closes[-60:])
    avg_amount = _mean(amounts[-20:])
    drawdown = calculate_max_drawdown(closes[-60:])
    volatility = calculate_volatility(closes[-60:])
    record.update({
        "last_close": closes[-1], "return_5d": ret5, "return_20d": ret20, "return_60d": ret60,
        "ma20": ma20, "ma60": ma60, "above_ma20": closes[-1] > ma20, "above_ma60": closes[-1] > ma60,
        "avg_amount_20d": avg_amount, "max_drawdown_60d": drawdown, "annualized_volatility_60d": volatility
    })
    if avg_amount < float(risk_limits.get("min_avg_amount_20d", 0)):
        record["skip_reason"] = "近20日平均成交额低于限制"
        return record
    if drawdown > float(risk_limits.get("max_drawdown_60d", 1.0)):
        record["skip_reason"] = "近60日最大回撤超过限制"
        return record

    components = {
        "return_5d": _momentum_score(ret5), "return_20d": _momentum_score(ret20),
        "return_60d": _momentum_score(ret60), "ma20_trend": 100.0 if closes[-1] > ma20 else 0.0,
        "ma60_trend": 100.0 if closes[-1] > ma60 else 0.0, "liquidity": 100.0,
        "drawdown_penalty": drawdown * 100.0, "volatility_penalty": volatility * 100.0
    }
    record["score_components"] = components
    record["score"] = round(sum(components[key] * float(weights.get(key, 0.0)) for key in components), 4)
    record["eligible"] = True
    return record


def _series(frame, code):
    return [float(frame.loc[code, col]) for col in list(frame.columns)]


def get_etf_name(xtdata, code):
    try:
        detail = xtdata.get_instrument_detail(code)
        return detail.get("InstrumentName") or detail.get("ProductName") or code
    except Exception:
        return code


def fetch_market_data(xtdata, codes, start_time, end_time=""):
    for code in codes:
        xtdata.download_history_data(code, "1d", start_time, end_time)
    return xtdata.get_market_data(field_list=["close", "amount"], stock_list=codes, period="1d",
                                  start_time=start_time, end_time=end_time, count=-1,
                                  dividend_type="front", fill_data=False)


def select_from_market_data(codes, data, rotation, xtdata=None):
    rows = []
    for code in codes:
        try:
            name = get_etf_name(xtdata, code) if xtdata else code
            rows.append(score_etf(code, _series(data["close"], code), _series(data["amount"], code),
                                  rotation.get("score_weights"), rotation.get("risk_limits"), name))
        except Exception as exc:
            rows.append({"stock_code": code, "stock_name": code, "eligible": False,
                         "skip_reason": "行情读取失败: {0}".format(exc)})
    eligible = sorted([row for row in rows if row.get("eligible")], key=lambda row: row["score"], reverse=True)
    return rows, eligible[:max(1, int(rotation.get("top_n", 1)))]


def write_outputs(cfg, rows, selected):
    signals_dir = cfg.get("paths", {}).get("signals_dir", "signals")
    os.makedirs(signals_dir, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {"generated_at": now, "mode": "READ_ONLY", "scores": rows}
    selected_payload = {"generated_at": now, "mode": "DRY_RUN", "selected": selected,
                        "safety_note": "ETF轮动只筛选候选，不执行任何实盘交易。"}
    with open(os.path.join(signals_dir, "etf_scores.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    with open(os.path.join(signals_dir, "selected_etf.json"), "w", encoding="utf-8") as handle:
        json.dump(selected_payload, handle, ensure_ascii=False, indent=2)
    fields = ["stock_code", "stock_name", "eligible", "score", "last_close", "return_5d", "return_20d",
              "return_60d", "above_ma20", "above_ma60", "avg_amount_20d", "max_drawdown_60d",
              "annualized_volatility_60d", "skip_reason"]
    with open(os.path.join(signals_dir, "etf_scores.csv"), "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def main():
    from xtquant import xtdata
    cfg, rotation = load_rotation_config()
    codes = load_etf_universe()
    data = fetch_market_data(xtdata, codes, rotation.get("lookback_start_time", "20230101"))
    rows, selected = select_from_market_data(codes, data, rotation, xtdata)
    write_outputs(cfg, rows, selected)
    print("[OK] ETF评分完成，合格ETF: {0}，入选ETF: {1}".format(len([x for x in rows if x.get("eligible")]), len(selected)))


if __name__ == "__main__":
    main()
