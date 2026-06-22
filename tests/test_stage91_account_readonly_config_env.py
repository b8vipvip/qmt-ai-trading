from qmt_ai_trading.trading_gateway.account_readonly_config import build_account_readonly_config

def test_reads_userdata_mini_from_env_file(tmp_path, monkeypatch):
    p=tmp_path/'userdata_mini'; p.mkdir(); monkeypatch.delenv('QMT_USERDATA_MINI_PATH', raising=False); monkeypatch.delenv('QMT_USERDATA_PATH', raising=False)
    (tmp_path/'.env').write_text(f'QMT_USERDATA_MINI_PATH={p}\nQMT_ACCOUNT_ID=123456789\nQMT_SESSION_ID_BASE=910000\n', encoding='utf-8')
    cfg=build_account_readonly_config(tmp_path,{})
    assert cfg.userdata_mini_path == str(p)
    assert cfg.config_source.startswith('.env')
    assert cfg.to_dict()['account_id_masked'] == '12****89'
    assert '123456789' not in str(cfg.to_dict())

def test_env_overrides_env_file(tmp_path, monkeypatch):
    p=tmp_path/'env_userdata'; p.mkdir(); (tmp_path/'.env').write_text('QMT_USERDATA_MINI_PATH=bad\n', encoding='utf-8')
    monkeypatch.setenv('QMT_USERDATA_MINI_PATH', str(p)); monkeypatch.setenv('QMT_ACCOUNT_ID','123456789')
    cfg=build_account_readonly_config(tmp_path,{})
    assert cfg.userdata_mini_path == str(p)
    assert 'os.environ' in cfg.config_source

def test_userdata_path_fallback(tmp_path, monkeypatch):
    p=tmp_path/'fallback'; p.mkdir(); monkeypatch.delenv('QMT_USERDATA_MINI_PATH', raising=False); monkeypatch.setenv('QMT_USERDATA_PATH', str(p)); monkeypatch.setenv('QMT_ACCOUNT_ID','123456789')
    cfg=build_account_readonly_config(tmp_path,{})
    assert cfg.userdata_mini_path == str(p)
