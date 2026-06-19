# 阶段四十：实盘开关隔离与最终红线复核（仍默认关闭）

阶段四十新增 Red-line Review 层，用于在 Final Authorization Package 之后生成 review-only / dry-run 的实盘开关隔离与红线复核报告。它不启用实盘、不调用 QMT、不调用 xttrader、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。

## 为什么需要

在任何未来单独阶段进入极小资金灰度前，必须先统一扫描 CLI、scheduler preview、Dashboard、文档和本地代码边界，确认危险入口、配置开关、计划任务参数、真实通知和交易 API 均被隔离。

## 模型

- `RedlineReviewConfig`：定义 repo root、扫描 include/exclude、scheduler dry-run、dashboard read-only、禁止敏感文件和禁止 xttrader/QMT/账户查询/真实通知/execute-live 等要求。
- `RedlineFinding`：记录分类、状态、严重级别、路径、行号、marker、阻断说明和修复建议。
- `RedlineReviewReport`：包含 decision、findings、blocked_reasons、warnings、summary、safety_note 和 metadata。

## 决策含义

- `BLOCKED`：发现 CRITICAL/FAIL 红线，必须阻断。
- `NEED_MORE_EVIDENCE`：只有 WARN/INFO，但仍需人工补充证据。
- `READY_FOR_REDLINE_REVIEW`：材料可交人工红线复核；不代表允许实盘。

## 红线边界

- live switch red-line：`--live-enabled`、`live_enabled=True` 等必须记录，执行型入口阻断。
- execute switch red-line：`--execute-live`、`--execute` scheduler preview 阻断。
- notification red-line：`--real-send`、`requests.post`、`smtp`、`sendMessage`、`webhook` 真实发送入口阻断。
- QMT / xttrader boundary：不调用 QMT 交易接口，不调用 xttrader。
- account query boundary：不查询账户、资金、持仓、订单、成交。
- scheduler isolation：本阶段 register 仍是 dry-run preview。
- dashboard isolation：Dashboard 只读展示，不提供下单按钮。
- sensitive file / runtime artifact boundary：不读取 `.env` 内容，只检测存在性；运行产物目录不提交。

## 使用方式

```bash
py scripts/run_redline_review.py --output redline_review_stage40/redline_review.md --json-output redline_review_stage40/redline_review.json --repo-root .
```

```bash
py scripts/run_daily_pipeline.py --data-source-mode mock --enable-redline-review --redline-review-output-dir redline_review_stage40
```

Scheduled pipeline / register task 可透传 `--enable-redline-review` 与 `--redline-review-output-dir`，但本阶段禁止真实注册和执行型实盘开关。

Dashboard 增加 Red-line Review section，只读读取最新 Markdown / JSON；文件不存在时返回 EMPTY。

## Safety note

Red-line review is review-only and dry-run. It does not enable live trading, does not submit orders, does not send real notifications, and does not call xttrader or QMT trading APIs.

## 下一阶段

阶段四十一：极小资金灰度实盘前只读确认台账（仍不执行）。
