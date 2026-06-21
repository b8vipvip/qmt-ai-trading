# Stage80：因子候选池到 Strategy Engine dry-run TradeIntent 联调层

Stage80 将 Stage79 的 `factor_candidates` 接入 Strategy Engine，生成 `strategy_signals` 和 dry-run `TradeIntent`，再进入 Risk Gate dry-run 校验。全链路仍然是 shadow / dry-run：不接实盘、不下单、不查询真实账户、不调用 `xttrader`，也不自动 approve。

`factor_candidates` 按 rank / score 排序后，Strategy Engine 选择 `max_positions` 内候选，保留 `reasons` 与 `risk_flags`，并强制补齐 `mock_data`、`not_live_trading`。信号只表示 `BUY_CANDIDATE_DRY_RUN`，不是交易建议。

TradeIntent 由信号转换而来，统一标记 `source=factor_strategy_stage80`、`dry_run=True`、`quantity=0`、`requires_risk_gate=True`、`requires_human_approval=True`、`auto_approve=False`。这些意图只能进入 Risk Gate dry-run，不会触达 QMT Gateway。

Risk Gate dry-run 对每个 TradeIntent 生成 `REJECTED_DRY_RUN` 决策，并写明阻断原因：mock 候选池不能作为实盘依据、未人工审批、缺少实盘授权。`mock_data / not_live_trading` 必须保留，不能作为实盘依据。

Stage80 同时真实修复 `run_qmt_tasks.ps1` 验收日志落盘。`scripts/install_run_qmt_tasks_logging.ps1` 从仓库脚本目录定位父级 `D:\AI\run_qmt_tasks.ps1`，写入 `Start-Transcript` / `Stop-Transcript` 与 fallback 日志逻辑。日志路径为 `validation_logs/stage*_validation_*.log`，成功或失败都会在最后打印“验收日志已保存到”。

下一阶段建议进入 Stage81：TradingAgents 多 Agent 投研工作台与模型用途映射联调层，把 Stage78 AI 模型配置接入 TradingAgents；仍然不是实盘，不真实下单。
