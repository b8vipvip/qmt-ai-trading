from qmt_ai_trading.research.factor_registry import catalog_as_dict
from qmt_ai_trading.research.factor_config import config_seed_as_dict
from qmt_ai_trading.research.factor_engine import make_mock_bars, compute_factor_value, run_factor_scan
from qmt_ai_trading.research.factor_evaluation import evaluate_factor_results
from qmt_ai_trading.research.candidate_builder import build_candidates
from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore

def test_factor_catalog_and_config_seed():
    cats=catalog_as_dict(); assert len(cats)>=8
    for f in cats:
        for k in ['factor_id','name_zh','category','params_schema','default_params','direction','default_weight','enabled','requires_fields']:
            assert k in f
        assert f['name_zh'] and f['category'] in ['动量','波动率','成交量','均线','回撤','基本面','情绪','自定义']
    cfg=config_seed_as_dict(); assert cfg and {'window','lookback','weight','direction','winsorize','standardize','neutralize','enabled'} <= set(cfg[0])

def test_factor_engine_core_factors():
    bars=make_mock_bars('510300.SH',90)
    assert compute_factor_value('momentum_20d',bars,{'window':20}) is not None
    assert compute_factor_value('volatility_20d',bars,{'window':20}) is not None
    assert compute_factor_value('volume_ratio_20d',bars,{'window':20}) is not None

def test_evaluation_candidates_and_factor_scan_not_placeholder():
    scan=run_factor_scan({'factor_set':['momentum_20d','volatility_20d','volume_ratio_20d']})
    assert scan['not_live_trading'] is True and scan['data_source'] in ['mock','cached','qmt']
    assert scan['factor_results'] and scan['factor_evaluation']['IC'] is not None and scan['factor_evaluation']['RankIC'] is not None
    c=scan['factor_candidates'][0]; assert {'score','rank','reasons','risk_flags'} <= set(c)
    r=run_task('factor_scan',{'universe':'ETF'},TaskStore())
    assert r.output['task_id']=='factor_scan' and r.output['factor_results']

def test_markdown_json_chinese_not_mojibake():
    assert '动量' in str(catalog_as_dict()) and '锟斤拷' not in str(catalog_as_dict())
