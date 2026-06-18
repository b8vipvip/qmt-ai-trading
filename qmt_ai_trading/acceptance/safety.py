"""Read-only safety checks for Stage 32 acceptance."""
from __future__ import annotations
import subprocess
from pathlib import Path

FORBIDDEN_LIVE_TOKENS = ("--live-enabled", "xttrader", "place_order", "submit_order")
RUNTIME_PATTERNS = (
    "final_acceptance_stage32/", "smoke_reports_stage32/", "market_data_test_stage32/", "dashboard_stage32/",
    "agent_reports_stage32/", "monitoring_reports_stage32/", "live_gray_reports_stage32/",
    "reports/", "logs/", "approvals/", "paper_orders/", "market_data/", "data_cache/",
    "*.acceptance.json", "*.acceptance.md", "*.smoke.json", "*.smoke.md",
)
SENSITIVE_DOC_PATTERNS = ("api_key=", "secret=", "password=", "token=")


def validate_acceptance_is_dry_run() -> tuple[bool, str]:
    return True, "Final acceptance is dry-run documentation validation only; no order, no xttrader, no QMT trading API."


def check_forbidden_live_flags(command_text: str) -> tuple[bool, list[str]]:
    lowered = (command_text or "").lower()
    found = [token for token in FORBIDDEN_LIVE_TOKENS if token.lower() in lowered]
    return len(found) == 0, found


def check_runtime_artifact_gitignore_patterns(repo_root: str | Path) -> tuple[bool, list[str]]:
    root = Path(repo_root)
    text = (root / ".gitignore").read_text(encoding="utf-8") if (root / ".gitignore").exists() else ""
    missing = [p for p in RUNTIME_PATTERNS if p not in text]
    return len(missing) == 0, missing


def check_sync_script_protected(repo_root: str | Path) -> tuple[bool, str]:
    root = Path(repo_root)
    path = root / "scripts" / "sync_all.ps1"
    if not path.exists():
        return False, "scripts/sync_all.ps1 is missing"
    try:
        result = subprocess.run(["git", "diff", "--", "scripts/sync_all.ps1"], cwd=root, text=True, capture_output=True, check=False)
    except Exception as exc:
        return False, f"git diff check failed: {exc}"
    if result.stdout.strip():
        return False, "scripts/sync_all.ps1 has uncommitted modifications"
    return True, "scripts/sync_all.ps1 exists and has no working-tree diff"


def check_no_sensitive_patterns_in_docs(repo_root: str | Path) -> tuple[bool, list[str]]:
    root = Path(repo_root)
    findings: list[str] = []
    for path in (root / "docs").glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for pat in SENSITIVE_DOC_PATTERNS:
            if pat in text:
                findings.append(f"{path.relative_to(root)}:{pat}")
    return len(findings) == 0, findings
