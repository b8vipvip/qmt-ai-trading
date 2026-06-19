# 阶段五十五：QMT 实机 dry-run 环境最终校准

Stage55 是 QMT 实机 dry-run 环境最终校准，属于 Stage53-60：灰度前真实数据 / QMT dry-run / 小资金灰度准备，不属于 Stage61-75 UI 产品化阶段。

## 安全边界

- Stage55 不等于实盘授权。
- Stage55 只允许 `xtquant.xtdata` 行情能力。
- Stage55 不调用 `xttrader`，不导入 `XtQuantTrader`。
- Stage55 不真实下单。
- Stage55 不查询资金、持仓、订单、成交。
- Stage55 不真实发送通知。
- `READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW` 只表示 QMT 实机 dry-run 环境校准材料可供人工复核，不代表实盘授权。

## 输出材料

默认输出目录为 `qmt_dryrun_calibration_stage55/`，运行产物不提交：

- `qmt_dryrun_calibration.md` / `qmt_dryrun_calibration.json`
- `xtdata_capability.md` / `xtdata_capability.json`
- `etf_whitelist_calibration.md` / `etf_whitelist_calibration.json`
- `next_real_cache_quality_plan.md` / `next_real_cache_quality_plan.json`

## Roadmap / UI 产品化路线复核

本阶段继续检查完整 Stage1-75 工程阶段计划和 Stage61-75 UI 产品化计划。UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。本阶段不提前开始 UI 开发。

## 下一阶段预告

Stage56 仍不能直接实盘，只能做真实缓存质量复核与长期样本补齐。Stage56 只允许使用 `xtdata` 或本地缓存，不得调用 `xttrader`，不得查询真实资金、持仓、订单、成交，不得下单。
