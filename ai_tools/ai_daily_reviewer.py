# -*- coding: utf-8 -*-
"""Create a safe daily ETF shadow-trading review without trading actions."""
from __future__ import print_function
import csv, datetime, json, os, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SECRET_VALUE_RE = re.compile(r"(?i)(api[_-]?key|token|secret|authorization)\s*[:=]\s*([^\s,;}]+)")
_BEARER_RE = re.compile(r"(?i)bearer\s+[^\s,;}]+")


def _json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (IOError, OSError, ValueError):
        return {}


def _safe_error_message(exc):
    text = str(exc).replace("\r", " ").replace("\n", " ")
    text = _SECRET_VALUE_RE.sub(lambda match: match.group(1) + "=***", text)
    text = _BEARER_RE.sub("Bearer ***", text)
    return text[:300]


def _ai_metadata(mode="template", called=False, provider=None, model=None, duration_ms=0,
                 error_type=None, error_message=None):
    return {"review_mode": mode, "ai_called": bool(called), "provider": provider,
            "model": model, "duration_ms": duration_ms, "error_type": error_type,
            "error_message": error_message}


def generate_daily_review(root=ROOT, now=None, ai_client=None, provider=None, model=None):
    """Write the daily review; AI is only called when an explicit client is supplied."""
    now = now or datetime.datetime.now()
    day = now.strftime("%Y%m%d")
    signals, shadow = os.path.join(root, "signals"), os.path.join(root, "shadow")
    names = ["market_regime", "etf_scores", "selected_etf", "target_signal", "order_plan", "daily_status"]
    data = {name: _json(os.path.join(signals, name + ".json")) for name in names}
    snap = _json(os.path.join(shadow, "daily_snapshot.json"))
    curve = []
    try:
        with open(os.path.join(shadow, "equity_curve.csv"), "r", encoding="utf-8") as handle:
            curve = list(csv.DictReader(handle))
    except (IOError, OSError):
        pass
    api_calls = 0
    try:
        with open(os.path.join(root, "logs", "ai_api_calls.jsonl"), "r", encoding="utf-8") as handle:
            api_calls = len([line for line in handle if line.strip()])
    except (IOError, OSError):
        pass
    report = {"date": day, "market_environment": data["market_regime"], "etf_scores": data["etf_scores"],
              "rotation_signal": data["selected_etf"], "target_signal": data["target_signal"],
              "virtual_actions": snap.get("today_trades", []), "virtual_positions": snap.get("positions", {}),
              "total_asset": snap.get("total_asset"), "floating_pnl": snap.get("floating_pnl"),
              "max_drawdown": snap.get("max_drawdown"), "equity_curve_days": len(curve),
              "ai_api_call_records": api_calls,
              "risk_triggered": bool(data["order_plan"].get("warnings") or data["daily_status"].get("risk_warnings")),
              "tomorrow_watch": ["市场环境变化", "ETF 轮动排名与成交量", "影子盘回撤"],
              "risk_reminder": "仅供研究复盘，不是投资建议，不执行实盘交易。"}
    metadata = _ai_metadata(provider=provider, model=model)
    if ai_client is not None:
        started = time.time()
        try:
            prompt = json.dumps(report, ensure_ascii=False)
            report["ai_review"] = ai_client.chat("只做 ETF 影子盘复盘，不提供实盘交易指令。", prompt,
                                                  temperature=0.2, task="ai_daily_reviewer")
            metadata = _ai_metadata("ai", True, provider, model, int(round((time.time() - started) * 1000)))
        except Exception as exc:
            metadata = _ai_metadata("ai_failed_fallback", True, provider, model,
                                    int(round((time.time() - started) * 1000)),
                                    exc.__class__.__name__, _safe_error_message(exc))
    report.update(metadata)
    out = os.path.join(root, "reports")
    os.makedirs(out, exist_ok=True)
    json_path, markdown_path = os.path.join(out, "daily_report_" + day + ".json"), os.path.join(out, "daily_report_" + day + ".md")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    text = "# ETF 影子盘每日复盘\n\n## 复盘模式\n- review_mode：{0}\n- ai_called：{1}\n\n## 今日市场环境\n{2}\n\n## ETF 轮动信号解释\n{3}\n\n## 今日虚拟交易动作\n{4}\n\n## 当前虚拟持仓\n{5}\n\n## 虚拟收益和最大回撤\n- 总资产：{6}\n- 浮动盈亏：{7}\n- 最大回撤：{8}\n\n## 风控是否触发\n{9}\n\n## 明日观察重点\n- 市场环境变化\n- ETF 轮动排名与成交量\n- 影子盘回撤\n\n## 风险提醒\n**不是投资建议，不执行实盘交易。**\n".format(report["review_mode"], str(report["ai_called"]).lower(), json.dumps(report["market_environment"], ensure_ascii=False), json.dumps(report["rotation_signal"], ensure_ascii=False), json.dumps(report["virtual_actions"], ensure_ascii=False), json.dumps(report["virtual_positions"], ensure_ascii=False), report["total_asset"], report["floating_pnl"], report["max_drawdown"], "是" if report["risk_triggered"] else "否")
    with open(markdown_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return report


if __name__ == "__main__":
    generate_daily_review()
