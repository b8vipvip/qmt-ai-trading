import json, subprocess
from pathlib import Path
from qmt_ai_trading.console_api.account_readonly_runtime import run_account_readonly_subprocess


def test_subprocess_reads_files_when_stdout_is_not_json(tmp_path, monkeypatch):
    (tmp_path/'scripts').mkdir(); (tmp_path/'scripts/run_account_readonly_stage91.py').write_text('print("noise")', encoding='utf-8')
    out=tmp_path/'local_runtime_account_stage91'; out.mkdir()
    (out/'account_readonly_report.json').write_text(json.dumps({'status':'SUCCESS'}), encoding='utf-8')
    (out/'account_asset_snapshot.json').write_text(json.dumps({'asset':{'account_id_masked':'88****16','total_asset':0}}), encoding='utf-8')
    (out/'account_positions_snapshot.json').write_text(json.dumps({'positions':[],'position_count':0}), encoding='utf-8')
    def fake_run(*a, **k):
        return subprocess.CompletedProcess(a[0], 0, stdout='xtquant docs banner\nconnect_result: 0', stderr='')
    monkeypatch.setattr(subprocess, 'run', fake_run)
    res=run_account_readonly_subprocess(tmp_path, {'QMT_ACCOUNT_ID':'88123416'})
    assert res['ok'] is True and res['asset']['account_id_masked']=='88****16'
    assert res['order_submit_enabled'] is False and res['order_cancel_enabled'] is False


def test_subprocess_failure_is_explicit(tmp_path, monkeypatch):
    (tmp_path/'scripts').mkdir(); (tmp_path/'scripts/run_account_readonly_stage91.py').write_text('', encoding='utf-8')
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a[0], 3, stdout='noise', stderr='boom'))
    res=run_account_readonly_subprocess(tmp_path, {})
    assert res['ok'] is False
    assert res['status']=='SUBPROCESS_QUERY_FAILED'
    assert res['real_order_submitted'] is False


def test_subprocess_timeout_is_explicit(tmp_path, monkeypatch):
    (tmp_path/'scripts').mkdir(); (tmp_path/'scripts/run_account_readonly_stage91.py').write_text('', encoding='utf-8')
    def fake_run(*a, **k):
        raise subprocess.TimeoutExpired(cmd=a[0], timeout=k.get('timeout'))
    monkeypatch.setattr(subprocess, 'run', fake_run)
    res=run_account_readonly_subprocess(tmp_path, {})
    assert res['ok'] is False
    assert res['status']=='SUBPROCESS_TIMEOUT'
    assert res['timeout_seconds']==30
    assert res['order_submit_enabled'] is False
    assert res['real_order_submitted'] is False


def test_subprocess_missing_runtime_outputs_is_explicit(tmp_path, monkeypatch):
    (tmp_path/'scripts').mkdir(); (tmp_path/'scripts/run_account_readonly_stage91.py').write_text('print("xtquant文档地址：http://dict.thinktrader.net/nativeApi/start_now.html")', encoding='utf-8')
    def fake_run(*a, **k):
        return subprocess.CompletedProcess(a[0], 0, stdout='xtquant文档地址：http://dict.thinktrader.net/nativeApi/start_now.html\n***** xtdata连接成功 *****', stderr='')
    monkeypatch.setattr(subprocess, 'run', fake_run)
    res=run_account_readonly_subprocess(tmp_path, {})
    assert res['ok'] is False
    assert res['status']=='RUNTIME_OUTPUT_MISSING'
    assert 'xtdata连接成功' in res['stdout_tail']
    assert res['order_submit_enabled'] is False
    assert res['real_order_submitted'] is False
