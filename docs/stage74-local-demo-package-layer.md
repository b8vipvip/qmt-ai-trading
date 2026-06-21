# Stage74 本地演示打包层

Stage74 是本地演示打包层，属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage74 基于 Stage73 本地文档/帮助层，只生成本地静态演示包目录、静态资源清单、演示入口页、演示说明、只读 demo manifest、demo route map、demo asset manifest、demo package index、demo safety report、demo validation summary 与 Stage75 UI 产品化收口计划。

## 安全边界

- Stage74 不等于实盘授权。
- Stage74 只提供本地静态演示包。
- Stage74 不提供下单按钮。
- Stage74 不提供账户/持仓/订单/成交查询入口。
- Stage74 不调用 xttrader。
- Stage74 不真实下单。
- Stage74 不查询资金/持仓/订单/成交。
- Stage74 不真实发送通知。
- Stage74 不自动 approve。
- demo guide / manifest / package index 都不是审批授权。
- READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW 只表示本地演示打包层材料可供人工复核，不是实盘授权。
- UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## 输出内容

默认运行产物目录是 `local_console_demo_stage74/`，该目录不提交。输出包括 `index.html`、`app.js`、`style.css`、`demo_manifest`、`demo_guide`、`demo_route_map`、`demo_asset_manifest`、`demo_package_index`、`demo_safety_report`、`demo_validation_summary`、`local_console_demo_package_report` 和 `next_ui_productization_closure_plan` 的 Markdown / JSON 材料。

## UTF-8 与乱码防回归

Stage74 Python 源码与 Markdown/JSON 输出使用 UTF-8；读写文件显式使用 `encoding="utf-8"`，JSON 使用 `ensure_ascii=False`。验证脚本打印 Markdown 时使用 `Get-Content -Encoding UTF8`，并在最终 sync scan/status 前执行 `Clean-PythonCache`。

## 下一阶段

Stage75 是 UI 产品化收口层，仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单，不真实发送通知，不自动 approve。
