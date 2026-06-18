from __future__ import annotations
import subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_manual_prep.models import LiveManualPrepConfig, LiveManualPrepPackage, LiveManualPrepDecision, SAFETY_NOTE
from qmt_ai_trading.live_manual_prep.safety import contains_forbidden_live_manual_action
from qmt_ai_trading.live_manual_prep.evidence import collect_live_manual_evidence_from_file
from qmt_ai_trading.live_manual_prep.service import run_live_manual_prep_package
from qmt_ai_trading.live_manual_prep.formatters import format_live_manual_prep_package_markdown
from qmt_ai_trading.live_manual_prep.models import LiveManualPrepEvidenceStatus, LiveManualPrepEvidenceType
from qmt_ai_trading.dashboard.collector import collect_live_manual_prep_section
from qmt_ai_trading.dashboard.models import DashboardConfig, DashboardStatus

def test_models_instantiable():
    assert LiveManualPrepConfig().max_total_capital == 5000.0
    assert LiveManualPrepPackage().safety_note == SAFETY_NOTE

def test_safety_forbidden_terms():
    for text in ["--live-enabled", "--execute-live", "xttrader", "submit_order", "place_order", "real_send", "requests.post", "smtp", "sendMessage", "webhook", "查询资金", "查询持仓", "查询订单", "查询成交"]:
        assert contains_forbidden_live_manual_action(text)

def test_collect_missing_and_blocker(tmp_path):
    ev = collect_live_manual_evidence_from_file(tmp_path / "missing.md", LiveManualPrepEvidenceType.SYSTEM)
    assert ev.status == LiveManualPrepEvidenceStatus.MISSING
    p = tmp_path / "bad.md"; p.write_text("xttrader submit_order live enabled", encoding="utf-8")
    ev2 = collect_live_manual_evidence_from_file(p, LiveManualPrepEvidenceType.SYSTEM)
    assert ev2.status == LiveManualPrepEvidenceStatus.FAIL

def test_run_no_input_and_markdown():
    pkg = run_live_manual_prep_package()
    assert pkg.decision in {LiveManualPrepDecision.NEED_MORE_EVIDENCE, LiveManualPrepDecision.NOT_READY}
    assert "preparation-only" in format_live_manual_prep_package_markdown(pkg)

def test_cli_generates_outputs(tmp_path):
    md = tmp_path / "live_manual_prep.md"; js = tmp_path / "live_manual_prep.json"
    r = subprocess.run([sys.executable, "scripts/run_live_manual_prep.py", "--output", str(md), "--json-output", str(js), "--allowed-symbols", "510300.SH,510500.SH", "--max-total-capital", "5000", "--max-single-order-value", "1000"], cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True)
    assert r.returncode == 0, r.stderr
    assert md.exists() and js.exists()
    assert "Live manual approval prep summary" in md.read_text(encoding="utf-8")

def test_dashboard_live_manual_prep_section(tmp_path):
    (tmp_path / "x.live_manual_prep.md").write_text("read-only live manual prep", encoding="utf-8")
    sec = collect_live_manual_prep_section(DashboardConfig(include_live_manual_prep=True, live_manual_prep_dir=str(tmp_path)))
    assert sec.status == DashboardStatus.OK

def test_gitignore_and_docs_contain_stage37():
    root = Path(__file__).resolve().parents[1]
    assert "live_manual_prep_stage37/" in (root / ".gitignore").read_text(encoding="utf-8")
    roadmap = (root / "docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段三十七：极小资金灰度实盘人工审批准备" in roadmap
    assert "阶段三十八：极小资金灰度只读环境核验" in roadmap
