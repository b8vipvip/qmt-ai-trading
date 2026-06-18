# 阶段三十一：UI / Dashboard

## 阶段三十一目标

阶段三十一在后端安全链路稳定后增加本地只读 Dashboard。Dashboard 用于汇总 Daily Pipeline 报告、Data Source / Cache Quality、Candidates、TradeIntents、RiskDecision、Portfolio Plan、Monitoring / Alerts / Circuit Breaker、Agent Research Memo、Live Gray Readiness、Human Approval 和 Paper Trading 状态文件。

## 为什么 UI / Dashboard 要后置

UI 位于 Reporting、Monitoring、Agent Research、Live Gray Readiness 之后。只有在 Risk Gate、Human Approval、Paper Trading、Monitoring、Agent Research 和 Live Gray Readiness 已具备后，UI 才能作为只读观察层展示这些证据，避免 UI 被误解为交易入口。

## Dashboard 只读原则

Dashboard 是 read-only dashboard，不是 order entry system。Dashboard 不提供下单按钮，不触发 Approval，不触发 Paper Trading，不触发 Live Trading，不调用 QMT 交易接口，不调用 `xttrader`，不真实发送通知，不下单，不读取 `.env`、token、key、password、secret。

## 核心模型

- `DashboardConfig`：定义本地报告目录、输出路径、包含哪些 section、`read_only=True` 和非敏感 metadata。
- `DashboardData`：记录生成时间、标题、sections、source paths、warnings、safety note 和 metadata。
- `DashboardSection`：记录 section_id、title、status、summary、html、source_path 和 metadata。

## 展示内容

Dashboard 展示 Daily Pipeline、Cache Quality、Candidates、TradeIntents、RiskDecision、Portfolio、Monitoring、Agent Research、Live Gray Readiness、Approval、Paper 的本地报告或状态文件。文件缺失时生成 EMPTY section，不崩溃。

## build_dashboard.py 使用方式

```powershell
py scripts/build_dashboard.py --output dashboard_stage31/index.html --report-dir reports --monitoring-dir monitoring_reports_stage30 --agent-dir agent_reports_stage30 --live-gray-dir live_gray_reports_stage30 --approval-dir approvals --paper-dir paper_orders --title "QMT AI Trading Dashboard"
```

该脚本只读取本地报告目录并生成单文件 HTML，不调用外部网络、不调用 QMT、不调用 `xttrader`、不下单。

## run_dashboard_preview.py 使用方式

```powershell
py scripts/run_dashboard_preview.py --dashboard dashboard_stage31/index.html --print-path-only
```

默认只打印本地路径；`--serve` 只用 Python 标准库启动 dashboard 所在目录的只读静态文件服务，不提供 API 或修改接口。

## run_daily_pipeline.py --build-dashboard 使用方式

```powershell
py scripts/run_daily_pipeline.py --build-dashboard --dashboard-output dashboard_stage31/daily_dashboard.html --dashboard-title "QMT AI Trading Daily Dashboard"
```

开启后只在 pipeline 完成后生成 dashboard HTML，不改变 TradeIntent、RiskDecision、Approval、PaperOrder 或 LiveGrayReadiness。

## scheduled pipeline dashboard 参数说明

`run_scheduled_daily_pipeline.py` 支持 `--build-dashboard`、`--dashboard-output`、`--dashboard-report-dir`、`--dashboard-title` 并透传给 daily pipeline。`register_daily_pipeline_task.py` 支持 `--build-dashboard`、`--dashboard-output`、`--dashboard-title`，dry-run 命令可包含 dashboard 生成参数。

## 安全边界

UI 不得作为交易绕过入口，不提供“提交订单 / 实盘下单 / 自动批准 / 绕过风控”按钮。当前阶段不调用 QMT 交易接口、不调用 `xttrader`、不真实发送通知、不下单。

## 下一阶段计划

阶段三十二：运行手册 / 部署手册 / 总体验收。目标是把本地运行、数据缓存、Daily Pipeline、Scheduler、Approval、Paper、Monitoring、Agent、Live Gray、Dashboard 全链路整理成操作手册和总体验收清单。阶段三十二仍不实盘、不调用 `xttrader`、不真实下单。
