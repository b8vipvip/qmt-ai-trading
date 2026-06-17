from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.market_data import get_bars, get_latest_price
from qmt_ai_trading.datahub.models import ETFUniverseItem, LatestPrice
from qmt_ai_trading.datahub.symbols import is_etf_symbol, normalize_symbol
from qmt_ai_trading.strategies.etf_rotation import build_candidates_from_universe, generate_etf_rotation_intents


def test_normalize_symbol_plain_defaults_to_sh_for_510300():
    assert normalize_symbol("510300") == "510300.SH"


def test_normalize_symbol_sh_prefix():
    assert normalize_symbol("SH510300") == "510300.SH"


def test_normalize_symbol_sz_dot_prefix():
    assert normalize_symbol("sz.159915") == "159915.SZ"


def test_is_etf_symbol():
    assert is_etf_symbol("510300.SH") is True


def test_default_etf_universe_non_empty():
    assert get_default_etf_universe()


def test_etf_universe_item_symbol_standardized():
    for item in get_default_etf_universe():
        assert isinstance(item, ETFUniverseItem)
        assert item.symbol == normalize_symbol(item.symbol)


def test_get_bars_without_real_data_returns_list():
    assert isinstance(get_bars("510300.SH"), list)


def test_get_latest_price_without_real_data_returns_none_or_model():
    value = get_latest_price("510300.SH")
    assert value is None or isinstance(value, LatestPrice)


def test_build_candidates_from_universe_returns_candidates():
    candidates = build_candidates_from_universe(score_by_symbol={"510300.SH": 88})
    assert candidates
    assert candidates[0].symbol == normalize_symbol(candidates[0].symbol)


def test_candidates_enter_generate_etf_rotation_intents_as_dry_run():
    candidates = build_candidates_from_universe(score_by_symbol={"510300.SH": 88}, default_score=1)
    intents = generate_etf_rotation_intents(candidates, top_n=1, min_score=10)
    assert intents
    assert intents[0].dry_run is True
    assert intents[0].side == "BUY"
