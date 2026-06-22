from pathlib import Path

APP = Path('local_console_app_stage87/app.js').read_text(encoding='utf-8')
HTML = Path('local_console_app_stage87/index.html').read_text(encoding='utf-8')


def test_workflow_frontend_menus_and_title_present():
    for text in ['总览','系统运行工作台','功能矩阵','行情数据','因子研究','选股中心','策略任务','Agent 投研','AI 模型配置','回测分析','风控中心','报告中心','任务中心','系统设置','xtdata 只读行情','artifacts 迁移']:
        assert text in APP
    assert 'QMT AI 系统运行工作台' in APP
    assert '运行系统链路检查' in APP


def test_workflow_frontend_uses_relative_apis_and_missing_states():
    assert 'http://' not in APP and 'https://' not in APP
    for api in ['/api/v1/workflow/status','/api/v1/workflow/feature-matrix','/api/v1/datahub/status','/api/v1/live/status']:
        assert api in APP
    assert 'BACKEND_MISSING' in APP
    assert 'DISABLED_FOR_SAFETY' in APP
    assert "fetch('/api/v1/tasks/run'" in APP


def test_no_forbidden_script_contract_changes_documented():
    assert Path('scripts/sync_all.ps1').exists()
    validate = Path('scripts/validate_stage87.ps1').read_text(encoding='utf-8')
    assert 'D:\\AI\\run_qmt_tasks.ps1' in validate
    assert 'Set-Content -LiteralPath $runQmt' not in validate
