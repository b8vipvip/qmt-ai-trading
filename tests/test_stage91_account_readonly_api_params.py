from qmt_ai_trading.console_api.api_server import _account_readonly_response

ENABLED_QS = {
    "enable_account_readonly": ["true"],
    "allow_import_xttrader": ["true"],
    "allow_connect_trade_session": ["true"],
    "allow_account_query": ["true"],
    "allow_position_query": ["true"],
    "manual_confirmed": ["true"],
    "read_only": ["true"],
    "dry_run": ["true"],
    "allow_order_submit": ["false"],
    "allow_order_cancel": ["false"],
}

def test_account_readonly_api_default_disabled():
    payload = _account_readonly_response({}, "status")
    assert payload["ok"] is True
    assert payload["enabled"] is False
    assert payload["account_query_enabled"] is False
    assert payload["position_query_enabled"] is False
    assert payload["order_submit_enabled"] is False
    assert payload["real_order_submitted"] is False

def test_account_readonly_api_enabled_params_use_readonly_provider():
    payload = _account_readonly_response(ENABLED_QS, "status")
    assert payload["enabled"] is True
    assert payload["account_query_enabled"] is True
    assert payload["position_query_enabled"] is True
    assert payload["manual_confirmation_completed"] is True
    assert payload["safety_status"] == "READONLY_ENABLED"

def test_account_readonly_api_forces_order_permissions_false():
    qs = {**ENABLED_QS, "allow_order_submit": ["true"], "allow_order_cancel": ["true"]}
    payload = _account_readonly_response(qs, "status")
    assert payload["order_submit_enabled"] is False
    assert payload["order_cancel_enabled"] is False
    assert payload["real_order_submitted"] is False
    assert payload["warnings"]


def test_account_readonly_asset_enabled_params_do_not_silent_disable():
    payload = _account_readonly_response(ENABLED_QS, "asset")
    assert payload["enabled"] is True
    assert payload["manual_confirmation_completed"] is True
    assert payload["order_submit_enabled"] is False
    assert payload["real_order_submitted"] is False
    assert payload["status"] in {"SUCCESS", "ACCOUNT_QUERY_FAILED", "ACCOUNT_QUERY_ERROR", "CONFIG_ERROR_USERDATA_PATH_MISSING", "CONFIG_ERROR_USERDATA_PATH_NOT_EXISTS", "CONFIG_ERROR_ACCOUNT_ID_MISSING", "IMPORT_ERROR_XTTRADER", "CONNECT_ERROR", "SUBPROCESS_QUERY_FAILED"}
    if payload["status"] == "ACCOUNT_QUERY_FAILED":
        assert payload["ok"] is False
        assert payload["mock_data"] is False
        assert payload["error_message"]


def test_account_readonly_positions_enabled_params_do_not_silent_disable():
    payload = _account_readonly_response(ENABLED_QS, "positions")
    assert payload["enabled"] is True
    assert payload["manual_confirmation_completed"] is True
    assert payload["order_cancel_enabled"] is False
    assert payload["real_order_submitted"] is False
    assert payload["status"] in {"SUCCESS", "POSITION_QUERY_FAILED", "POSITION_QUERY_ERROR", "CONFIG_ERROR_USERDATA_PATH_MISSING", "CONFIG_ERROR_USERDATA_PATH_NOT_EXISTS", "CONFIG_ERROR_ACCOUNT_ID_MISSING", "IMPORT_ERROR_XTTRADER", "CONNECT_ERROR", "SUBPROCESS_QUERY_FAILED"}
    if payload["status"] == "POSITION_QUERY_FAILED":
        assert payload["ok"] is False
        assert payload["mock_data"] is False
        assert payload["error_message"]


def test_account_readonly_without_manual_confirmation_refuses_real_query():
    qs = {**ENABLED_QS, "manual_confirmed": ["false"]}
    payload = _account_readonly_response(qs, "asset")
    assert payload["enabled"] is False
    assert payload["manual_confirmation_completed"] is False
    assert payload["query_attempted"] is False
    assert payload["order_submit_enabled"] is False


def test_account_readonly_task_runner_accepts_string_query_booleans(tmp_path, monkeypatch):
    from qmt_ai_trading.console_api.task_runner import run_task
    from qmt_ai_trading.console_api.task_store import TaskStore
    params = {k: v[0] for k, v in ENABLED_QS.items()}
    monkeypatch.chdir(tmp_path)
    params["repo_root"] = "."
    params["output_dir"] = "local_console_account_stage91_test_tmp"
    run = run_task("account_readonly_dry_run", params, TaskStore())
    assert run.output["enabled"] is True
    assert run.output["manual_confirmation_completed"] is True
    assert run.output["account_query_enabled"] is True
    assert run.output["position_query_enabled"] is True
    assert run.output["order_submit_enabled"] is False
    assert run.output["real_order_submitted"] is False

def test_account_readonly_refresh_uses_subprocess(monkeypatch):
    import qmt_ai_trading.console_api.api_server as api
    called={}
    def fake(root, qs):
        called['yes']=True
        return {'ok':True,'status':'SUCCESS','asset':{'total_asset':0},'positions':[],'position_count':0,'read_only':True,'order_submit_enabled':False,'order_cancel_enabled':False,'real_order_submitted':False}
    monkeypatch.setattr(api, 'run_account_readonly_subprocess', fake)
    res=api._account_readonly_refresh(ENABLED_QS)
    assert called['yes'] and res['asset'] and res['position_count']==0


def test_runtime_dir_and_tmp_probe_ignored():
    gi=open('.gitignore',encoding='utf-8').read()
    assert 'local_runtime_account_stage91/' in gi
    assert 'tmp_*.py' in gi
