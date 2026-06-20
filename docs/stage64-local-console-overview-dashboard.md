# 阶段六十四：本地控制台概览面板层

Stage64 是本地控制台概览面板层，正式进入 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。它基于 Stage63 本地控制台报告详情页与过滤层，生成本地只读概览面板材料、dashboard card index、stage status cards、warning/blocking stats、manifest/hash status、scheduler preview status、safety boundary status 与 Stage65 控制台 shell 计划。

## 安全边界

- Stage64 不等于实盘授权。
- Stage64 只提供本地只读概览面板材料。
- Stage64 不提供下单接口。
- Stage64 不提供账户/持仓/订单/成交查询接口。
- Stage64 不调用 `xttrader`，不导入 `XtQuantTrader`。
- Stage64 不真实下单。
- Stage64 不查询资金/持仓/订单/成交。
- Stage64 不真实发送通知。
- Stage64 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW` 只表示本地控制台概览面板层材料可供人工复核，不代表实盘授权。

## Dashboard Cards

- Stage Status Card：当前阶段、最近通过阶段、Stage55-63 总览、critical/warning/blocking reason 数量。
- Latest Validation Card：latest validation log 路径、状态、encoding、NUL 与 replacement char 清理状态。
- Warning / Blocking Stats Card：按 stage 和 severity 统计 warning、blocking reason、critical。
- Manifest / Hash Card：manifest item count、sha256 完整性说明、缺失项、read_only=True。
- Scheduler Preview Card：register preview only、no_task_registered=True、dry_run_only=True、no_trade_authorization=True。
- Safety Boundary Card：read_only=True、dry_run_only=True、no_trade_authorization=True、no xttrader、no account query、no order、no real notification。
- API Capability Card：Stage61 API Gateway 只读能力概览。
- Detail / Filter Card：Stage63 detail/filter 只读能力概览。

## Dashboard Route Index

- `/dashboard/overview`
- `/dashboard/stage-status`
- `/dashboard/latest-validation`
- `/dashboard/warnings`
- `/dashboard/blocking-reasons`
- `/dashboard/manifest`
- `/dashboard/scheduler-preview`
- `/dashboard/safety-boundary`
- `/dashboard/api-capability`
- `/dashboard/detail-filter`
- `/dashboard/next`

禁止 `/order`、`/orders`、`/trade`、`/execute`、`/approve`、`/live`、`/notify`、`/account`、`/positions`、`/assets`。

## Validation Log 解码

Stage64 validation log reader 优先 UTF-8-SIG，再 UTF-8，再 UTF-16 / UTF-16LE / UTF-16BE，最后才使用 UTF-8 replacement fallback。摘要只读取 latest validation log 的头尾有限片段，输出前剥离 BOM、清理 NUL 字符；如果仍检测到 U+FFFD 或 `��`，记录 warning 但不崩溃。

## 下一阶段

Stage65 是本地控制台 shell / 静态页面骨架层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。Stage65 基于 Stage64 生成页面布局、导航、只读数据注入点、dashboard card 占位、报告列表占位、详情过滤占位和安全边界固定展示。
