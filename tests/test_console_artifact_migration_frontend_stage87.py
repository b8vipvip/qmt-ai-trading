from pathlib import Path

def test_frontend_artifact_pages_exist():
    text=Path('local_console_app_stage87/index.html').read_text(encoding='utf-8')
    assert 'artifacts 目录规范化' in text
    assert 'path compatibility map' in text
    assert 'artifacts/reports/stage84/market_gateway' in text
    assert 'legacy 目录只读兼容，不删除' in text

def test_validate_script_readonly_constraints():
    text=Path('scripts/validate_stage87.ps1').read_text(encoding='utf-8')
    assert 'install_run_qmt_tasks_logging.ps1' not in text
    assert 'sync_all.ps1' not in text
    assert 'Tee-Object' not in text
    assert 'Out-File' not in text
    assert '>>' not in text
