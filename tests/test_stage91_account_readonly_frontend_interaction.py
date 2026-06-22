from pathlib import Path

HTML = Path("local_console_app_stage91/index.html").read_text(encoding="utf-8")

def test_stage91_frontend_buttons_are_wired_to_interaction_state():
    assert "const accountReadonlyState" in HTML
    assert "enableReadonly.onclick" in HTML
    assert "disableReadonly.onclick" in HTML
    assert "refreshAsset.onclick" in HTML
    assert "refreshPositions.onclick" in HTML

def test_stage91_frontend_has_manual_confirmation_checkbox_and_blocks_without_it():
    assert 'id="manualConfirm" type="checkbox"' in HTML
    assert "请先勾选人工确认。" in HTML
    assert "if(!manualConfirm.checked)" in HTML

def test_stage91_frontend_fetches_enabled_query_params_and_readonly_endpoints():
    assert "enable_account_readonly" in HTML
    assert "manual_confirmed" in HTML
    assert "allow_order_submit:'false'" in HTML
    assert "allow_order_cancel:'false'" in HTML
    assert "/api/v1/account-readonly/asset" in HTML
    assert "/api/v1/account-readonly/positions" in HTML

def test_stage91_frontend_human_readable_cards_and_no_forbidden_actions():
    for text in ["账户状态", "账号：", "总资产", "可用资金", "持仓市值", "证券代码", "证券名称", "原始 JSON 折叠区"]:
        assert text in HTML
    for forbidden in ["一键下单", "立即买入", "立即卖出", "撤单", "自动交易"]:
        # Only explanatory safety text may mention no cancel/no auto trading; no entry labels are present.
        assert f">{forbidden}<" not in HTML

def test_stage91_frontend_enable_button_refreshes_backend_asset_and_positions():
    assert "await Promise.all([refreshStatus(),refreshAssetOnly(),refreshPositionsOnly()])" in HTML
    assert "正在调用后端账户/持仓只读 API" in HTML
    assert "a.ok===false" in HTML
    assert "p.ok===false" in HTML
