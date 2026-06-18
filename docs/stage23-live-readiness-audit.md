# 阶段二十三：实盘前安全审计

## 阶段二十三目标

阶段二十三建立 Live Readiness Audit（实盘前安全审计）框架，在 Paper Trading 之后、任何 QMT 实机数据联调和未来实盘之前，生成结构化 go/no-go 审计报告。当前阶段默认输出 `NO_GO`，只做静态项目文件、配置、文档和本地测试结果检查。

## 为什么需要实盘前安全审计

系统已经具备 Risk Gate、Human Approval 和 Paper Trading，但这些能力不能自动等同于实盘授权。实盘前安全审计用于确认关键安全边界仍存在、运行产物不会被提交、live trading 默认关闭、代码没有明显绕过风控或直接触达真实下单接口。

## 核心模型

- `AuditCheckResult`：单项审计结果，包含 check_id、name、status、severity、message、evidence、remediation 和 metadata。
- `AuditReport`：完整审计报告，包含 report_id、created_at、project_root、decision、summary、统计计数、检查列表和 metadata。
- `LiveReadinessPolicy`：审计策略，定义是否要求 roadmap、architecture、Risk Gate、Human Approval、Paper Trading、sync script 保护、live disabled、禁止 xttrader import、禁止直接下单调用、gitignore runtime dirs 和敏感模式检查。

## 默认 NO_GO 的原因

当前阶段只建立审计框架，不开启实盘。`LiveReadinessPolicy.allow_go` 默认是 `False`，因此即使所有检查通过，默认结论仍是 `NO_GO`，并在报告中说明 `GO disabled by policy`。只有未来经过审计的阶段显式允许 `allow_go=True` 且无 FAIL/CRITICAL 时，才可能输出 `GO`。

## run_live_readiness_audit.py 使用方式

```powershell
py scripts/run_live_readiness_audit.py --project-root .
py scripts/run_live_readiness_audit.py --project-root . --output reports/live_readiness_audit.md --json-output reports/live_readiness_audit.json
py scripts/run_live_readiness_audit.py --project-root . --allow-go
```

默认输出 Markdown 到 stdout；传入 `--output` 会写 Markdown；传入 `--json-output` 会写 JSON。脚本不会调用 QMT、不会调用 `xttrader`、不会下单。

## 审计项说明

- 检查 roadmap / architecture 是否存在。
- 检查 roadmap 是否包含阶段二十三“实盘前安全审计”和阶段二十四“QMT 实机数据联调与真实缓存质量验证”。
- 检查 architecture 是否说明 Live Readiness Audit、安全边界、默认 NO_GO 和不下单。
- 检查 `scripts/sync_all.ps1` 存在且不应被本阶段修改。
- 检查 `.gitignore` 是否忽略 approvals、paper_orders、market_data、data_cache、reports、logs 和相关 JSON 运行产物。
- 检查 live trading 默认关闭。
- 检查当前代码没有直接 import `xttrader`。
- 检查策略、research、pipeline、agents 不直接调用真实下单函数。
- 检查 Risk Gate、Human Approval、Paper Trading 关键边界存在。
- 检查 tracked files 中没有明显敏感赋值模式；如发现只输出文件路径和规则名，不输出敏感值。
- 检查 runtime dirs 未被 git 跟踪。

## GO / NO_GO 的含义

`NO_GO` 表示不得进入实盘或更接近实盘的交易执行阶段。`GO` 仅表示审计条件在特定策略下通过，不代表自动允许交易，也不代表已开启 live trading。

## 为什么 audit report 不是交易授权

Audit report 是安全检查产物，不是人工交易授权、不是券商授权、不是账户授权、不是策略上线审批。未来即使报告为 `GO`，仍必须经过明确的后续阶段、配置开关、Risk Gate、Human Approval 和 QMT Gateway 边界。

## 当前阶段安全边界

当前阶段不调用 QMT、不调用 `xttrader`、不实盘、不下单、不查询资金/持仓/订单/成交、不真实发送通知。审计只读项目文件、配置、文档和本地测试结果。

## 阶段二十三通过后的下一阶段计划

阶段二十四：QMT 实机数据联调与真实缓存质量验证。目标是在真实 MiniQMT / xtquant 环境中小范围拉取 ETF 历史数据，校验字段、日期、复权、成交量、缺失值、重复值和缓存质量。阶段二十四仍不实盘、不调用 `xttrader`、不真实下单。
