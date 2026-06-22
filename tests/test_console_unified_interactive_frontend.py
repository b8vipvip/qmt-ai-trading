from pathlib import Path

def test_frontend_interactive_not_json_shell():
    app=Path('local_console_app/app.js').read_text(encoding='utf-8')
    html=Path('local_console_app/index.html').read_text(encoding='utf-8')
    css=Path('local_console_app/style.css').read_text(encoding='utf-8')
    for term in ['刷新','查询参数','EMPTY/DATA_MISSING','调试 JSON','/datahub/status','/account-readonly/positions']:
        assert term in app
    assert 'nav' in html and 'app.js' in html and 'style.css' in html
    assert 'table' in app and 'badge' in app and 'refresh' in css
    assert 'stageXX' not in app and 'local_console_' not in app
