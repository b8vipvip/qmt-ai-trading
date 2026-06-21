# Stage77 任务白名单

- `data_cache_check`：本地缓存质量检查 / DATA / dry-run=True
- `qmt_data_diagnostics_readonly`：QMT 行情只读诊断 / DATA / dry-run=True
- `market_snapshot_readonly`：只读行情快照 / DATA / dry-run=True
- `research_score_etf`：ETF 研究评分 / RESEARCH / dry-run=True
- `model_lab_evaluate`：模型实验评估 / RESEARCH / dry-run=True
- `factor_scan`：多因子扫描 / RESEARCH / dry-run=True
- `etf_rotation_candidates`：ETF 轮动候选 / STRATEGY / dry-run=True
- `strategy_dry_run_signals`：策略 dry-run 信号 / STRATEGY / dry-run=True
- `daily_pipeline_dry_run`：日线流水线 dry-run / STRATEGY / dry-run=True
- `agent_research_brief`：Agent 投研简报 / AGENTS / dry-run=True
- `agent_risk_review`：Agent 风险复核 / AGENTS / dry-run=True
- `agent_portfolio_review`：Agent 组合复核 / AGENTS / dry-run=True
- `shadow_replay_backtest`：Shadow Replay 回测 / BACKTEST / dry-run=True
- `backtest_report`：回测报告生成 / BACKTEST / dry-run=True
- `risk_gate_dry_run_check`：Risk Gate dry-run / RISK / dry-run=True
- `live_readiness_blockers_review`：实盘阻断项复核 / RISK / dry-run=True
- `generate_daily_report`：生成日报 / REPORT / dry-run=True
- `list_latest_reports`：最新报告列表 / REPORT / dry-run=True