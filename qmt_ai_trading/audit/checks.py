"""Static live-readiness checks for Stage 23.

These checks read repository files only. They do not import QMT, xttrader, or
any trading/account/order runtime.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from .models import AuditCheckResult, AuditSeverity, AuditStatus

REQUIRED_GITIGNORE_PATTERNS = [
    "approvals/", "approval_test_stage21/", "approval_test_stage22/",
    "paper_orders/", "paper_orders_test_stage22/", "market_data/",
    "data_cache/", "reports/", "logs/", "*.approval.json",
    "*.decision.json", "*.paper_order.json", "*.paper_report.json",
]
SCAN_SUFFIXES = {".py", ".md", ".json", ".ps1"}
SKIP_NAMES = {".env"}
SENSITIVE_RULES = {
    "possible_token_assignment": ["token", "api_token", "access_token"],
    "possible_key_assignment": ["api_key", "secret_key", "private_key"],
    "possible_password_assignment": ["password", "passwd"],
}
DIRECT_ORDER_NAMES = {"place_order", "buy", "sell", "submit_order", "cancel_order"}
DIRECT_ORDER_ALLOWED_PARTS = {
    ("qmt_ai_trading", "gateway"),
    ("qmt_ai_trading", "paper"),
    ("qmt_ai_trading", "audit"),
    ("tests",),
    ("docs",),
}


def _root(project_root: str | Path) -> Path:
    return Path(project_root).resolve()


def _result(check_id: str, name: str, status: AuditStatus, severity: AuditSeverity, message: str, evidence=None, remediation: str = "", metadata=None) -> AuditCheckResult:
    return AuditCheckResult(check_id, name, status, severity, message, list(evidence or []), remediation, dict(metadata or {}))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _is_allowed(path: Path, root: Path, allowed_parts: set[tuple[str, ...]]) -> bool:
    parts = path.relative_to(root).parts
    return any(parts[: len(prefix)] == prefix for prefix in allowed_parts)


def _tracked_files(root: Path) -> list[Path]:
    try:
        cp = subprocess.run(["git", "ls-files"], cwd=root, text=True, capture_output=True, check=True)
        return [root / line for line in cp.stdout.splitlines() if line]
    except Exception:
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def _scan_files(root: Path) -> list[Path]:
    return [p for p in _tracked_files(root) if p.suffix.lower() in SCAN_SUFFIXES and p.name not in SKIP_NAMES]


def check_required_docs(project_root) -> AuditCheckResult:
    root = _root(project_root)
    required = ["docs/qmt-ai-trading-project-roadmap.md", "docs/qmt-ai-trading-architecture.md"]
    missing = [p for p in required if not (root / p).exists()]
    return _result("required_docs", "Required roadmap and architecture docs", AuditStatus.FAIL if missing else AuditStatus.PASS, AuditSeverity.ERROR if missing else AuditSeverity.INFO, "Required documents are present." if not missing else "Required documents are missing.", required if not missing else missing, "Restore the required roadmap and architecture documents.")


def check_roadmap_stage_alignment(project_root) -> AuditCheckResult:
    p = _root(project_root) / "docs/qmt-ai-trading-project-roadmap.md"
    text = _read(p) if p.exists() else ""
    required = ["阶段二十三", "实盘前安全审计", "阶段二十四", "QMT 实机数据联调与真实缓存质量验证"]
    missing = [s for s in required if s not in text]
    return _result("roadmap_stage_alignment", "Roadmap stage 23/24 alignment", AuditStatus.FAIL if missing else AuditStatus.PASS, AuditSeverity.ERROR if missing else AuditSeverity.INFO, "Roadmap contains Stage 23 and Stage 24 alignment." if not missing else "Roadmap stage alignment text is incomplete.", ["docs/qmt-ai-trading-project-roadmap.md"], "Update roadmap Stage 23 and Stage 24 descriptions.", {"missing_terms": missing})


def check_architecture_safety_rules(project_root) -> AuditCheckResult:
    p = _root(project_root) / "docs/qmt-ai-trading-architecture.md"
    text = _read(p) if p.exists() else ""
    required = ["Live Readiness Audit", "不是交易授权", "默认 NO_GO", "不调用 xttrader", "不真实下单"]
    missing = [s for s in required if s not in text]
    return _result("architecture_safety_rules", "Architecture live-readiness safety rules", AuditStatus.FAIL if missing else AuditStatus.PASS, AuditSeverity.ERROR if missing else AuditSeverity.INFO, "Architecture documents Stage 23 safety rules." if not missing else "Architecture safety rules are incomplete.", ["docs/qmt-ai-trading-architecture.md"], "Document Live Readiness Audit placement and safety rules.", {"missing_terms": missing})


def check_sync_script_protected(project_root) -> AuditCheckResult:
    root = _root(project_root); p = root / "scripts/sync_all.ps1"
    if not p.exists():
        return _result("sync_script_protected", "sync_all.ps1 protected", AuditStatus.FAIL, AuditSeverity.ERROR, "scripts/sync_all.ps1 is missing.", ["scripts/sync_all.ps1"], "Restore the protected sync script.")
    try:
        cp = subprocess.run(["git", "ls-files", "-v", "scripts/sync_all.ps1"], cwd=root, text=True, capture_output=True, check=True)
        marker = cp.stdout[:1]
        status = AuditStatus.PASS if marker else AuditStatus.WARN
        return _result("sync_script_protected", "sync_all.ps1 protected", status, AuditSeverity.INFO if status == AuditStatus.PASS else AuditSeverity.WARNING, "scripts/sync_all.ps1 exists; git tracking marker inspected." if status == AuditStatus.PASS else "scripts/sync_all.ps1 exists but git marker could not be verified.", ["scripts/sync_all.ps1", f"git marker: {marker or 'unavailable'}"], "Do not modify scripts/sync_all.ps1 in Stage 23.")
    except Exception as exc:
        return _result("sync_script_protected", "sync_all.ps1 protected", AuditStatus.WARN, AuditSeverity.WARNING, "scripts/sync_all.ps1 exists but git marker could not be read.", ["scripts/sync_all.ps1"], "Optionally inspect git skip-worktree/assume-unchanged flags manually.", {"error_type": type(exc).__name__})


def check_gitignore_runtime_dirs(project_root) -> AuditCheckResult:
    p = _root(project_root) / ".gitignore"; text = _read(p) if p.exists() else ""
    lines = {line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")}
    missing = [x for x in REQUIRED_GITIGNORE_PATTERNS if x not in lines]
    return _result("gitignore_runtime_dirs", "Runtime dirs ignored", AuditStatus.FAIL if missing else AuditStatus.PASS, AuditSeverity.ERROR if missing else AuditSeverity.INFO, ".gitignore contains required runtime patterns." if not missing else ".gitignore is missing runtime patterns.", [".gitignore"], "Add missing runtime directories and file patterns to .gitignore.", {"missing_patterns": missing})


def check_live_trading_disabled(project_root) -> AuditCheckResult:
    root = _root(project_root); p = root / "qmt_ai_trading/config/settings.py"
    text = _read(p) if p.exists() else ""
    ok = "live_trading_enabled: bool = False" in text and "LIVE_TRADING_ENABLED" in text and "False" in text
    status = AuditStatus.PASS if ok else AuditStatus.WARN
    return _result("live_trading_disabled", "Live trading disabled by default", status, AuditSeverity.INFO if ok else AuditSeverity.WARNING, "Configuration defaults live trading to disabled." if ok else "Could not conclusively prove live trading is disabled by default.", ["qmt_ai_trading/config/settings.py"], "Ensure live_trading_enabled defaults to False and requires explicit future audited enablement.")


def check_no_xttrader_import_outside_gateway(project_root) -> AuditCheckResult:
    root = _root(project_root); findings=[]
    for p in _scan_files(root):
        if _is_allowed(p, root, {("docs",), ("tests",), ("qmt_gateway",)}):
            continue
        rel = p.relative_to(root).as_posix(); text = _read(p)
        for i,line in enumerate(text.splitlines(),1):
            stripped=line.strip()
            if (stripped.startswith("import ") or stripped.startswith("from ")) and ("import xttrader" in stripped or "xtquant.xttrader" in stripped) and not stripped.startswith("#"):
                findings.append(f"{rel}:{i}")
    return _result("no_xttrader_import", "No xttrader import in current code", AuditStatus.FAIL if findings else AuditStatus.PASS, AuditSeverity.CRITICAL if findings else AuditSeverity.INFO, "No current code imports xttrader." if not findings else "Potential xttrader import detected outside allowed documentation/tests.", findings, "Remove xttrader imports until a future audited gateway phase.")


def check_no_direct_order_call_outside_gateway(project_root) -> AuditCheckResult:
    root=_root(project_root); findings=[]
    for p in [x for x in _scan_files(root) if x.suffix == ".py" and not _is_allowed(x, root, DIRECT_ORDER_ALLOWED_PARTS)]:
        try: tree=ast.parse(_read(p))
        except SyntaxError: continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
                if name in DIRECT_ORDER_NAMES:
                    findings.append(f"{p.relative_to(root).as_posix()}:{node.lineno}:{name}")
    return _result("no_direct_order_call", "No direct order calls outside gateway/paper", AuditStatus.FAIL if findings else AuditStatus.PASS, AuditSeverity.CRITICAL if findings else AuditSeverity.INFO, "No direct order calls detected outside gateway/paper/tests/docs." if not findings else "Direct order-like calls detected outside allowed boundaries.", findings, "Route any future real order behavior only through QMT Gateway after audited approval and Risk Gate.")


def check_risk_gate_exists(project_root) -> AuditCheckResult:
    root=_root(project_root); paths=["qmt_ai_trading/risk/trade_validator.py", "qmt_ai_trading/risk/live_gate.py"]
    missing=[p for p in paths if not (root/p).exists()]
    return _result("risk_gate_exists", "Risk Gate exists", AuditStatus.FAIL if missing else AuditStatus.PASS, AuditSeverity.ERROR if missing else AuditSeverity.INFO, "Risk Gate modules exist." if not missing else "Risk Gate modules are missing.", paths, "Restore Risk Gate modules.")


def check_human_approval_exists(project_root) -> AuditCheckResult:
    root=_root(project_root); paths=["qmt_ai_trading/approval/service.py", "scripts/approval_cli.py"]
    missing=[p for p in paths if not (root/p).exists()]
    return _result("human_approval_exists", "Human Approval exists", AuditStatus.FAIL if missing else AuditStatus.PASS, AuditSeverity.ERROR if missing else AuditSeverity.INFO, "Human Approval modules and CLI exist." if not missing else "Human Approval files are missing.", paths, "Restore Human Approval package and CLI.")


def check_paper_trading_exists(project_root) -> AuditCheckResult:
    root=_root(project_root); paths=["qmt_ai_trading/paper/service.py", "scripts/paper_trading_cli.py"]
    missing=[p for p in paths if not (root/p).exists()]
    return _result("paper_trading_exists", "Paper Trading exists", AuditStatus.FAIL if missing else AuditStatus.PASS, AuditSeverity.ERROR if missing else AuditSeverity.INFO, "Paper Trading modules and CLI exist." if not missing else "Paper Trading files are missing.", paths, "Restore Paper Trading package and CLI.")


def check_no_sensitive_patterns_in_tracked_files(project_root) -> AuditCheckResult:
    root=_root(project_root); findings=[]
    for p in _scan_files(root):
        rel=p.relative_to(root).as_posix()
        if p.name.startswith(".env"):
            continue
        for i,line in enumerate(_read(p).splitlines(),1):
            low=line.lower()
            for rule, words in SENSITIVE_RULES.items():
                if any(w in low for w in words) and ("=" in line or ":" in line) and not rel.startswith("qmt_ai_trading/audit/"):
                    findings.append(f"{rel}:{i}:{rule}")
    status = AuditStatus.WARN if findings else AuditStatus.PASS
    return _result("no_sensitive_patterns", "No obvious sensitive patterns in tracked files", status, AuditSeverity.WARNING if findings else AuditSeverity.INFO, "No obvious sensitive assignment patterns found." if not findings else "Potential sensitive patterns found; values intentionally omitted.", findings[:50], "Review flagged files manually; never commit secrets or runtime credentials.", {"finding_count": len(findings)})


def check_runtime_dirs_not_tracked(project_root) -> AuditCheckResult:
    root=_root(project_root); prefixes=("approvals/","paper_orders/","market_data/","data_cache/","reports/","logs/","audit_test_reports/")
    tracked=[]
    try:
        cp=subprocess.run(["git","ls-files"], cwd=root, text=True, capture_output=True, check=True)
        tracked=[line for line in cp.stdout.splitlines() if line.startswith(prefixes)]
    except Exception:
        return _result("runtime_dirs_not_tracked", "Runtime dirs not tracked", AuditStatus.WARN, AuditSeverity.WARNING, "Could not inspect tracked files.", [], "Run git ls-files manually.")
    return _result("runtime_dirs_not_tracked", "Runtime dirs not tracked", AuditStatus.FAIL if tracked else AuditStatus.PASS, AuditSeverity.ERROR if tracked else AuditSeverity.INFO, "No runtime directory files are tracked." if not tracked else "Runtime output files are tracked.", tracked, "Remove runtime outputs from git tracking.")


def check_pipeline_dry_run_report_capable(project_root) -> AuditCheckResult:
    root = _root(project_root)
    paths = ["scripts/run_daily_pipeline.py", "qmt_ai_trading/pipeline/report.py", "qmt_ai_trading/reporting/writer.py"]
    missing = [p for p in paths if not (root / p).exists()]
    return _result("pipeline_dry_run_report_capable", "Pipeline dry-run report capability exists", AuditStatus.FAIL if missing else AuditStatus.PASS, AuditSeverity.ERROR if missing else AuditSeverity.INFO, "Daily pipeline/reporting files exist for dry-run report generation." if not missing else "Pipeline/reporting files are missing.", paths, "Restore daily pipeline and reporting modules.")


def check_approval_and_paper_blocking_logic(project_root) -> AuditCheckResult:
    root = _root(project_root)
    files = [root / "qmt_ai_trading/approval/service.py", root / "qmt_ai_trading/paper/service.py"]
    text = "\n".join(_read(p) for p in files if p.exists())
    required = ["execution is blocked", "paper trading is blocked", "risk_decisions are missing", "not allowed"]
    missing = [s for s in required if s not in text]
    return _result("approval_paper_blocking_logic", "Approval and paper trading blocking logic", AuditStatus.FAIL if missing else AuditStatus.PASS, AuditSeverity.ERROR if missing else AuditSeverity.INFO, "Approval and paper trading blocking logic is present." if not missing else "Approval/paper blocking logic text is incomplete.", ["qmt_ai_trading/approval/service.py", "qmt_ai_trading/paper/service.py"], "Ensure non-approved approvals and missing/denied RiskDecision block paper/live execution.", {"missing_terms": missing})
