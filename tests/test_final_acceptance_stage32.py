from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.acceptance.formatters import FINAL_ACCEPTANCE_SAFETY_NOTE, format_acceptance_report_markdown
from qmt_ai_trading.acceptance.models import AcceptanceCheck, AcceptanceDecision, AcceptanceReport
from qmt_ai_trading.acceptance.safety import check_forbidden_live_flags, validate_acceptance_is_dry_run
from qmt_ai_trading.acceptance.service import run_final_acceptance_check

ROOT = Path(__file__).resolve().parents[1]

def test_acceptance_models_instantiable():
    c = AcceptanceCheck("id", "title", AcceptanceDecision.PASS, "ok")
    r = AcceptanceReport("rid", "now", AcceptanceDecision.PASS, [c], {}, FINAL_ACCEPTANCE_SAFETY_NOTE, True, "ok")
    assert c.check_id == "id" and r.success

def test_dry_run_validation_and_forbidden_flags():
    assert validate_acceptance_is_dry_run()[0]
    assert not check_forbidden_live_flags("py script.py --live-enabled")[0]
    assert "--live-enabled" in check_forbidden_live_flags("py script.py --live-enabled")[1]
    assert not check_forbidden_live_flags("import xttrader")[0]
    assert "xttrader" in check_forbidden_live_flags("import xttrader")[1]

def test_run_final_acceptance_and_format():
    report = run_final_acceptance_check(ROOT)
    md = format_acceptance_report_markdown(report)
    assert "Final acceptance decision" in md
    assert FINAL_ACCEPTANCE_SAFETY_NOTE in md

def test_run_final_acceptance_cli_generates_outputs(tmp_path):
    md = tmp_path / "final.acceptance.md"; js = tmp_path / "final.acceptance.json"
    p = subprocess.run([sys.executable, "scripts/run_final_acceptance.py", "--output", str(md), "--json-output", str(js)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert p.returncode == 0, p.stderr
    assert FINAL_ACCEPTANCE_SAFETY_NOTE in md.read_text(encoding="utf-8")
    assert json.loads(js.read_text(encoding="utf-8"))["safety_note"] == FINAL_ACCEPTANCE_SAFETY_NOTE

def test_full_dry_run_smoke_generates_summary(tmp_path):
    out = tmp_path / "smoke"; cache = tmp_path / "cache"
    p = subprocess.run([sys.executable, "scripts/run_full_dry_run_smoke.py", "--cache-root", str(cache), "--output-dir", str(out)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert p.returncode == 0, p.stderr
    summary = (out / "smoke_summary.md").read_text(encoding="utf-8")
    assert "Stage 32 Full Dry Run Smoke Summary" in summary
    assert "--live-enabled" not in summary

def test_stage32_docs_and_roadmap():
    assert (ROOT / "docs/runbook-overview.md").exists()
    assert (ROOT / "docs/final-acceptance-checklist.md").exists()
    roadmap = (ROOT / "docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段三十二：运行手册 / 部署手册 / 总体验收" in roadmap
    assert "项目总体验收完成 / 后续增强待定" in roadmap

def test_sync_all_not_modified():
    path = ROOT / "scripts/sync_all.ps1"
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    p = subprocess.run(["git", "diff", "--", "scripts/sync_all.ps1"], cwd=ROOT, text=True, capture_output=True, check=False)
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    assert before == after
    assert p.stdout.strip() == ""
