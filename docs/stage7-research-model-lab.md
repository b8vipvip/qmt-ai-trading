# 阶段七：Research Model Lab

阶段七新增轻量 Research Model Lab，用于标准化 ETF / 指数研究中的样本构造、标签构造、训练验证切分和基础模型评价。该层只输出研究结果、评分或候选，不连接真实实盘、不连接 QMT、不直接下单、不做 UI。

## Model Lab 职责

- 将 Data Hub 已提供的 `MarketBar` 转换为研究样本。
- 构造特征矩阵和 forward return 标签。
- 按时间顺序拆分 train/test 数据集。
- 运行轻量 baseline 模型并输出 `ModelPrediction`。
- 计算 IC、RankIC、方向准确率等研究指标。
- 通过 adapter 可选转换为 `ResearchScore`，再由 Strategy Engine 转换为 `ETFCandidate` 或 dry-run `TradeIntent`。

## 样本构造：features / labels

`qmt_ai_trading.research.dataset` 提供以下数据结构：

- `FeatureRow`：单个 symbol、datetime 下的一组特征。
- `LabelRow`：单个 symbol、datetime 下的 forward return 标签。
- `ResearchDataset`：特征和标签集合。
- `TrainTestSplit`：训练集和测试集拆分结果。

当前 `build_feature_rows_from_bars(...)` 使用纯 Python 从本地 K 线构造基础特征，例如收盘价、开收盘收益、日内高低区间、相邻收盘收益和成交量变化。

## 标签：forward_return

`build_forward_return_labels(...)` 以 `horizon` 为前瞻窗口构造：

```text
forward_return = (future_close - current_close) / current_close
```

空 bars、无效价格或数据不足时不抛不可控异常，而是返回空列表，并可在 `ResearchDataset.metadata` 中记录 reason。

## 切分：train/test

`split_dataset_by_ratio(...)` 按样本顺序进行轻量 train/test 拆分，默认训练集比例为 0.7。该拆分不打乱时间顺序，适合 ETF / 指数这类时间序列研究的基础验证。

## 指标：IC / RankIC / directional accuracy

`qmt_ai_trading.research.metrics` 提供：

- `pearson_corr(...)`：纯 Python Pearson correlation。
- `spearman_corr(...)`：纯 Python 排名和 Spearman correlation，不依赖 scipy。
- `compute_ic(...)`：使用 Pearson correlation 表示 IC。
- `compute_rank_ic(...)`：使用 Spearman correlation 表示 RankIC。
- `compute_directional_accuracy(...)`：预测方向与标签方向一致的比例。
- `evaluate_predictions(...)`：返回 `ModelEvaluationResult`。

输入为空或长度不匹配时返回 0 或失败 reason，不抛不可控异常。

## 轻量 baseline

`qmt_ai_trading.research.model_lab` 提供：

- `train_simple_linear_model(...)`
- `predict_with_simple_linear_model(...)`
- `run_model_lab(...)`

当前只实现纯 Python 简单线性 baseline：对每个特征计算与 forward return 的一元斜率并组合预测。该实现参考 Qlib / vnpy.alpha 的研究分层思想，但不整体引入 Qlib、vn.py 或 TradingAgents 源码，也不把 pandas、numpy、scikit-learn 作为硬依赖。

## 与 Research Score / ETF Strategy 的关系

`research_scores_from_model_predictions(...)` 可将 Model Lab 的 `ModelPrediction` 转换为 `ResearchScore`。ETF Rotation Strategy 可以继续使用既有 `build_candidates_from_research_scores(...)`，或可选使用 Model Lab adapter。

Model Lab 输出不会直接下单。Strategy 使用 Model Lab 输出时，仍必须输出 `TradeIntent`，再经过 Risk Gate 和 QMT Gateway。任何真实执行仍在 Gateway 层之后受安全开关和风控约束。

## 后续扩展方向

- 接入 LightGBM adapter。
- 接入 Qlib adapter。
- 扩展 Alpha158 / Alpha101 风格因子。
- 增加更多时间序列交叉验证方式。
- 增加多标的横截面 RankIC 分析。

上述扩展应继续保持 adapter 化，不直接侵入 Strategy / Risk / Gateway，也不得绕过 Risk Gate 或直接调用真实 QMT 下单。
