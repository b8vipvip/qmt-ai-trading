from pathlib import Path

def test_frontend_contains_paper_dashboard_labels():
    html=Path('local_console_app_stage89/index.html').read_text(encoding='utf-8')
    assert 'Paper Trading' in html and '影子交易' in html and '真实下单' in html and '标的' in html
