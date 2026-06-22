from pathlib import Path

def test_cleanup_scripts_are_dry_run_first():
    audit=Path('scripts/audit_stage_legacy_inventory.ps1').read_text(encoding='utf-8')
    cleanup=Path('scripts/cleanup_stage_legacy.ps1').read_text(encoding='utf-8')
    assert 'delete_plan.md' in audit
    assert 'tracked_stage_files.txt' in audit
    assert 'DRY-RUN' in cleanup
    assert '--Apply' in cleanup or '$Apply' in cleanup
