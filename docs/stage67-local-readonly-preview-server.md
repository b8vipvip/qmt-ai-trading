# 阶段六十七：本地只读预览服务层

Stage67 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage67 基于 Stage66 本地控制台静态数据绑定层，提供本地只读预览服务，用于在浏览器中预览 `index.html`、`data_bundle.json`、`binding_manifest.json`、`data_source_map.json` 等静态材料。

## 安全边界

- Stage67 是本地只读预览服务层。
- Stage67 进入 Stage61-75 UI 产品化路线。
- Stage67 不等于实盘授权。
- Stage67 只提供本地 `127.0.0.1` 静态文件预览服务，默认端口 `8767`。
- Stage67 不提供下单按钮。
- Stage67 不提供账户/持仓/订单/成交查询入口。
- Stage67 不调用 `xttrader`。
- Stage67 不真实下单。
- Stage67 不查询资金/持仓/订单/成交。
- Stage67 不真实发送通知。
- Stage67 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW` 只表示本地只读预览服务层材料可供人工复核，不代表实盘授权。

## 服务行为

`run_local_console_preview_server.py --dry-run` 只检查 host、port、static-dir、routes 和 safety，不长期启动服务。`--serve-once` 只绑定 `127.0.0.1`，最多运行 `timeout-seconds`，只接受 GET / HEAD 并自动退出。

## 路由边界

允许 GET / HEAD：`/`、`/index.html`、`/app.js`、`/style.css`、`/data_bundle.json`、`/binding_manifest.json`、`/data_source_map.json`、`/static_data_safety.json`、`/health`、`/preview-safety`、`/preview-manifest`。

禁止 POST / PUT / PATCH / DELETE，禁止 `/order`、`/orders`、`/trade`、`/execute`、`/approve`、`/live`、`/notify`、`/account`、`/positions`、`/assets` 以及对应 hash route。

## 编码与 xttrader 文案处理

如果上游报告存在明显 mojibake / 乱码，Stage67 只展示 `encoding_warning=True` 与“上游报告存在编码异常，已隐藏乱码正文”，不输出大段乱码、不作为 CRITICAL、不阻断只读预览服务。安全横幅、文档、生成报告中的“不调用 xttrader”归类为 INFO/WARN；真实可执行 server code / JS action 中出现 `xttrader`、`XtQuantTrader`、下单或账户查询才是 CRITICAL。

## 下一阶段

Stage68 是本地控制台刷新与导航增强层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。
