from pathlib import Path
from qmt_ai_trading.trading_gateway.account_readonly_report import run_account_readonly_stage91

def test_stage91_frontend_contract_and_html(tmp_path):
    r = run_account_readonly_stage91(tmp_path, "local_console_account_stage91")
    assert r["order_submit_enabled"] is False
    contract = (tmp_path/"local_console_account_stage91/frontend_account_contract.json").read_text(encoding="utf-8")
    html = (tmp_path/"local_console_app_stage91/index.html").read_text(encoding="utf-8")
    for text in ["账户只读", "持仓只读", "read_only=true", "order_submit_enabled=false", "real_order_submitted=false", "account_masked=true"]:
        assert text in contract or text in html
    for forbidden in ["一键下单", "立即买入", "立即卖出"]:
        assert forbidden not in html
