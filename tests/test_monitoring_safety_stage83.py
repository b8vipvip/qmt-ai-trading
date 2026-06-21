from qmt_ai_trading.monitoring.safety import scan_obj
from qmt_ai_trading.monitoring.anomaly_detector import detect_alerts

def test_forbidden_terms_detected():
    hits=scan_obj({'note':'execute_order live_trade xttrader auto_approve bypass_risk query_account send_sms'})
    for term in ['execute_order','live_trade','xttrader','auto_approve','bypass_risk','query_account','send_sms']:
        assert term in hits

def test_forbidden_terms_create_high_or_critical_alerts():
    ctx={'created_at':'stable','input_sources':[{'stage':'StageX','path':'x.json','fallback_used':False,'mock_data':False}], 'payloads':{'x.json':{'unsafe':True,'text':'place_order query_position'}}, 'missing_files':[], 'repo_dirty':False, 'validation_nul_logs':[]}
    alerts=detect_alerts(ctx)
    assert any(a['rule_id']=='UNSAFE_AGENT_OUTPUT' for a in alerts)
    assert any(a['severity'] in {'HIGH','CRITICAL'} for a in alerts)
