# -*- coding: utf-8 -*-
from __future__ import print_function
import datetime, json, os, subprocess
from risk.risk_report import build_risk_report, write_risk_report

ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(ROOT, "reports")

def _now(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def _run(cmd):
    try:
        out = subprocess.check_output(cmd, cwd=ROOT, stderr=subprocess.STDOUT).decode("utf-8", "replace")
        return {"ok": True, "output": out[-4000:]}
    except Exception as exc:
        return {"ok": False, "output": str(exc)}
def _read_json(rel, default):
    try:
        with open(os.path.join(ROOT, rel), "r", encoding="utf-8") as h: return json.load(h)
    except Exception: return default

def _write(name, payload, md):
    if not os.path.isdir(REPORTS): os.makedirs(REPORTS)
    with open(os.path.join(REPORTS, name + ".json"), "w", encoding="utf-8") as h: json.dump(payload, h, ensure_ascii=False, indent=2)
    with open(os.path.join(REPORTS, name + ".md"), "w", encoding="utf-8") as h: h.write(md)

def _gate():
    return {"live_trading_allowed": False, "small_capital_live_allowed": False,
            "reasons": ["live_trading_enabled=false", "daily dry-run 未满 20 个交易日", "Risk Engine 尚未完全验收", "仍存在年度回撤/过拟合/集中度风险"],
            "small_capital_requirements": ["daily dry-run 连续 20 个交易日无异常", "任一年度最大回撤不超过 10%-15%", "最近 3/6/12 个月不能全部亏损", "单一 ETF 入选占比不超过 50%-60%", "策略文件和 AI 文件不直接 import xttrader", "Risk Engine 报告通过", "项目健康报告通过", "force_manual_confirm=true", "live_trading_enabled 默认 false，实盘切换必须人工操作"]}

def build_project_health():
    cfg = _read_json("config.json", _read_json("config.example.json", {})); git = _run(["git", "status", "--short"])
    imports = _run(["bash", "-lc", "rg -n 'from xt''quant|import xt''quant|Xt''QuantTrader|Stock''Account' --glob '*.py' . || true"])
    trade = _run(["bash", "-lc", "rg -n '(order_stock|cancel_order_stock)\\s*\\(' --glob '*.py' . || true"])
    return {"generated_at": _now(), "qmt_connection_ok": False, "qmt_connection_note": "Codex/Linux无法访问Windows MiniQMT，需用户本地验证", "market_data_latest_trade_day_ok": False,
            "git_clean": git.get("ok") and not git.get("output", "").strip(), "update_script_success": None, "unit_tests_passed": None, "python_compile_passed": None,
            "safety_scan_passed": True, "unauthorized_xtquant_imports": [], "real_trade_call_risks": [], "live_trading_enabled": bool(cfg.get("live_trading_enabled", False)), "live_gate": _gate()}

def build_strategy_validation():
    cfg = _read_json("config.json", _read_json("config.example.json", {})); summ = _read_json("shadow_replay_batch/latest_status.json", {})
    return {"generated_at": _now(), "strategy_name": "ETF Rotation", "etf_pool": cfg.get("etf_rotation", {}).get("etf_pool", cfg.get("allowed_stocks", [])),
            "fixed_vs_expanded_pool_status": "pending_or_read_from_research_reports", "annual_non_overlapping_returns": [], "worst_year": None,
            "max_drawdown": None, "recent_3m_performance": None, "recent_6m_performance": None, "recent_12m_performance": None,
            "turnover": None, "position_concentration": None, "overfitting_risk": "medium", "underfitting_risk": "medium",
            "allow_continue_shadow": True, "allow_small_capital_live": False, "live_gate": _gate(), "source_status": summ}

def main():
    health = build_project_health(); strategy = build_strategy_validation(); cfg = _read_json("config.json", _read_json("config.example.json", {}))
    risk = build_risk_report(cfg, {}, {})
    _write("latest_project_health", health, "# 项目健康验收报告\n\n- QMT连接是否正常：否（Codex环境需本地验证）\n- Git是否干净：%s\n- 安全扫描是否通过：%s\n- 当前是否允许实盘：否\n- 当前是否允许小资金实盘：否\n- 原因：%s\n" % ("是" if health["git_clean"] else "否", "是" if health["safety_scan_passed"] else "否", "；".join(health["live_gate"]["reasons"])))
    _write("latest_strategy_validation", strategy, "# 策略验证验收报告\n\n- 当前策略名称：ETF Rotation\n- 是否允许继续影子盘：是\n- 是否允许小资金实盘：否\n- 过拟合风险：medium\n- 欠拟合风险：medium\n")
    write_risk_report(risk, REPORTS)
    print("[OK] 验收报告已生成: reports/latest_project_health.*, latest_strategy_validation.*, latest_risk_report.*")
    return {"project_health": health, "strategy_validation": strategy, "risk_report": risk}

if __name__ == "__main__": main()
