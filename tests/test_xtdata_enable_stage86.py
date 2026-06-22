import sys
from qmt_ai_trading.market_gateway import XtDataEnableRequest, default_manual_checklist, run_environment_check, audit_xtdata_config, decide_xtdata_enable, run_xtdata_enable_stage86

def test_enable_request_defaults_disabled():
    r=XtDataEnableRequest().to_dict()
    assert r['enable_xtdata'] is False and r['enable_real_market_data'] is False and r['connect_miniqmt'] is False and r['allow_xttrader'] is False
    assert r['dry_run'] is True and r['read_only'] is True and r['manual_confirmation_completed'] is False

def test_manual_checklist_defaults_unchecked():
    c=default_manual_checklist().to_dict()
    assert len(c['items']) >= 10
    assert all(i['checked'] is False for i in c['items'])
    assert c['manual_confirmation_completed'] is False

def test_environment_check_no_import_or_connection():
    before=set(sys.modules); env=run_environment_check('.').to_dict()
    assert env['xtdata_import_attempted'] is False and env['mini_qmt_connection_attempted'] is False and env['real_market_data_attempted'] is False
    assert 'xtquant' not in set(sys.modules)-before

def test_decision_allowed_and_not_enabled():
    req=XtDataEnableRequest().to_dict(); env=run_environment_check('.').to_dict(); c=default_manual_checklist().to_dict(); audit=audit_xtdata_config({}, req).to_dict(); d=decide_xtdata_enable(c,env,audit,req)
    assert d['decision'] in {'BLOCKED','READY_FOR_MANUAL_REVIEW','SANDBOX_ONLY'}
    assert d['decision'] != 'ENABLED'
    assert d['xtdata_enabled'] is False and d['real_market_data'] is False and d['mini_qmt_connected'] is False and d['xtdata_imported'] is False

def test_stage86_outputs_reports(tmp_path):
    out=tmp_path/'enable'; report=run_xtdata_enable_stage86('.', str(out))
    assert report['enable_xtdata'] is False and report['real_market_data'] is False and report['mini_qmt_connected'] is False and report['xtdata_imported'] is False
    for name in ['xtdata_enable_input_context','xtdata_enable_request','xtdata_environment_check','xtdata_manual_checklist','xtdata_config_audit','xtdata_enable_decision','xtdata_enable_report','frontend_xtdata_enable_contract','next_xtdata_adapter_probe_plan']:
        assert (out/f'{name}.json').exists(); assert (out/f'{name}.md').exists()
