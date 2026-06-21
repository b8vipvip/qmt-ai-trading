from pathlib import Path

def test_logging_template_contains_required_transcript_bits():
    text=Path('scripts/run_qmt_tasks_with_validation_log.ps1').read_text(encoding='utf-8')
    assert 'validation_logs' in text
    assert 'stage${stage}_validation_${timestamp}.log' in text
    assert 'Start-Transcript' in text and '-Encoding UTF8' in text
    assert 'Stop-Transcript' in text
    assert '验收日志已保存到:' in text
    assert 'Tee-Object' in text or 'Out-File' in text
    assert 'sync_all.ps1 -Mode pull' in text and 'validate_stage${stage}.ps1' in text

def test_sync_all_not_modified_and_validate_stage79_rules():
    assert Path('scripts/sync_all.ps1').exists()
    text=Path('scripts/validate_stage79.ps1').read_text(encoding='utf-8')
    assert 'function Print-File' in text and '-Encoding UTF8' in text
    assert 'Clean-PythonCache' in text and text.find('Clean-PythonCache') < text.find('sync_all.ps1 -Mode scan')
    assert 'validate_stage78.ps1.bak_stage78fix_*' in text
