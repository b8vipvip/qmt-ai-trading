# qmt-ai-trading 统一开发规则

本文件用于替代继续按“阶段”推进的旧流程。历史阶段文档和历史目录仅作为追溯材料保留；从现在开始，所有修改都直接面向整个 qmt-ai-trading 项目。

## 1. 开发方式

- 不再新建 `stageXX`、`StageXX`、`local_console_*_stageXX` 作为新功能入口。
- 不再把后续需求写成“下一阶段开发”；后续需求统一写成“项目级修改 / 模块级修改 / 验收项”。
- 已经存在的历史阶段函数、历史产物目录、历史任务 ID 只作为兼容入口保留；新增代码必须使用业务模块命名。
- 多个历史阶段实现同一功能时，以最新统一控制台、统一 API、统一安全边界为准。
- 前端页面必须展示给人看的可视化状态、表格、卡片和操作按钮，不允许把主要功能做成裸 JSON 或代码展示。

## 2. 后端统一约定

统一后端入口：

```text
py scripts\\run_console_api.py --host 127.0.0.1 --port 8768
```

统一 API 前缀：

```text
/api/v1
```

后端接口按业务模块组织：workflow、datahub、research、strategy、risk、backtest、paper-trading、approval、account-readonly、monitoring、safety、tasks。

任何新增接口必须满足：默认只读或 dry-run；不绕过 Risk Gate；不默认启用实盘；不把 mock/fallback 当成真实可交易数据；敏感信息必须脱敏。

## 3. 前端统一约定

统一前端入口：

```text
local_console_app/index.html
local_console_app/app.js
local_console_app/style.css
```

前端模块规则：

- 后端已实现的模块必须接入真实 API，支持刷新、查询参数、状态展示、列表/表格展示和错误提示。
- 后端接口存在但产物缺失时，前端显示“产物待生成”，并提示运行刷新或验收脚本。
- 后端尚未开发的模块可以保留静态占位，但必须明确标注“后端待开发”，不得伪造数据。
- 主要页面不展示裸 JSON；诊断信息应以表格、卡片或可读列表展示。
- 任何真实交易、下单、撤单、自动审批入口都必须保持关闭或不可见。

## 4. 统一验收入口

每次修改代码后，统一运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\validate_project.ps1
```

该脚本会调用统一控制台验收流程，并输出：

```text
validation_logs/project_validation_<时间戳>.log
artifacts/reports/console_validation/latest_project_validation.json
artifacts/reports/console_validation/latest_project_validation.md
```

验收必须覆盖：刷新控制台运行产物、compileall、统一控制台 pytest、API smoke test、安全边界检查和同步隐私扫描。

## 5. 后续需求书写格式

后续不要再写“第 X 阶段”。统一使用：目标、影响模块、需要改的后端、需要改的前端、验收命令、验收通过标准、风险边界。
