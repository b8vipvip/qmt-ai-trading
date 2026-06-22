import json
from qmt_ai_trading.datahub.datahub_report import run_stage88_datahub

def test_stage88_datahub_real_cache(tmp_path):
    r=run_stage88_datahub('.', str(tmp_path/'dh'), ['510300.SH','510500.SH'], '1d', 30)
    cache=json.loads((tmp_path/'dh'/'datahub_real_cache.json').read_text())
    assert r['dry_run'] and r['no_order_submitted'] and cache['bar_count'] >= 1
    assert set(cache['symbols']).issubset({'510300.SH','510500.SH'})
