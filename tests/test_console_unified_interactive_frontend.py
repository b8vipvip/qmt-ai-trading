from pathlib import Path


def test_frontend_interactive_human_readable_not_json_shell():
    app = Path('local_console_app/app.js').read_text(encoding='utf-8')
    html = Path('local_console_app/index.html').read_text(encoding='utf-8')
    css = Path('local_console_app/style.css').read_text(encoding='utf-8')
    task_params = Path('local_console_app/task_params.js').read_text(encoding='utf-8')
    task_css = Path('local_console_app/task_params.css').read_text(encoding='utf-8')

    for term in [
        '刷新',
        '查询参数',
        '产物待生成',
        '后端待开发',
        '系统诊断明细',
        '/datahub/status',
        '/account-readonly/positions',
        '/tasks/catalog',
    ]:
        assert term in app

    for term in [
        'TASK_PARAM_PRESETS',
        'TASK_PRIORITY',
        'sortTasksForWorkflow',
        'xtdata_live_readonly_smoke',
        'paper_trading_dry_run',
        'Paper Trading / Shadow Trading dry-run',
        'allow_real_market_data',
        'allow_connect_miniqmt',
        'enable_account_readonly',
        'manual_confirmed',
        'allow_order_submit = false',
        'allow_order_cancel = false',
        'renderUpdatedArtifacts',
        '/datahub/market/latest',
        '/paper-trading/orders/latest',
        '/paper-trading/positions/latest',
        'Data Hub / market latest',
        'Paper Orders',
        'Shadow Positions',
        'orderedColumns',
    ]:
        assert term in task_params

    assert '.slice(0, 24)' not in task_params
    assert 'app.js' in html and 'style.css' in html and 'task_params.js' in html and 'ui_sanitize.js' in html
    assert 'table' in app and 'badge' in app and 'metrics' in css and 'task-card' in css and 'task-param-grid' in task_css
    assert '<pre>' not in app and '调试 JSON' not in app
    assert 'stageXX' not in app and 'local_console_' not in app
