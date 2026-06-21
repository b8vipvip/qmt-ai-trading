from qmt_ai_trading.console_api.safety import *
from qmt_ai_trading.console_api.task_registry import list_tasks, get_task
from qmt_ai_trading.console_api.task_store import TaskStore
from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.api_server import summary
import pytest

def test_api_bind_and_health_semantics():
    assert_localhost_bind('127.0.0.1')
    with pytest.raises(ConsoleSafetyError): assert_localhost_bind('0.0.0.0')
    s=summary(); assert s['mode']=='dry-run/shadow' and s['no_trade_authorization'] is True

def test_catalog_whitelist():
    ids={t.task_id for t in list_tasks()}
    for x in ['market_snapshot_readonly','daily_pipeline_dry_run','agent_research_brief','risk_gate_dry_run_check']:
        assert x in ids
    for t in list_tasks():
        assert t.safe_mode and t.dry_run_only and t.forbidden_in_live

def test_run_whitelist_and_unknown_blocked():
    st=TaskStore(); r=run_task('market_snapshot_readonly',{'symbol':'510300.SH'},st)
    assert r.status=='SUCCESS' and r.output['read_only'] is True
    with pytest.raises(ConsoleSafetyError): run_task('unknown_task',{},st)

def test_reject_command_script_path_shell_path_sensitive():
    for p in [{'command':'echo x'},{'script_path':'x.py'},{'symbol':'510300.SH;rm -rf x'},{'symbol':'../x'},{'symbol':'.env'}]:
        with pytest.raises(ConsoleSafetyError): assert_safe_task_params(p)

def test_methods_rejected():
    for m in ['PUT','PATCH','DELETE']:
        with pytest.raises(ConsoleSafetyError): assert_http_method_allowed(m,'/api/v1/tasks/run')
    with pytest.raises(ConsoleSafetyError): assert_http_method_allowed('POST','/api/v1/health')

def test_forbidden_markers():
    for marker in ['xttrader','XtQuantTrader','order_stock','place_order','query_stock_asset','query_stock_positions']:
        with pytest.raises(ConsoleSafetyError): scan_console_api_for_forbidden_markers(marker)

def test_task_output_boundaries():
    st=TaskStore()
    assert 'ohlcv' in run_task('market_snapshot_readonly',{},st).output
    a=run_task('agent_research_brief',{},st).output; assert 'confidence' in a and 'risk_flags' in a and 'order' not in str(a).lower()
    s=run_task('strategy_dry_run_signals',{},st).output; assert 'signals' in s and 'DRY_RUN_ONLY' in str(s)
    r=run_task('risk_gate_dry_run_check',{},st).output; assert r['blocked'] is True
