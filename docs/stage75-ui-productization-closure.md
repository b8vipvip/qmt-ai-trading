# Stage75 UI 产品化收口层

Stage75 是 UI 产品化收口层，属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线，也是 Stage61-75 UI 产品化路线的收口阶段。

## 安全边界

- Stage75 不等于实盘授权。
- Stage75 只提供本地静态 UI 收口材料。
- Stage75 不提供下单按钮。
- Stage75 不提供账户/持仓/订单/成交查询入口。
- Stage75 不调用 xttrader。
- Stage75 不真实下单。
- Stage75 不查询资金/持仓/订单/成交。
- Stage75 不真实发送通知。
- Stage75 不自动 approve。
- closure report / capability matrix / final conclusion draft 都不是审批授权。
- READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW 只表示 UI 产品化收口层材料可供人工复核。

## 输出内容

默认运行产物目录是 `local_console_closure_stage75/`，该目录不提交。输出包括 `index.html`、`app.js`、`style.css`、UI 产品化收口报告、阶段总览、UI 能力矩阵、安全边界总表、只读演示入口汇总、路由覆盖总览、静态资产覆盖总览、风险与限制总览、最终验收结论草稿、后续路线建议和 closure safety report 的 Markdown / JSON 材料。

## UTF-8 与乱码防回归

Stage75 Python 源码与 Markdown/JSON 输出使用 UTF-8；读写文件显式使用 `encoding="utf-8"`，JSON 使用 `ensure_ascii=False`。验证脚本打印 Markdown 时使用 `Get-Content -Encoding UTF8`，并在最终 sync scan/status 前执行 `Clean-PythonCache`。

## 下一阶段建议

Stage75 通过后建议先做 roadmap 重审与下一阶段规划，不直接进入实盘。建议 Stage76 为路线重审与下一轮开发计划层，继续不接实盘、不下单、不调用 `xttrader`、不查询真实账户、不自动 approve。
