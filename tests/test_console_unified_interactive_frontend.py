from pathlib import Path


def test_frontend_interactive_human_readable_not_json_shell():
    app = Path('local_console_app/app.js').read_text(encoding='utf-8')
    html = Path('local_console_app/index.html').read_text(encoding='utf-8')
    css = Path('local_console_app/style.css').read_text(encoding='utf-8')

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

    assert 'app.js' in html and 'style.css' in html and 'ui_sanitize.js' in html
    assert 'table' in app and 'badge' in app and 'metrics' in css and 'task-card' in css
    assert '<pre>' not in app and '调试 JSON' not in app
    assert 'stageXX' not in app and 'local_console_' not in app
