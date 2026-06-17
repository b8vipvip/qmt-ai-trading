from datetime import datetime, timedelta

from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.research.factors import (
    FactorResult,
    compute_momentum_factor,
    compute_volatility_factor,
    compute_volume_factor,
    rank_factor_results,
)
from qmt_ai_trading.research.report import ResearchReport, build_research_report, format_research_report_text
from qmt_ai_trading.research.scoring import ResearchScore, score_etf_universe, score_symbol_from_bars
from qmt_ai_trading.strategies.etf_rotation import build_candidates_from_research_scores, generate_etf_rotation_intents, ETFCandidate


def make_bars(symbol="510300.SH", count=30):
    base = datetime(2026, 1, 1)
    return [
        MarketBar(
            symbol=symbol,
            datetime=base + timedelta(days=i),
            open=100 + i,
            high=101 + i,
            low=99 + i,
            close=100 + i,
            volume=1000 + i * 10,
            amount=(100 + i) * (1000 + i * 10),
            source="test",
        )
        for i in range(count)
    ]


def test_empty_bars_do_not_crash():
    score = score_symbol_from_bars("510300.SH", [])
    assert isinstance(score, ResearchScore)
    assert score.score is None
    assert not score.eligible


def test_momentum_factor_can_compute():
    result = compute_momentum_factor(make_bars(), window=5)
    assert isinstance(result, FactorResult)
    assert result.score is not None
    assert result.factors[0].name == "momentum"


def test_volatility_factor_can_compute():
    result = compute_volatility_factor(make_bars(), window=5)
    assert result.score is not None
    assert result.factors[0].name == "volatility"


def test_volume_factor_can_compute():
    result = compute_volume_factor(make_bars(), window=5)
    assert result.score is not None
    assert result.factors[0].name == "volume"


def test_factor_results_can_be_ranked():
    ranked = rank_factor_results([
        FactorResult(symbol="A", score=1.0),
        FactorResult(symbol="B", score=3.0),
        FactorResult(symbol="C", score=None),
    ])
    assert [item.symbol for item in ranked] == ["B", "A", "C"]


def test_score_symbol_from_bars_returns_research_score():
    score = score_symbol_from_bars("510300.SH", make_bars())
    assert isinstance(score, ResearchScore)
    assert score.symbol == "510300.SH"
    assert score.score is not None


def test_score_etf_universe_handles_multiple_symbols():
    scores = score_etf_universe({"510300.SH": make_bars("510300.SH"), "510500.SH": make_bars("510500.SH")})
    assert len(scores) == 2
    assert all(isinstance(item, ResearchScore) for item in scores)


def test_build_research_report_generates_report():
    report = build_research_report([score_symbol_from_bars("510300.SH", make_bars())])
    assert isinstance(report, ResearchReport)
    assert report.scores


def test_format_research_report_text_returns_string():
    report = build_research_report([score_symbol_from_bars("510300.SH", make_bars())])
    text = format_research_report_text(report)
    assert isinstance(text, str)
    assert "辅助分析" in text


def test_research_scores_build_candidates_and_generate_intents():
    scores = [score_symbol_from_bars("510300.SH", make_bars())]
    candidates = build_candidates_from_research_scores(scores, target_percent=0.1)
    assert candidates
    assert isinstance(candidates[0], ETFCandidate)
    intents = generate_etf_rotation_intents(candidates, top_n=1, capital=100000)
    assert intents
    assert intents[0].symbol == "510300.SH"
