# -*- coding: utf-8 -*-
"""Create a safe daily ETF shadow-trading review without trading actions."""
from __future__ import print_function
import csv, datetime, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _json(path):
    try:
        with open(path, "r", encoding="utf-8") as h: return json.load(h)
    except (IOError, OSError, ValueError): return {}
def generate_daily_review(root=ROOT, now=None):
    now = now or datetime.datetime.now(); day = now.strftime("%Y%m%d"); signals = os.path.join(root,"signals"); shadow = os.path.join(root,"shadow")
    names = ["market_regime","etf_scores","selected_etf","target_signal","order_plan","daily_status"]
    data = {n:_json(os.path.join(signals,n+".json")) for n in names}; snap = _json(os.path.join(shadow,"daily_snapshot.json"))
    curve = []
    try:
        with open(os.path.join(shadow, "equity_curve.csv"), "r", encoding="utf-8") as handle: curve = list(csv.DictReader(handle))
    except (IOError, OSError): pass
    api_calls = 0
    try:
        with open(os.path.join(root, "logs", "ai_api_calls.jsonl"), "r", encoding="utf-8") as handle: api_calls = len([line for line in handle if line.strip()])
    except (IOError, OSError): pass
    report = {"date":day,"market_environment":data["market_regime"],"etf_scores":data["etf_scores"],"rotation_signal":data["selected_etf"],"target_signal":data["target_signal"],"virtual_actions":snap.get("today_trades",[]),"virtual_positions":snap.get("positions",{}),"total_asset":snap.get("total_asset"),"floating_pnl":snap.get("floating_pnl"),"max_drawdown":snap.get("max_drawdown"),"equity_curve_days":len(curve),"ai_api_call_records":api_calls,"risk_triggered":bool(data["order_plan"].get("warnings") or data["daily_status"].get("risk_warnings")),"tomorrow_watch":["市场环境变化","ETF 轮动排名与成交量","影子盘回撤"],"risk_reminder":"仅供研究复盘，不是投资建议，不执行实盘交易。"}
    out = os.path.join(root,"reports"); os.makedirs(out, exist_ok=True); jp=os.path.join(out,"daily_report_"+day+".json"); mp=os.path.join(out,"daily_report_"+day+".md")
    with open(jp,"w",encoding="utf-8") as h: json.dump(report,h,ensure_ascii=False,indent=2)
    text = "# ETF 影子盘每日 AI 复盘\n\n## 今日市场环境\n{0}\n\n## ETF 轮动信号解释\n{1}\n\n## 今日虚拟交易动作\n{2}\n\n## 当前虚拟持仓\n{3}\n\n## 虚拟收益和最大回撤\n- 总资产：{4}\n- 浮动盈亏：{5}\n- 最大回撤：{6}\n\n## 风控是否触发\n{7}\n\n## 明日观察重点\n- 市场环境变化\n- ETF 轮动排名与成交量\n- 影子盘回撤\n\n## 风险提醒\n**不是投资建议，不执行实盘交易。**\n".format(json.dumps(report["market_environment"],ensure_ascii=False),json.dumps(report["rotation_signal"],ensure_ascii=False),json.dumps(report["virtual_actions"],ensure_ascii=False),json.dumps(report["virtual_positions"],ensure_ascii=False),report["total_asset"],report["floating_pnl"],report["max_drawdown"],"是" if report["risk_triggered"] else "否")
    with open(mp,"w",encoding="utf-8") as h: h.write(text)
    return report
if __name__ == "__main__": generate_daily_review()
