from pathlib import Path
import json
from qmt_ai_trading.monitoring import run_monitoring_stage83

def test_stage83_generates_outputs(tmp_path):
    report=run_monitoring_stage83('.', str(tmp_path/'mon'))
    assert report['dry_run'] and report['not_live_trading'] and report['research_only'] and report['no_real_notification']
    for name in ['monitoring_input_context','monitoring_alerts','circuit_breaker_status','risk_event_timeline','system_health_report','frontend_monitoring_contract','next_live_sandbox_plan']:
        assert (tmp_path/'mon'/f'{name}.json').exists()
        assert (tmp_path/'mon'/f'{name}.md').exists()
    alerts=json.loads((tmp_path/'mon'/'monitoring_alerts.json').read_text(encoding='utf-8'))['alerts']
    assert alerts
    required={'alert_id','rule_id','severity','source_stage','source_file','message','evidence','recommendation','dry_run','not_live_trading','research_only','no_real_notification','created_at'}
    assert required <= set(alerts[0])
    assert all(a['dry_run'] and a['no_real_notification'] for a in alerts)

def test_stage83_fallback_when_inputs_missing(tmp_path):
    report=run_monitoring_stage83(str(tmp_path), 'out')
    ctx=json.loads((tmp_path/'out'/'monitoring_input_context.json').read_text(encoding='utf-8'))
    assert ctx['fallback_used'] is True and ctx['mock_data'] is True
    assert ctx['not_live_trading'] is True and ctx['research_only'] is True
