from datetime import datetime, timedelta

from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.research.dataset import (
    ResearchDataset,
    build_feature_rows_from_bars,
    build_forward_return_labels,
    build_research_dataset,
    split_dataset_by_ratio,
)
from qmt_ai_trading.research.metrics import (
    ModelEvaluationResult,
    compute_ic,
    compute_rank_ic,
    evaluate_predictions,
    pearson_corr,
    spearman_corr,
)
from qmt_ai_trading.research.model_lab import ModelLabResult, run_model_lab
from qmt_ai_trading.research.scoring import ResearchScore, research_scores_from_model_predictions
from qmt_ai_trading.strategies.etf_rotation import build_candidates_from_research_scores, generate_etf_rotation_intents


def make_bars(symbol="510300.SH", count=12):
    base = datetime(2026, 1, 1)
    return [
        MarketBar(
            symbol=symbol,
            datetime=base + timedelta(days=i),
            open=100 + i,
            high=101 + i,
            low=99 + i,
            close=100 + i * 2,
            volume=1000 + i * 10,
            amount=(100 + i * 2) * (1000 + i * 10),
            source="test",
        )
        for i in range(count)
    ]


def test_build_feature_rows_from_bars_empty_does_not_crash():
    assert build_feature_rows_from_bars("510300.SH", []) == []


def test_build_feature_rows_from_bars_generates_features():
    rows = build_feature_rows_from_bars("510300.SH", make_bars(count=3))
    assert len(rows) == 3
    assert rows[0].symbol == "510300.SH"
    assert "prev_close_return" in rows[1].features


def test_build_forward_return_labels_generates_forward_return():
    labels = build_forward_return_labels("510300.SH", make_bars(count=3), horizon=1)
    assert len(labels) == 2
    assert labels[0].forward_return > 0


def test_build_research_dataset_generates_dataset():
    dataset = build_research_dataset("510300.SH", make_bars(count=5), horizon=1)
    assert isinstance(dataset, ResearchDataset)
    assert len(dataset.features) == len(dataset.labels) == 4


def test_split_dataset_by_ratio_splits_train_test():
    dataset = build_research_dataset("510300.SH", make_bars(count=11), horizon=1)
    split = split_dataset_by_ratio(dataset, train_ratio=0.6)
    assert len(split.train.labels) == 6
    assert len(split.test.labels) == 4


def test_pearson_corr_normal():
    assert round(pearson_corr([1, 2, 3], [1, 2, 3]), 6) == 1.0


def test_spearman_corr_normal():
    assert round(spearman_corr([10, 20, 30], [1, 2, 3]), 6) == 1.0


def test_compute_ic_normal():
    assert compute_ic([1, 2, 3], [1, 2, 3]) > 0.99


def test_compute_rank_ic_normal():
    assert compute_rank_ic([3, 2, 1], [1, 2, 3]) < -0.99


def test_evaluate_predictions_returns_result():
    result = evaluate_predictions([0.1, -0.1, 0.2], [0.2, -0.2, 0.1])
    assert isinstance(result, ModelEvaluationResult)
    assert result.sample_count == 3


def test_run_model_lab_insufficient_data_does_not_crash():
    result = run_model_lab(build_research_dataset("510300.SH", make_bars(count=2), horizon=1))
    assert isinstance(result, ModelLabResult)
    assert not result.success


def test_run_model_lab_with_data_returns_result():
    result = run_model_lab(build_research_dataset("510300.SH", make_bars(count=20), horizon=1))
    assert isinstance(result, ModelLabResult)
    assert result.predictions
    assert result.evaluation is not None


def test_research_scores_from_model_predictions_generates_scores():
    result = run_model_lab(build_research_dataset("510300.SH", make_bars(count=20), horizon=1))
    scores = research_scores_from_model_predictions(result.predictions)
    assert scores
    assert isinstance(scores[0], ResearchScore)


def test_research_score_enters_build_candidates_from_research_scores():
    result = run_model_lab(build_research_dataset("510300.SH", make_bars(count=20), horizon=1))
    scores = research_scores_from_model_predictions(result.predictions)
    candidates = build_candidates_from_research_scores(scores, target_percent=0.1)
    assert candidates
    assert candidates[0].symbol == "510300.SH"


def test_model_lab_candidates_enter_generate_etf_rotation_intents_dry_run():
    result = run_model_lab(build_research_dataset("510300.SH", make_bars(count=20), horizon=1))
    scores = research_scores_from_model_predictions(result.predictions)
    candidates = build_candidates_from_research_scores(scores, target_percent=0.1)
    intents = generate_etf_rotation_intents(candidates, top_n=1, capital=100000)
    assert intents
    assert intents[0].dry_run is True
    assert intents[0].symbol == "510300.SH"
