# -*- coding: utf-8 -*-
"""Generate a qmt_plan_order_dryrun_v2-compatible signal from ETF selection."""
from __future__ import print_function

import json
import os
from datetime import datetime

from data_tools.etf_universe import load_rotation_config


def load_json(path):
    if not os.path.exists(path):
        raise RuntimeError("[ERROR] 文件不存在: {0}".format(path))
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_rotation_signal(selected_payload, regime_payload, min_score_to_buy):
    selected = selected_payload.get("selected") or []
    regime = regime_payload.get("market_regime", "unknown")
    candidate = selected[0] if selected else None
    if not candidate:
        return {"stock_code": "", "last_close": 0.0, "signal": "HOLD", "position_intent": "NO_EXPOSURE_CHANGE",
                "raw_target_position_pct": None, "target_position_pct": None, "strategy_confidence": 0.0,
                "reason": "没有通过风控过滤的ETF候选"}
    score = float(candidate.get("score", 0.0))
    if regime == "bearish":
        signal, target, reason = "SELL_SIGNAL", 0.0, "市场环境偏空，轮动策略不生成买入信号"
        intent = "DECREASE_EXPOSURE"; confidence = 0.7
    elif regime == "bullish" and score >= float(min_score_to_buy):
        signal, target, reason = "BUY_SIGNAL", 1.0, "市场环境偏多且ETF趋势评分通过"
        intent = "INCREASE_EXPOSURE"; confidence = min(0.95, max(0.5, score / 100.0))
    else:
        signal, target, reason = "HOLD", None, "市场环境或ETF评分未达到买入条件"
        intent = "NO_EXPOSURE_CHANGE"; confidence = 0.5
    return {"stock_code": candidate["stock_code"], "last_close": float(candidate["last_close"]), "signal": signal,
            "position_intent": intent, "raw_target_position_pct": target, "target_position_pct": None,
            "strategy_confidence": confidence, "reason": reason, "rotation_score": score, "market_regime": regime}


def main():
    cfg, rotation = load_rotation_config()
    signals_dir = cfg.get("paths", {}).get("signals_dir", "signals")
    selected = load_json(os.path.join(signals_dir, "selected_etf.json"))
    regime = load_json(os.path.join(signals_dir, "market_regime.json"))
    result = build_rotation_signal(selected, regime, rotation.get("risk_limits", {}).get("min_score_to_buy", 60))
    result.update({"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "period": "1d",
                   "mode": "DRY_RUN", "safety_note": "本文件只生成dry-run信号，不执行任何实盘交易。"})
    out_file = cfg.get("paths", {}).get("target_signal_file", os.path.join(signals_dir, "target_signal.json"))
    out_dir = os.path.dirname(out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print("[OK] ETF轮动dry-run信号: {0}，输出: {1}".format(result["signal"], out_file))


if __name__ == "__main__":
    main()
