from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_install_script_real_logging_markers_and_parent_target():
    p = ROOT/'scripts/install_run_qmt_tasks_logging.ps1'
    assert p.exists()
    text = p.read_text(encoding='utf-8')
    for marker in ['run_qmt_tasks.ps1','validation_logs','stage${stage}_validation_','Start-Transcript','Stop-Transcript','try','finally','验收日志已保存到']:
        assert marker in text
    assert 'Split-Path -Parent $PSScriptRoot' in text and '$aiRoot = Split-Path -Parent $repoRoot' in text

def test_actual_parent_run_script_or_installer_is_not_template_only():
    actual = ROOT.parent/'run_qmt_tasks.ps1'
    text = actual.read_text(encoding='utf-8') if actual.exists() else (ROOT/'scripts/install_run_qmt_tasks_logging.ps1').read_text(encoding='utf-8')
    for marker in ['validation_logs','stage${stage}_validation_','Start-Transcript','Stop-Transcript','验收日志已保存到']:
        assert marker in text
    assert 'Read-Host' in text and 'sync_all.ps1' in text and 'validate_stage${stage}.ps1' in text

def test_sync_all_not_modified_for_stage80():
    text = (ROOT/'scripts/sync_all.ps1').read_text(encoding='utf-8')
    assert 'stage80fix' not in text.lower()
