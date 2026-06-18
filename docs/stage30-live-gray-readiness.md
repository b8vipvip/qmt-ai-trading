# 阶段三十：小资金实盘灰度准备

## 阶段三十目标

阶段三十建立 Live Gray Readiness 准备框架，用于生成小资金灰度前的配置、检查、清单与报告。当前阶段默认 `live_enabled=False`、默认 `gray_enabled=False`、默认 `NO_GO`。

## 为什么需要小资金实盘灰度准备

在 Risk Gate、Human Approval、Paper Trading、Live Readiness Audit、Monitoring、Agent Research 之后，需要一个独立准备层把白名单标的、小资金上限、单笔金额上限、仓位上限、证据链和人工复核事项集中输出，供未来人工判断是否进入极小资金灰度。

## 为什么本阶段仍不启用实盘

本阶段只生成 readiness report，不开启实盘，不调用 QMT 交易接口，不调用 `xttrader`，不查询真实资金/持仓/订单/成交，不真实发送通知，不下单。

## 核心模型

- `LiveGrayConfig`：配置 live/gray 开关、资金上限、仓位上限、白名单和证据要求。
- `LiveGrayCheck`：单项只读检查，包含 scope、status、severity、evidence 和 remediation。
- `LiveGrayReadinessReport`：汇总 decision、checks、summary、blocked reasons、manual review checklist 和 safety note。

## 决策含义

- `NO_GO`：默认状态，live 或 gray 未启用，或当前仅准备不推进。
- `BLOCKED`：存在 FAIL 或 CRITICAL，必须阻断。
- `READY_FOR_MANUAL_REVIEW`：仅表示可进入人工复核候选；不代表 GO，不代表实盘授权。

## 白名单与资金上限

白名单不能为空；任何非白名单 TradeIntent 都会 FAIL。默认小资金上限为总额 5000、单笔 1000、单标的权重 0.1、组合权重 0.2，超出即 FAIL。

## 证据要求

Human Approval、Risk Gate、Paper Trading、Live Readiness Audit、Monitoring、Agent Research、Circuit Breaker、Quality 均为灰度前必需证据。缺失时 FAIL；Circuit Breaker OPEN 必须 FAIL；Quality UNKNOWN 只有显式允许人工复核时才 WARN。

## run_live_gray_readiness.py 使用方式

```powershell
py scripts/run_live_gray_readiness.py --output live_gray_reports_stage30/live_gray_readiness.md --json-output live_gray_reports_stage30/live_gray_readiness.json --allowed-symbols 510300.SH,510500.SH --max-total-capital 5000 --max-single-order-value 1000 --max-symbol-weight 0.1 --max-portfolio-weight 0.2
```

## run_daily_pipeline.py 使用方式

```powershell
py scripts/run_daily_pipeline.py --enable-live-gray-readiness --live-gray-output-dir live_gray_reports_stage30 --live-gray-allowed-symbols 510300.SH,510500.SH --live-gray-max-total-capital 5000 --live-gray-max-single-order-value 1000 --live-gray-max-symbol-weight 0.1 --live-gray-max-portfolio-weight 0.2
```

## scheduled pipeline 参数说明

`run_scheduled_daily_pipeline.py` 和 `register_daily_pipeline_task.py` 支持 `--enable-live-gray-readiness`、`--live-gray-output-dir`、`--live-gray-allowed-symbols`、资金与仓位上限参数、`--live-gray-enabled`。计划任务默认不包含 `--live-enabled`。

## 安全边界

当前阶段不调用 QMT 交易接口、不调用 `xttrader`、不真实发送通知、不下单。`--live-enabled` 默认不使用；即使误传，也只能导致 BLOCKED/NO_GO，不能开启实盘。

## 下一阶段计划

阶段三十一：UI / Dashboard。目标是在后端安全链路稳定后建立本地只读 dashboard，展示报告、审批状态、风险状态、缓存覆盖率、监控事件、Agent Research Memo 和 Live Gray Readiness。
