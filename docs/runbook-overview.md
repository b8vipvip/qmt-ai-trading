# 运行手册总览

## 项目定位
qmt-ai-trading 是个人本地 A股 / ETF / QMT / AI Agent 辅助量化系统，默认模式为 dry-run / shadow / paper only。当前不实盘、不调用 xttrader、不真实下单。

## 核心链路
`ETF Universe -> Universe Warmup -> LocalBarStore -> Cached Research -> Cached ETF Rotation -> Portfolio Plan -> TradeIntent -> Risk Gate -> Human Approval -> Paper Trading -> Monitoring -> Agent Research -> Live Gray Readiness -> Dashboard`

## 模块作用
- ETF Universe / Universe Warmup：维护并预热 ETF 本地行情缓存。
- LocalBarStore：保存本地历史 bar，运行产物不提交。
- Cached Research / Cached ETF Rotation：只读缓存生成评分和 dry-run TradeIntent。
- Portfolio Plan / Risk Gate：生成组合计划并执行风控闸门。
- Human Approval / Paper Trading：人工审批与本地 paper 生命周期模拟。
- Monitoring / Agent Research / Live Gray Readiness / Dashboard：只读观察、解释、灰度准备和展示层。

## 常用命令入口
- `py scripts/warmup_etf_universe.py --provider mock --cache-root market_data_test_stage32`
- `py scripts/run_daily_pipeline.py --data-source-mode cached_real_first --allow-mock-fallback --build-dashboard`
- `py scripts/run_final_acceptance.py --output final_acceptance_stage32/final_acceptance.md --json-output final_acceptance_stage32/final_acceptance.json`
- `py scripts/run_full_dry_run_smoke.py --cache-root market_data_test_stage32 --output-dir smoke_reports_stage32`

## 安全边界
当前阶段仍不实盘、不调用 QMT 交易接口、不调用 xttrader、不查询真实资金/持仓/订单/成交、不真实发送通知、不自动 approve、不自动 paper submit、不自动 live submit、不真实下单。

## 当前阶段状态
阶段一到阶段三十一已完成；阶段三十二为运行手册 / 部署手册 / 总体验收。
