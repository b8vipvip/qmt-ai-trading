import json
from qmt_ai_trading.datahub.datahub_report import run_stage88_datahub
from qmt_ai_trading.research.stage88_real_cache_factors import write_research

def test_stage88_research_from_real_cache(tmp_path):
    run_stage88_datahub('.', str(tmp_path/'dh'), ['510300.SH'], '1d', 30)
    r=write_research('.', str(tmp_path/'dh'/'datahub_real_cache.json'), str(tmp_path/'rs'))
    vals=json.loads((tmp_path/'rs'/'factor_values.json').read_text())['factors']
    assert r['dry_run'] and vals and {'momentum_5','momentum_20','volatility_20','volume_change_20','drawdown_20','composite_score','risk_flags'} <= set(vals[0])
