# Stage73 本地文档/帮助层

Stage73 是本地文档/帮助层，属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage73 基于 Stage72 本地控制台 UI 验收汇总层，只生成本地静态帮助文档、页面说明、功能说明、安全说明、FAQ、错误处理说明、术语表、route help map、help package index、docs safety report 和 Stage74 本地演示打包层计划。

## 安全边界

- Stage73 不等于实盘授权。
- Stage73 只提供本地静态帮助文档。
- Stage73 不提供下单按钮。
- Stage73 不提供账户/持仓/订单/成交查询入口。
- Stage73 不调用 xttrader。
- Stage73 不真实下单。
- Stage73 不查询资金/持仓/订单/成交。
- Stage73 不真实发送通知。
- Stage73 不自动 approve。
- help docs / FAQ / glossary 都不是审批授权。
- READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW 只表示本地文档/帮助层材料可供人工复核，不是实盘授权。
- UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## 输出内容

Stage73 输出 help home、page help、feature help、safety help、FAQ、error handling guide、glossary、route help map、help package index、docs safety report 与 next local demo package plan。默认运行产物目录是 `local_console_help_stage73/`，该目录不提交。

## UTF-8 与乱码防回归

Stage73 Python 源码与 Markdown/JSON 输出使用 UTF-8；读写文件显式使用 `encoding="utf-8"`，JSON 使用 `ensure_ascii=False`。验证脚本打印 Markdown 时使用 `Get-Content -Encoding UTF8`，并在最终 sync scan/status 前执行 `Clean-PythonCache`。

## 下一阶段

Stage74 是本地演示打包层，仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单，不真实发送通知，不自动 approve。
