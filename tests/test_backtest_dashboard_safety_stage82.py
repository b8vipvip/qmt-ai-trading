from pathlib import Path
from qmt_ai_trading.backtest_dashboard.safety import scan_text, with_safety


def test_forbidden_terms_mark_unsafe():
    res=scan_text({'x':'please place_order and bypass_risk via xttrader'})
    assert res['unsafe'] is True
    assert {'place_order','bypass_risk','xttrader'} <= set(res['forbidden_terms'])


def test_outputs_keep_safety_flags():
    res=with_safety({'hello':'world'})
    for k in ['dry_run','not_live_trading','research_only','no_order_submitted','no_qmt_trader_api','requires_risk_gate','requires_human_approval']:
        assert res[k] is True


def test_validate_stage82_readonly_constraints():
    text=Path('scripts/validate_stage82.ps1').read_text(encoding='utf-8')
    assert 'install_run_qmt_tasks_logging.ps1' not in text
    assert 'Set-Content D:\\AI\\run_qmt_tasks.ps1' not in text
    assert 'Add-Content D:\\AI\\run_qmt_tasks.ps1' not in text
    assert 'sync_all.ps1 -Mode scan' in text and 'sync_all.ps1 -Mode status' in text
