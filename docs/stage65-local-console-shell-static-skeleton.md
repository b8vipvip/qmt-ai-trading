# 阶段六十五：本地控制台 shell / 静态页面骨架层

Stage65 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage65 基于 Stage64 本地控制台概览面板层，生成本地静态控制台 shell、页面布局、导航结构、只读数据注入点、dashboard card 占位、报告列表占位、详情过滤占位、安全边界固定展示和 Stage66 数据绑定计划。

## 安全边界

- Stage65 不等于实盘授权。
- Stage65 只提供本地静态页面骨架。
- Stage65 不提供下单按钮。
- Stage65 不提供账户/持仓/订单/成交查询入口。
- Stage65 不调用 `xttrader`，不导入 `XtQuantTrader`。
- Stage65 不真实下单。
- Stage65 不查询资金/持仓/订单/成交。
- Stage65 不真实发送通知。
- Stage65 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW` 只表示本地控制台 shell / 静态页面骨架层材料可供人工复核，不代表实盘授权。

## 静态页面骨架

默认生成 `local_console_shell_stage65/`，包含 `index.html`、`app.js`、`style.css`、`shell_manifest`、`route_map`、`asset_index`、`data_binding_placeholders`、`static_safety_boundary`、`next_console_data_binding_plan` 与 `local_console_shell_report`。

`index.html` 固定展示 Header、Safety Banner、Navigation、Dashboard Overview、Stage Status Cards、Latest Validation、Warning / Blocking Stats、Manifest / Hash、Scheduler Preview、Safety Boundary、API Capability、Detail / Filter、Report List 与 Footer。

`app.js` 只允许加载 `./shell_manifest.json`、`./route_map.json`、`./data_binding_placeholders.json` 三类本地静态材料，不发送交易、账户、审批、通知请求。

## tolerant reader

Stage65 tolerant reader 优先 JSON，JSON 解析失败时降级 Markdown 摘要并记录 WARN；validation log 解码优先 UTF-8-SIG、UTF-8、UTF-16、UTF-16LE、UTF-16BE，最后才使用 UTF-8 replacement fallback。页面摘要会剥离 BOM、清理 NUL；replacement char 只记录 encoding warning，不阻断。

## 下一阶段

Stage66 是本地控制台静态数据绑定层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。Stage66 将 Stage64 dashboard cards、Stage63 filters、Stage62 report list、Stage61 API capability 等 JSON 材料绑定到静态页面。
