from pathlib import Path
import inspect
import qmt_ai_trading.console_api.api_server as api_server
from qmt_ai_trading.console_api.task_registry import get_task

def test_monitoring_frontend_contains_required_sections_and_no_forbidden_ui_terms():
    text=(Path('local_console_app_stage83/index.html').read_text(encoding='utf-8')+'\n'+Path('local_console_app_stage83/app.js').read_text(encoding='utf-8'))
    for token in ['监控告警','告警列表','熔断状态卡片','风险事件时间线','系统健康总览','GET /api/v1/monitoring/alerts/latest','dry_run=true','no_real_notification=true','requires_human_review=true']:
        assert token in text
    for forbidden in ['真实发送','发送短信','发送邮件','一键下单','自动买入','自动卖出','实盘交易','批准交易','绕过风控']:
        assert forbidden not in text

def test_monitoring_api_routes_and_task_registered():
    src=inspect.getsource(api_server)
    for route in ['/api/v1/monitoring/context','/api/v1/monitoring/alerts/latest','/api/v1/monitoring/circuit-breaker/latest','/api/v1/monitoring/risk-events/latest','/api/v1/monitoring/system-health/latest','/api/v1/monitoring/report/latest']:
        assert route in src
    assert get_task('monitoring_alert_dry_run') is not None

def test_validate_stage83_is_read_only():
    text=Path('scripts/validate_stage83.ps1').read_text(encoding='utf-8')
    assert 'install_run_qmt_tasks_logging.ps1' not in text
    assert 'sync_all.ps1' not in text
    assert 'Tee-Object -FilePath' not in text and 'Out-File' not in text
    assert 'Set-Content' not in text and 'Add-Content' not in text
