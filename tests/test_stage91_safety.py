from pathlib import Path
from qmt_ai_trading.trading_gateway.account_readonly_report import run_account_readonly_stage91, scan_stage91_safety

def test_stage91_safety_report_passes_and_outputs_are_safe(tmp_path):
    report = run_account_readonly_stage91(tmp_path, "local_console_account_stage91")
    assert report["real_order_submitted"] is False
    safety = (tmp_path/"local_console_account_stage91/account_readonly_safety_report.json").read_text(encoding="utf-8")
    assert "\"status\": \"PASS\"" in safety
    combined = "\n".join(p.read_text(encoding="utf-8") for p in (tmp_path/"local_console_account_stage91").glob("*.json"))
    assert "1234567890" not in combined
    assert "local_runtime_account_stage91/" in Path(".gitignore").read_text(encoding="utf-8")

def test_stage91_repo_safety_scan_passes():
    assert scan_stage91_safety(".")["status"] == "PASS"
