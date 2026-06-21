# Stage79：因子研究工作台与选股评分可视化层 + 验收日志落盘修复

Stage79 建设 Research / Factor Engineering 前端可视化模块，并追加本地总控脚本验收日志落盘修复模板。

## 因子工程链路

Data Hub 提供 ETF universe 与 MarketBar 数据；Stage79 默认使用离线 mock 样本，通过 `factor_engine` 生成动量、波动率、成交量、回撤、均线趋势等特征。结果明确标记 `data_source=mock`、`quality_level=sample_offline`、`not_live_trading=true`。

## 因子配置与候选池评分

每个因子包含 window / lookback / weight / direction / winsorize / standardize / neutralize / enabled。权重与方向共同影响综合分，negative 因子会反向计分，候选池按 `composite_score` 排名。

## IC / RankIC

IC 用于观察因子值与后续收益的线性相关性，RankIC 用于观察排序相关性。Stage79 的 mock 样本只用于工作流验收，不构成投资建议。

## 候选池生成

`candidate_builder` 从 `factor_results` 提取 rank、symbol、score、reasons、risk_flags，形成后续 Strategy Engine 可消费的候选池。

## 后续 Strategy Engine 使用方式

Stage80 建议把 Stage79 的 `factor_candidates` 接到 Strategy Engine，生成 dry-run TradeIntent，再继续经过 Risk Gate 校验；仍不进入实盘。

## 验收日志落盘修复

由于当前环境无法访问 Windows 侧 `D:\AI\run_qmt_tasks.ps1`，仓库提供 `scripts/run_qmt_tasks_with_validation_log.ps1` 模板。复制覆盖到 `D:\AI\run_qmt_tasks.ps1` 后，交互输入阶段号会生成 `D:\AI\qmt\validation_logs\stage<阶段号>_validation_<yyyyMMdd_HHmmss>.log`。

## 安全边界

Stage79 不接实盘、不下单、不查询真实账户、不调用 xttrader、不导入 XtQuantTrader、不真实通知、不自动 approve、不绕过 Risk Gate / Human Approval。
