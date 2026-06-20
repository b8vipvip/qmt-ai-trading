# 阶段六十三：本地控制台报告详情页与过滤层

Stage63 是本地控制台报告详情页与过滤层，正式处于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage63 基于 Stage62 本地控制台报告读取层，只提供本地只读报告详情和过滤材料，供后续 Stage64 本地控制台概览面板层使用。

## 安全边界

- Stage63 不等于实盘授权。
- Stage63 只提供本地只读报告详情和过滤材料。
- Stage63 不提供下单接口。
- Stage63 不提供账户/持仓/订单/成交查询接口。
- Stage63 不调用 `xttrader`，不导入 `XtQuantTrader`。
- Stage63 不真实下单。
- Stage63 不查询资金/持仓/订单/成交。
- Stage63 不真实发送通知。
- Stage63 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW` 只表示本地控制台报告详情页与过滤层材料可供人工复核，不代表实盘授权。

## 详情视图路由索引

- `/dashboard/detail`
- `/reports/detail`
- `/reports/stage62/detail`
- `/reports/stage61/detail`
- `/reports/stage60/detail`
- `/reports/stage59/detail`
- `/reports/stage58/detail`
- `/reports/stage57/detail`
- `/reports/stage56/detail`
- `/reports/stage55/detail`
- `/filters/stage`
- `/filters/status`
- `/filters/severity`
- `/filters/warnings`
- `/filters/blocking-reasons`
- `/manifest/detail`
- `/validation/latest/detail`
- `/safety/detail`
- `/api-capabilities/detail`
- `/scheduler-preview/detail`

## 禁止视图和动作

禁止 `/order`、`/orders`、`/trade`、`/execute`、`/approve`、`/live`、`/notify`、`/account`、`/positions`、`/assets`。本地控制台不能绕过 Risk Gate，不能绕过 Human Approval，不能直接访问 QMT，不能自动 approve。

## validation log 摘要修复

Stage63 的 validation log 读取支持 UTF-8、UTF-8-SIG、UTF-16LE、UTF-16BE 自动识别；如果摘要出现大量 NUL 字符，会按 UTF-16LE/UTF-16BE 重新解码并在输出前清理 NUL。读取只截取 latest validation log 的头尾有限片段，读取失败输出 WARN/UNAVAILABLE，不崩溃。

## 下一阶段

Stage64 是本地控制台概览面板层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。Stage64 基于 Stage63 生成阶段状态卡片、最新 validation 状态卡片、warning/blocking reason 统计、manifest/hash 状态卡片、scheduler preview 状态卡片和 safety boundary 状态卡片。
