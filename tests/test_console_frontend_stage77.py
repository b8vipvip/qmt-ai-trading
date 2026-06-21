from pathlib import Path
ROOT=Path('local_console_app_stage77')
def read(n): return (ROOT/n).read_text(encoding='utf-8')
def test_files_exist_and_chinese_title():
    assert ROOT.exists(); assert (ROOT/'README.md').exists(); assert 'QMT AI 本地量化控制台' in read('index.html')
def test_app_calls_whitelist_api_and_no_danger_fetch():
    js=read('app.js')
    for p in ['/health','/tasks/catalog','/tasks/run','/tasks','/reports','/console/summary']:
        assert p in js
    assert 'http://127.0.0.1:8768/api/v1' in js
    for bad in ["fetch('/trade')",'fetch("/trade")',"fetch('/order')",'fetch("/order")',"fetch('/approve')",'fetch("/approve")',"fetch('/account')",'fetch("/account")',"fetch('/positions')",'fetch("/positions")',"fetch('/assets')",'fetch("/assets")',"fetch('/live')",'fetch("/live")',"fetch('/notify')",'fetch("/notify")']:
        assert bad not in js
    assert 'cdn' not in read('index.html').lower()
def test_css_backend_layout_cards_table_badge_responsive():
    css=read('style.css')
    for x in ['sidebar','topbar','card','table','badge','@media']:
        assert x in css
def test_offline_and_status_chinese():
    js=read('app.js')
    for x in ['API 离线','运行中','成功','失败','已阻断','JSON 解析失败','网络超时','后端返回错误']:
        assert x in js
def test_generated_reports_and_validate_rules():
    for n in ['local_console_business_console_report.md','local_console_business_console_report.json','frontend_api_contract.md','task_catalog.md','integration_check_report.md','next_pre_live_safety_audit_plan.md']:
        assert (ROOT/n).exists()
    text=Path('scripts/validate_stage77.ps1').read_text(encoding='utf-8')
    assert 'sync_all.ps1' in text and 'Clean-PythonCache' in text
    assert text.find('Clean-PythonCache') < text.find('sync_all.ps1 -Mode scan')
