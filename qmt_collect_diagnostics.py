# -*- coding: utf-8 -*-
"""Create a read-only, redacted diagnostic bundle for support."""
from __future__ import print_function
import datetime
import glob
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
SECRET_RE = re.compile(r"(?i)(api[_-]?key|token|secret|authorization|account[_-]?id|account)" )
KEY_VALUE_RE = re.compile(r"(?i)(api[_-]?key|token|secret|authorization)\s*[:=]\s*([^\s,}\]]+)")


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (IOError, OSError, ValueError, TypeError):
        return {} if default is None else default


def _mask(value):
    text = str(value)
    return text[:2] + "***" + text[-2:] if len(text) >= 4 else "***"


def redact(value, key=""):
    """Recursively redact credentials and account identifiers."""
    if isinstance(value, dict):
        return {k: redact(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, key) for v in value]
    if SECRET_RE.search(str(key)):
        return _mask(value)
    if isinstance(value, str):
        return KEY_VALUE_RE.sub(lambda m: m.group(1) + "=***", value)
    return value


def _git(*args):
    try:
        return subprocess.check_output(["git"] + list(args), cwd=ROOT, stderr=subprocess.STDOUT).decode("utf-8", "replace").strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def collect_git():
    status = _git("status", "--short")
    return {"branch": _git("rev-parse", "--abbrev-ref", "HEAD"), "head": _git("rev-parse", "HEAD"),
            "origin_main": _git("rev-parse", "origin/main"), "has_uncommitted_changes": bool(status),
            "status_short": status.splitlines(), "recent_commits": _git("log", "-5", "--oneline").splitlines()}


def collect_config():
    path = os.path.join(ROOT, "config.json")
    raw = _read_json(path, {})
    wanted = ["live_trading_enabled", "allowed_stocks", "qmt_python_exe", "qmt_userdata_path",
              "max_single_order_value", "max_order_amount", "account_id"]
    result = {"exists": os.path.exists(path)}
    for key in wanted:
        result[key] = raw.get(key)
    result["path_config"] = {k: v for k, v in raw.items() if "path" in k.lower() or k.lower().endswith("_dir")}
    return redact(result)


def _latest(pattern):
    paths = glob.glob(os.path.join(ROOT, pattern))
    return max(paths, key=os.path.getmtime) if paths else None


def _modified_at(path):
    if not os.path.exists(path):
        return None
    return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%dT%H:%M:%S")


def _stock_code(payload):
    if not isinstance(payload, dict):
        return None
    value = payload.get("selected_etf") or payload.get("stock_code") or payload.get("code")
    if value:
        return value
    selected = payload.get("selected") or []
    if isinstance(selected, list) and selected and isinstance(selected[0], dict):
        return selected[0].get("stock_code") or selected[0].get("code")
    return None


def collect_update_checks():
    result = {k: "未知" for k in ["code_pull", "config_check", "unit_tests", "python_compile", "safety_scan"]}
    log_path = _latest("logs/*update*.log") or _latest("logs/*update*.txt")
    result["source_log"] = os.path.relpath(log_path, ROOT) if log_path else None
    if log_path:
        try:
            with open(log_path, "r", encoding="utf-8") as handle:
                text = handle.read().lower()
        except IOError:
            text = ""
        labels = {"code_pull": ["git pull", "代码拉取"], "config_check": ["config", "配置检查"],
                  "unit_tests": ["unittest", "单元测试"], "python_compile": ["compile", "python 编译"],
                  "safety_scan": ["safety", "安全扫描"]}
        for key, terms in labels.items():
            lines = [line for line in text.splitlines() if any(term in line for term in terms)]
            if any(re.search(r"fail|error|失败", line) for line in lines): result[key] = "失败"
            elif any(re.search(r"pass|success|ok|通过", line) for line in lines): result[key] = "通过"
    backup = _latest("*backup*") or _latest("backups/*")
    result["latest_backup"] = os.path.relpath(backup, ROOT) if backup else None
    return result


def collect_etf():
    names = ["market_regime", "etf_scores", "selected_etf", "target_signal", "order_plan"]
    paths = {n: os.path.join(ROOT, "signals", n + ".json") for n in names}
    data = {n: _read_json(paths[n], {}) for n in names}
    shadow_paths = {"snapshot": os.path.join(ROOT, "shadow", "daily_snapshot.json"),
                    "portfolio": os.path.join(ROOT, "shadow", "portfolio.json")}
    snapshot = _read_json(shadow_paths["snapshot"], {})
    portfolio = _read_json(shadow_paths["portfolio"], {})
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    trades = snapshot.get("today_trades", []) if isinstance(snapshot, dict) else []
    if not trades and isinstance(portfolio, dict):
        trades = [trade for trade in portfolio.get("trades", []) if trade.get("trade_date") == today]
    shadow_trade = trades[-1] if trades else {}
    selected_code = _stock_code(data["selected_etf"])
    target_code = _stock_code(data["target_signal"])
    plan_code = _stock_code(data["order_plan"])
    trade_code = _stock_code(shadow_trade)
    codes = [code for code in [selected_code, target_code, plan_code, trade_code] if code]
    mismatch = len(set(codes)) > 1
    shadow_exists = bool(snapshot or portfolio)
    signal = data["target_signal"].get("signal_type", data["target_signal"].get("signal"))
    action = data["order_plan"].get("action", data["order_plan"].get("planned_action"))
    exists = any(bool(v) for v in data.values())
    result = {"files_found": [n + ".json" for n, v in data.items() if v], "dry_run_passed": exists and not any(bool(v.get("error")) for v in data.values()),
        "strategy_source": "etf_rotation" if shadow_exists else ("ma_daily" if data["target_signal"] or data["order_plan"] else "unknown"),
        "market_regime": data["market_regime"].get("market_regime", data["market_regime"].get("regime")),
        "selected_etf": selected_code, "signal_type": signal, "planned_action": action,
        "planned_value": data["order_plan"].get("planned_value", data["order_plan"].get("order_value")),
        "planned_amount": data["order_plan"].get("planned_amount", data["order_plan"].get("order_amount", data["order_plan"].get("plan_volume"))),
        "no_action": signal == "NO_ACTION" or action == "NO_ACTION",
        "risk_warnings": data["order_plan"].get("risk_warnings", data["order_plan"].get("warnings", [])),
        "signal_file_updated_at": _modified_at(paths["target_signal"]),
        "order_plan_updated_at": _modified_at(paths["order_plan"]),
        "shadow_updated_at": max([value for value in [_modified_at(shadow_paths["snapshot"]), _modified_at(shadow_paths["portfolio"])] if value] or [None])}
    if mismatch:
        result["mismatch_details"] = {"selected_etf_code": selected_code, "target_signal_code": target_code,
                                      "order_plan_code": plan_code, "shadow_trade_code": trade_code}
    if plan_code and trade_code and plan_code != trade_code:
        result["warning"] = "order_plan 与 shadow 成交标的不一致"
    return redact(result)


def collect_ai_api():
    report_path = os.path.join(ROOT, "logs", "ai_api_report.json")
    try:
        report = {}
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as handle:
                report_text = handle.read().strip()
            report = json.loads(report_text) if report_text else {}
        if not isinstance(report, (dict, list)):
            report = {}
        calls_path = os.path.join(ROOT, "logs", "ai_api_calls.jsonl")
        calls = []
        try:
            with open(calls_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        item = json.loads(line)
                        if isinstance(item, dict): calls.append(item)
                    except (ValueError, TypeError):
                        pass
        except (IOError, OSError):
            pass
        errors = {k: 0 for k in ["401", "403", "429", "5xx", "timeout"]}
        durations, providers = [], {}
        success = 0
        for call in calls:
            text = json.dumps(call).lower()
            for key in ["401", "403", "429", "timeout"]: errors[key] += int(key in text)
            errors["5xx"] += int(bool(re.search(r"\b5\d\d\b", text)))
            success += int(call.get("success") is True or str(call.get("status", "")).lower() == "success")
            duration = call.get("duration_ms", call.get("latency_ms"))
            if isinstance(duration, (int, float)): durations.append(duration)
            name = "%s/%s" % (call.get("provider", "unknown"), call.get("model", "unknown"))
            providers.setdefault(name, {"calls": 0, "success": 0}); providers[name]["calls"] += 1; providers[name]["success"] += int(call.get("success") is True)
        for value in providers.values(): value["success_rate"] = round(float(value["success"]) / value["calls"], 4) if value["calls"] else None
        if isinstance(report, list):
            report_providers = [{"provider": item.get("provider", "未知"), "model": item.get("model", "未知"),
                "calls": item.get("calls"), "success_rate": item.get("success_rate"),
                "average_duration_ms": item.get("average_duration_ms", item.get("avg_duration_ms", item.get("avg_duration")))}
                for item in report if isinstance(item, dict)]
            report_average = None
        else:
            report_providers = report.get("provider_model", report.get("providers", {}))
            report_average = report.get("average_duration_ms")
        return redact({"status": "ok", "report_exists": os.path.exists(report_path), "total_calls": len(calls),
            "success_rate": round(float(success) / len(calls), 4) if calls else None,
            "provider_model": providers or report_providers, "errors": errors,
            "average_duration_ms": round(sum(durations) / float(len(durations)), 2) if durations else report_average})
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def collect_ai_research():
    paths = {"analysis": "backtest_results/ai-analysis.json", "backtest_best": "backtest_results/best-result.json", "runs_best": "runs/best-result.json"}
    data = {k: _read_json(os.path.join(ROOT, v), {}) for k, v in paths.items()}
    strategy = _latest("strategies/ai_strategy_*.py"); summary = _latest("logs/ai_research_pipeline_*_summary.json")
    summary_data = _read_json(summary, {}) if summary else {}
    def ok(obj): return bool(obj) and not bool(obj.get("error")) and obj.get("success", True) is not False
    return redact({"analysis_success": ok(data["analysis"]), "latest_strategy": os.path.relpath(strategy, ROOT) if strategy else None,
                   "optimization_success": ok(data["backtest_best"]), "iteration_success": ok(data["runs_best"]),
                   "pipeline_success": ok(summary_data), "latest_pipeline_summary": os.path.relpath(summary, ROOT) if summary else None})


def _file_list(pattern, limit=10):
    paths = [p for p in glob.glob(os.path.join(ROOT, pattern)) if os.path.isfile(p)]
    paths.sort(key=os.path.getmtime, reverse=True)
    return [{"name": os.path.relpath(p, ROOT), "modified_at": datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%dT%H:%M:%S"), "size_bytes": os.path.getsize(p)} for p in paths[:limit]]


def collect_recent_files():
    return {"logs": _file_list("logs/*.log"), "summaries": _file_list("logs/*summary*.json"),
            "backtest_results": _file_list("backtest_results/*.json"), "runs": _file_list("runs/**/*"),
            "reports": _file_list("reports/daily_report_*")}


def collect_shadow():
    portfolio = _read_json(os.path.join(ROOT, "shadow", "portfolio.json"), {})
    snapshot = _read_json(os.path.join(ROOT, "shadow", "daily_snapshot.json"), {})
    curve = os.path.join(ROOT, "shadow", "equity_curve.csv")
    days = 0
    if os.path.exists(curve):
        try:
            with open(curve, "r", encoding="utf-8") as handle:
                days = max(0, len([line for line in handle if line.strip()]) - 1)
        except IOError:
            pass
    return redact({"started": bool(portfolio or snapshot or days), "running_days": days,
                   "portfolio": portfolio, "daily_snapshot": snapshot,
                   "equity_curve_exists": os.path.exists(curve), "latest_reports": _file_list("reports/daily_report_*", 2)})


def determine_stage(config, updates, etf, ai, shadow=None):
    if any(updates[k] == "失败" for k in ["code_pull", "unit_tests", "safety_scan"]): return "基础修复", False, "先修复更新、测试或安全扫描失败项"
    if not etf["dry_run_passed"]: return "ETF dry-run 修复", False, "运行并修复 ETF dry-run"
    if not ai["pipeline_success"]: return "AI 研究链路修复", False, "运行并修复 AI research pipeline"
    shadow = shadow or collect_shadow()
    if not shadow.get("started"): return "准备进入 ETF 影子盘", True, "开始 ETF 影子盘并持续观察至少 2 周"
    if shadow.get("running_days", 0) < 14: return "ETF 影子盘观察期", False, "继续影子盘观察至连续运行满 2 周"
    return "ETF 影子盘观察完成", True, "复核风险后决定下一步；诊断器不会执行交易"


def build_report():
    errors = []
    defaults = {"config": {}, "update_checks": {k: "未知" for k in ["code_pull", "unit_tests", "safety_scan"]},
                "etf_rotation": {"dry_run_passed": False}, "ai_research": {"pipeline_success": False}}
    collectors = [("config", collect_config), ("update_checks", collect_update_checks), ("etf_rotation", collect_etf),
                  ("ai_research", collect_ai_research), ("git", collect_git), ("ai_api", collect_ai_api), ("shadow", collect_shadow), ("recent_files", collect_recent_files)]
    values = {}
    for name, collector in collectors:
        try:
            values[name] = collector()
            if isinstance(values[name], dict) and values[name].get("status") == "error":
                errors.append({"collector": name, "error": values[name].get("error", "未知错误")})
        except Exception as exc:
            errors.append({"collector": name, "error": str(exc)})
            values[name] = defaults.get(name, {"status": "error", "error": str(exc)})
    config, updates, etf, ai = values["config"], values["update_checks"], values["etf_rotation"], values["ai_research"]
    try: stage, can_continue, recommendation = determine_stage(config, updates, etf, ai, values["shadow"])
    except Exception as exc:
        errors.append({"collector": "determine_stage", "error": str(exc)}); stage, can_continue, recommendation = "诊断收集失败", False, "查看 errors 字段"
    live = config.get("live_trading_enabled") is True
    return redact(dict({"generated_at": _now(), "stage": stage, "can_continue": can_continue, "next_recommendation": recommendation,
        "risks": (["live_trading_enabled=true：存在实盘风险"] if live else ["live_trading_enabled=false：不会实盘下单"]),
        "redactions_applied": ["API keys/tokens/secrets", "account_id/account identifiers"], "errors": errors}, **values))


def render_markdown(r):
    def block(value): return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"
    return """# QMT AI Trading Diagnostic Report

## 1. 总体结论
- 当前阶段：{stage}
- 是否可进入下一步：{go}
- 下一步建议：{next}
- 是否存在实盘风险：{risk}

## 2. Git / 更新状态
{git}
{updates}

## 3. 配置与安全状态
{config}

## 4. ETF 轮动 / Dry-run 状态
{etf}

## 5. AI 研究流水线状态
{ai}

## 6. AI API 稳定性
{api}

## 7. 最近产物文件
{files}

## 8. 需要发给 ChatGPT 的重点
- 请优先分析当前阶段、失败检查、风险警告和下一步建议。
- 报告已脱敏；诊断器只读，不执行交易。
""".format(stage=r["stage"], go="是" if r["can_continue"] else "否", next=r["next_recommendation"], risk="；".join(r["risks"]), git=block(r["git"]), updates=block(r["update_checks"]), config=block(r["config"]), etf=block(r["etf_rotation"]), ai=block(r["ai_research"]), api=block(r["ai_api"]), files=block(r["recent_files"]))


def main():
    report = build_report(); logs = os.path.join(ROOT, "logs")
    if not os.path.isdir(logs): os.makedirs(logs)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for name in ["assistant_diagnostic_latest", "assistant_diagnostic_" + stamp]:
        with open(os.path.join(logs, name + ".json"), "w", encoding="utf-8") as handle: json.dump(report, handle, ensure_ascii=False, indent=2)
        with open(os.path.join(logs, name + ".md"), "w", encoding="utf-8") as handle: handle.write(render_markdown(report))
    print("[OK] 诊断报告已生成")
    print("logs/assistant_diagnostic_latest.md")
    print("logs/assistant_diagnostic_latest.json")
    return report

if __name__ == "__main__": main()
