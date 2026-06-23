from pathlib import Path


def test_unified_development_rules_and_validation_entry_exist():
    rules = Path('docs/qmt-ai-trading-unified-development-rules.md').read_text(encoding='utf-8')
    script = Path('scripts/validate_project.ps1').read_text(encoding='utf-8')

    assert '不再新建 `stageXX`' in rules
    assert '统一后端入口' in rules
    assert '统一前端入口' in rules
    assert 'scripts\\validate_project.ps1' in rules
    assert 'project_validation_' in script
    assert 'validate_console_unified.ps1' in script
    assert 'no_stage_development' in script
