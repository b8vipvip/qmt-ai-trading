from qmt_ai_trading.common.artifact_migration import build_migration_plan, run_artifact_migration_stage87

def test_migration_plan_is_non_destructive(tmp_path):
    plan=build_migration_plan(tmp_path)
    assert plan['plan_only'] is True
    assert plan['delete_legacy'] is False
    assert all(step['destructive'] is False for step in plan['steps'])

def test_migration_report_generated(tmp_path):
    report=run_artifact_migration_stage87(tmp_path, 'local_console_artifact_migration_stage87')
    assert report['status']=='SUCCESS'
    assert (tmp_path/'local_console_artifact_migration_stage87/artifact_migration_report.json').exists()
