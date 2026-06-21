# 阶段七十七：业务控制台 MVP 与任务编排 API 层

Stage77 是一次路线纠偏：它不再继续美化“开发进度验收台 / 报告浏览台”，而是交付本系统真正的本地业务控制台 MVP。

## 能力范围

- 前端可以触发白名单 dry-run 后端任务。
- 前端可以查看任务状态、日志摘要、输出 artifacts 和报告摘要。
- 前端可以查看只读行情 / 数据质量 / 选股 / Agent / 策略 / 回测 / 风控模块入口。
- 后端新增 `qmt_ai_trading.console_api`，仅作为本地任务编排 API，默认 `127.0.0.1:8768`。
- 所有任务来自 `task_registry` 白名单，不接受前端传入任意 command、script_path 或 path。

## 安全边界

Stage77 仍然是 dry-run / shadow / read-only：

- Stage77 不接实盘。
- Stage77 不查询真实账户、资金、持仓、订单、成交。
- Stage77 不真实下单。
- Stage77 不调用 xttrader / XtQuantTrader。
- Stage77 不绕过 Risk Gate。
- Stage77 不自动 approve。
- Stage77 不开放 `0.0.0.0`、公网或 LAN。

## 启动方式

静态前端：

```powershell
cd D:\AI\qmt\local_console_app_stage77
py -m http.server 8767 --bind 127.0.0.1
```

业务控制台 API：

```powershell
cd D:\AI\qmt
py scripts\run_console_api.py --host 127.0.0.1 --port 8768 --static-dir local_console_app_stage77
```

## Stage78 预告

Stage78 才回到“实盘前安全审计重启与真实数据质量复核层”。Stage78 仍然不是实盘；它将基于 Stage77 控制台 MVP 复核真实缓存质量、QMT xtdata 稳定性、Paper Trading 成熟度、异常监控、live config 多重确认和数据质量报告。
