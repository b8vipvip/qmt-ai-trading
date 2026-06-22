from pathlib import Path
from qmt_ai_trading.trading_gateway.import_guard import scan_imports

def test_import_guard_ast_blocks_executable_import(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("from xtquant import xttrader\n", encoding="utf-8")
    assert scan_imports([str(bad)])["status"] == "FAIL"

def test_import_guard_allows_string(tmp_path):
    ok = tmp_path / "ok.py"
    ok.write_text('target = "xtquant.xttrader"\n', encoding="utf-8")
    assert scan_imports([str(ok)])["status"] == "PASS"
