from __future__ import annotations
import importlib.util, subprocess, sys
from pathlib import Path
from qmt_ai_trading.final_authorization.models import FinalAuthorizationConfig, FinalAuthorizationPackage, FinalAuthorizationDecision, FinalAuthorizationEvidenceType, SAFETY_NOTE
from qmt_ai_trading.final_authorization.safety import contains_forbidden_final_authorization_action
from qmt_ai_trading.final_authorization.evidence import collect_final_authorization_evidence_from_file
from qmt_ai_trading.final_authorization.service import run_final_authorization_package
from qmt_ai_trading.final_authorization.formatters import format_final_authorization_package_markdown
from qmt_ai_trading.dashboard.collector import collect_final_authorization_section
from qmt_ai_trading.dashboard.models import DashboardConfig, DashboardStatus
ROOT=Path(__file__).resolve().parents[1]


def test_formatters_module_exists_and_importable():
    path = ROOT / "qmt_ai_trading/final_authorization/formatters.py"
    assert path.exists()
    spec = importlib.util.find_spec("qmt_ai_trading.final_authorization.formatters")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert hasattr(module, "format_final_authorization_package_markdown")

def test_models_instantiable():
    assert FinalAuthorizationConfig().max_total_capital == 5000.0
    assert FinalAuthorizationPackage().safety_note == SAFETY_NOTE

def test_safety_forbidden_terms():
    for text in ["--live-enabled", "--execute-live", "xttrader", "submit_order", "place_order", "real_send", "requests.post", "smtp", "sendMessage", "webhook", "查询资金", "查询持仓", "查询订单", "查询成交"]:
        assert contains_forbidden_final_authorization_action(text)

def test_collect_missing_and_blocker(tmp_path):
    ev=collect_final_authorization_evidence_from_file(tmp_path/"missing.md", FinalAuthorizationEvidenceType.LIVE_ENV_CHECK)
    assert getattr(ev.status,"value",ev.status) == "MISSING"
    p=tmp_path/"bad.md"; p.write_text("live_enabled=True xttrader", encoding="utf-8")
    ev=collect_final_authorization_evidence_from_file(p, FinalAuthorizationEvidenceType.LIVE_ENV_CHECK)
    assert getattr(ev.status,"value",ev.status) == "FAIL"

def test_run_no_input_and_format():
    pkg=run_final_authorization_package()
    assert getattr(pkg.decision,"value",pkg.decision) in {FinalAuthorizationDecision.NEED_MORE_EVIDENCE.value, FinalAuthorizationDecision.NOT_AUTHORIZED.value}
    md = format_final_authorization_package_markdown(pkg)
    assert "review-only and dry-run" in md
    assert "新阶段必须单独人工确认" in md
    assert "阶段四十：实盘开关隔离与最终红线复核" in md
    for marker in ["鏂", "闃", "鈥"]:
        assert marker not in md

def test_cli_generates_markdown_json(tmp_path):
    md=tmp_path/"final_authorization.md"; js=tmp_path/"final_authorization.json"
    r=subprocess.run([sys.executable, str(ROOT/"scripts/run_final_authorization_package.py"), "--output", str(md), "--json-output", str(js), "--allowed-symbols", "510300.SH,510500.SH", "--max-total-capital", "5000", "--max-single-order-value", "1000"], cwd=ROOT, text=True, capture_output=True)
    assert r.returncode == 0, r.stderr
    assert md.exists() and js.exists()
    assert "Final manual authorization package summary" in md.read_text(encoding="utf-8")

def test_dashboard_final_authorization_section(tmp_path):
    (tmp_path/"a.final_authorization.md").write_text("Final Authorization Package read-only no order entry", encoding="utf-8")
    sec=collect_final_authorization_section(DashboardConfig(include_final_authorization=True, final_authorization_dir=str(tmp_path)))
    assert sec.status == DashboardStatus.OK
    assert "read-only" in str(sec.to_dict())

def test_register_preview_final_authorization_safe():
    r=subprocess.run([sys.executable, str(ROOT/"scripts/register_daily_pipeline_task.py"), "--enable-final-authorization-package", "--final-authorization-output-dir", "final_authorization", "--final-authorization-allowed-symbols", "510300.SH,510500.SH", "--final-authorization-max-total-capital", "5000", "--final-authorization-max-single-order-value", "1000"], cwd=ROOT, text=True, capture_output=True)
    assert r.returncode == 0, r.stderr
    out=r.stdout
    assert "--enable-final-authorization-package" in out
    assert "--live-enabled" not in out and "--execute-live" not in out
    for bad in ["--live-env-check-max-port", " H ", "500ge38", "2026-06- "]:
        assert bad not in out

def test_gitignore_and_roadmap():
    gi=(ROOT/".gitignore").read_text(encoding="utf-8")
    assert "final_authorization/" in gi or "final_authorization_stage39/" in gi
    roadmap=(ROOT/"docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段三十九" in roadmap and "极小资金灰度最终人工授权包" in roadmap
    assert "阶段四十" in roadmap and "实盘开关隔离与最终红线复核" in roadmap
