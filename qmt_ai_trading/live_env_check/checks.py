from __future__ import annotations

import subprocess
from pathlib import Path
from .models import LiveEnvCheckConfig, LiveEnvCheckDecision, LiveEnvCheckItem, LiveEnvCheckScope as S, LiveEnvCheckStatus as St
from .safety import contains_forbidden_live_env_action

def _item(cid, scope, status, title, msg="", evidence=None, remediation="", metadata=None): return LiveEnvCheckItem(cid, scope, status, title, msg, list(evidence or []), remediation, dict(metadata or {}))
def _read(text=None, path=None):
    if text is not None: return text, ["inline text"]
    if not path: return "", []
    p=Path(path)
    if not p.exists(): return "", [f"missing: {p}"]
    if any(x in p.name.lower() for x in (".env","token","key","password","secret")): return "", [f"sensitive path not read: {p}"]
    return p.read_text(encoding="utf-8", errors="replace"), [str(p)]

def check_project_files(repo_root):
    root=Path(repo_root); req=["qmt_ai_trading","scripts/run_daily_pipeline.py","scripts/register_daily_pipeline_task.py","docs/qmt-ai-trading-project-roadmap.md","docs/qmt-ai-trading-architecture.md"]
    missing=[x for x in req if not (root/x).exists()]
    return _item("project_files", S.FILES, St.FAIL if missing else St.PASS, "Core project files exist", "Missing files: "+", ".join(missing) if missing else "Core scripts and docs are present.", req, "Restore missing core files.")

def check_gitignore_runtime_patterns(repo_root):
    patterns=["live_env_check/","live_env_check_stage38/","reports/","logs/","approvals/","paper_orders/","market_data/","data_cache/","*.live_env_check.json","*.live_env_check.md"]
    p=Path(repo_root)/".gitignore"; txt=p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""; missing=[x for x in patterns if x not in txt]
    return _item("gitignore_runtime_patterns", S.GIT, St.FAIL if missing else St.PASS, ".gitignore covers runtime artifacts", "Missing patterns: "+", ".join(missing) if missing else "Runtime artifact patterns are ignored.", [str(p)], "Add missing runtime artifact patterns.")

def check_sync_script_protected(repo_root):
    p=Path(repo_root)/"scripts/sync_all.ps1"
    status=St.PASS if p.exists() else St.FAIL
    msg="sync_all.ps1 exists and was not read or modified by this check." if p.exists() else "scripts/sync_all.ps1 missing."
    return _item("sync_script_protected", S.GIT, status, "sync_all.ps1 protected", msg, [str(p)], "Restore protected sync script.")

def check_no_sensitive_files(repo_root):
    root=Path(repo_root); bad=[]
    for p in root.iterdir():
        n=p.name.lower()
        if n==".env" or any(x in n for x in ("token","password","secret")): bad.append(p.name)
    return _item("no_sensitive_files", S.SECURITY, St.FAIL if bad else St.PASS, "No obvious sensitive files at repo root", "Potential sensitive files: "+", ".join(bad) if bad else "No obvious sensitive files found at repo root; file contents were not read.", bad, "Move secrets outside repo and keep .env untracked.")

def check_scheduler_preview_text(text):
    bad=contains_forbidden_live_env_action(text or "") or "--live-enabled" in (text or "") or "--execute-live" in (text or "") or "real-send" in (text or "")
    return _item("scheduler_preview_text", S.SCHEDULER, St.FAIL if bad else St.PASS, "Scheduler preview stays dry-run", "Forbidden scheduler live/real-send flag detected." if bad else "Scheduler preview contains no --live-enabled, --execute-live, or real-send.", ["scheduler preview text"], "Remove live execution flags.")

def check_live_flags_absent(text):
    bad=contains_forbidden_live_env_action(text or "")
    return _item("live_flags_absent", S.SECURITY, St.FAIL if bad else St.PASS, "Forbidden live flags absent", "Forbidden live action marker detected." if bad else "No forbidden live execution markers detected.")

def check_capital_config(config):
    fail=config.max_total_capital is None or config.max_single_order_value is None
    warn=(not fail) and (float(config.max_total_capital)>10000 or float(config.max_single_order_value)>2000)
    return _item("capital_config", S.CONFIG, St.FAIL if fail else (St.WARN if warn else St.PASS), "Tiny-capital limits are explicit", "Capital limits missing." if fail else f"max_total_capital={config.max_total_capital}, max_single_order_value={config.max_single_order_value}", remediation="Set explicit tiny capital limits.")

def check_allowed_symbols(config):
    ok=bool(config.allowed_symbols)
    return _item("allowed_symbols", S.CONFIG, St.PASS if ok else St.FAIL, "Allowed symbol whitelist is non-empty", f"allowed_symbols={config.allowed_symbols}" if ok else "Allowed symbol whitelist is empty.", remediation="Provide explicit allowed symbols.")

def _evidence_check(cid, scope, title, text=None, path=None, must=()):
    body, ev = _read(text, path); missing = not body.strip(); forbidden=contains_forbidden_live_env_action(body)
    status = St.FAIL if forbidden else (St.WARN if missing else St.PASS)
    msg = "Forbidden live marker detected." if forbidden else ("Evidence missing." if missing else "Read-only evidence available.")
    return _item(cid, scope, status, title, msg, ev, "Provide local read-only evidence report.")

def check_dashboard_read_only(text=None, path=None): return _evidence_check("dashboard_read_only", S.DASHBOARD, "Dashboard is read-only with no order entry", text, path)
def check_notification_dry_run(text=None, path=None): return _evidence_check("notification_dry_run", S.NOTIFICATION, "Notification remains dry-run", text, path)
def check_data_quality_read_only(text=None, path=None): return _evidence_check("data_quality_read_only", S.DATA_QUALITY, "Data Quality Tracking is read-only", text, path)
def check_agent_read_only(text=None, path=None): return _evidence_check("agent_read_only", S.AGENT, "Agent Research is read-only", text, path)
def check_live_manual_prep_evidence(text=None, path=None): return _evidence_check("live_manual_prep_evidence", S.LIVE_MANUAL_PREP, "Live Manual Prep evidence is available", text, path)
def check_risk_approval_paper_chain(text=None, path=None): return _evidence_check("risk_approval_paper_chain", S.RISK, "Risk / Approval / Paper safety chain exists", text, path)

def aggregate_live_env_checks(checks, config):
    critical={S.SECURITY.value,S.SCHEDULER.value,S.CONFIG.value,S.RISK.value,S.SECURITY,S.SCHEDULER,S.CONFIG,S.RISK}
    fails=[c for c in checks if str(c.status)==St.FAIL.value]
    blockers=[c for c in fails if c.scope in critical or str(c.scope) in critical]
    missing=[c for c in checks if str(c.status)==St.WARN.value]
    if blockers: return LiveEnvCheckDecision.BLOCKED, [f"{c.check_id}: {c.message}" for c in blockers], [c.message for c in missing]
    if fails or missing: return LiveEnvCheckDecision.NEED_MORE_EVIDENCE, [], [c.message for c in missing+fails]
    return LiveEnvCheckDecision.READY_FOR_ENV_REVIEW, [], []
