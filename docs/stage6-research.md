# 阶段六：Research 层标准化

## Research 层职责

Research 层负责把 Data Hub 已经提供的本地行情数据转换为可验证、可复用、结构化的研究结果。当前阶段只处理调用方传入的数据，不连接网络、不连接 QMT、不读取账户、不生成订单。

Research 输出用于辅助 Strategy Engine 做候选评分，不能绕过 Risk Gate，也不能直接调用 QMT Gateway。

## 因子计算职责

`qmt_ai_trading.research.factors` 提供轻量因子接口：

- `FactorValue`：单个 symbol 的单个因子观测值。
- `FactorResult`：单个 symbol 的因子计算结果集合。
- `compute_momentum_factor(...)`：基于收盘价计算动量。
- `compute_volatility_factor(...)`：基于收盘收益率计算波动率。
- `compute_volume_factor(...)`：基于成交量计算均量。
- `compute_simple_score(...)`：对多个因子做简单加权合成。
- `rank_factor_results(...)`：按 score 对因子结果排序。

当数据不足时，因子函数返回 `eligible=False` 和明确 `reason`，不抛出不可控异常。

## scoring 输出职责

`qmt_ai_trading.research.scoring` 提供统一研究评分：

- `ResearchScore`：面向 Strategy Engine 的结构化研究评分。
- `score_symbol_from_bars(...)`：对单个 symbol 的 MarketBar 列表评分。
- `score_etf_universe(...)`：对多个 ETF symbol 的 bars 字典批量评分。
- `normalize_score(...)`：把原始因子值映射到 0-100 区间。
- `combine_factor_scores(...)`：对多个标准化因子分做加权合成。

`ResearchScore` 只表达研究层判断，不表达下单意图。

## report 输出职责

`qmt_ai_trading.research.report` 提供研究摘要输出：

- `ResearchReport`：结构化研究报告。
- `build_research_report(...)`：由 ResearchScore 生成报告对象。
- `format_research_report_text(...)`：生成可读文本摘要。

报告文本只作为辅助分析，不包含投资承诺，不使用“保证收益”等表达。

## 当前阶段边界

阶段六暂不接完整 Qlib / vn.py 依赖，不引入 UI，不连接实盘，不接真实 QMT 下单，不复制 TradingAgents / Qlib / vn.py 源码。

后续可以借鉴 Qlib / vnpy.alpha 的 Alpha158、Alpha101、LightGBM、IC、RankIC 等思想，逐步扩展离线研究、回测评估和模型评分能力。

## 与 Strategy / Risk / Gateway 的关系

Strategy Engine 通过 `ResearchScore` 使用研究结果，例如 ETF 轮动策略可以使用 `build_candidates_from_research_scores(...)` 将研究评分转换为 `ETFCandidate`。

Research 不能直接下单；Strategy 生成的 `TradeIntent` 仍必须经过 Risk Gate 审核，最终执行仍必须经过 QMT Gateway。
