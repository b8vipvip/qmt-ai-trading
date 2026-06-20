# 阶段六十六：本地控制台静态数据绑定层

Stage66 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage66 基于 Stage65 本地控制台 shell / 静态页面骨架层，把 Stage64 dashboard cards、Stage63 detail/filter、Stage62 report list、Stage61 API capability 等 JSON/Markdown 材料绑定到静态页面，形成可浏览的本地只读控制台数据绑定层。

## 安全边界

- Stage66 是本地控制台静态数据绑定层。
- Stage66 不等于实盘授权。
- Stage66 只提供本地静态数据绑定和只读展示。
- Stage66 不提供下单按钮。
- Stage66 不提供账户/持仓/订单/成交查询入口。
- Stage66 不调用 `xttrader`。
- Stage66 不真实下单。
- Stage66 不查询资金/持仓/订单/成交。
- Stage66 不真实发送通知。
- Stage66 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW` 只表示本地控制台静态数据绑定层材料可供人工复核，不代表实盘授权。

## 输出材料

默认生成 `local_console_binding_stage66/`，包含 `index.html`、`app.js`、`style.css`、`data_bundle.json`、`binding_manifest.json`、`data_source_map.json`、`missing_data_placeholders.json`、`bound_asset_index.json`、`static_data_safety.json`、`next_console_preview_server_plan.json` 与 `local_console_binding_report.json/md`。

## tolerant reader / encoding 防护

Stage66 读取器 JSON 优先；JSON 失败时降级 Markdown；Markdown 自动识别 UTF-8-SIG、UTF-8、UTF-16、UTF-16LE、UTF-16BE，最后才使用 replacement fallback。摘要输出清理 BOM 与 NUL；检测到明显乱码时展示 `encoding_warning=True`，不输出大段乱码。

## 下一阶段

Stage67 是本地只读预览服务层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。Stage67 只绑定 `127.0.0.1`，默认 dry-run，只读，不提供 POST/PUT/PATCH/DELETE，不访问 QMT，不发送真实通知。
