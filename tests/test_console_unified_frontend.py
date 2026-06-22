from pathlib import Path

def test_frontend_modules_and_api_prefix():
    app=Path('local_console_app/app.js').read_text(encoding='utf-8')
    for label in ['总览 / 工作流状态','QMT / xtdata 行情状态','Data Hub 行情缓存','Research 因子研究','候选池排名','Agent 投研','Strategy 策略信号','Risk Gate 风控审查','TradeIntent dry-run','Paper Trading / Shadow Replay','Monitoring / Alerts','Human Approval 人工确认','Account Readonly / 持仓只读','Safety / Live Disabled 安全边界']:
        assert label in app
    assert "const API='/api/v1'" in app
    assert '真实下单' not in app and '撤单按钮' not in app

def test_frontend_safety_display():
    html=Path('local_console_app/index.html').read_text(encoding='utf-8')
    for flag in ['read_only=true','dry_run=true','live_disabled=true','no_order_submitted=true','requires_human_approval=true','account_masked=true']:
        assert flag in html
