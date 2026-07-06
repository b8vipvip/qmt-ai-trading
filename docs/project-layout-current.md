# QMT AI 当前本地工作台目录说明

这个文档用于区分当前真正还在使用的主线目录、运行产物目录、历史实验目录，避免 `D:\AI\qmt` 根目录越来越乱。

## 当前主线入口

| 用途 | 目录 / 文件 | 说明 |
| --- | --- | --- |
| 前端工作台 | `local_console_app/` | 浏览器打开 `http://127.0.0.1:8768/` 看到的页面。主要文件是 `index.html`、`app.js`、`task_params.js`、`workbench.css`、`workbench_overrides.js`。 |
| 后端业务代码 | `qmt_ai_trading/` | 当前统一后端主包，行情、Data Hub、Research、Strategy、Risk、Paper、Approval、Account Readonly、Portfolio 等业务模块都应逐步收敛到这里。 |
| 后端启动入口 | `scripts/run_console_api.py` | 启动统一本地 API 与静态前端。常用命令：`py scripts\run_console_api.py --host 127.0.0.1 --port 8768`。 |
| 任务参数与白名单 | `local_console_app/task_params.js` + 后端任务注册 | 前端按钮只调用白名单任务，并强制 `dry_run/read_only/allow_order_submit=false/allow_order_cancel=false`。 |
| 任务历史 / 日志中心 | `qmt_ai_trading/console_api/api_server.py` + `qmt_ai_trading/console_api/task_store.py` | `/api/v1/tasks/history` 展示最近任务历史、状态、日志入口和产物路径；当前已落地本地 JSON 持久化，重启 API 后仍可读取历史。 |
| 当前控制台产物 | `artifacts/reports/console/` | 前端页面读取的统一产物目录。这里是运行结果，不是源码主线。 |
| 本地任务历史文件 | `artifacts/reports/console/task_history/task_history.json` | 仅本地运行时文件，已加入 `.gitignore`，不要提交到 GitHub。 |
| 文档与路线 | `docs/` | 项目路线、架构、当前目录说明和后续阶段计划。 |
| 验证脚本 | `scripts/validate_local_console_workbench.ps1` | 校验前端、API、危险旗标、任务历史接口和关键接口。 |
| 本地清理脚本 | `scripts/cleanup_local_workspace.ps1` | 先 `-Mode plan` 预览，再 `-Mode archive` 安全归档历史文件。 |

## 不建议继续作为主线开发入口的内容

下面这些通常属于早期阶段实验、历史脚本、临时报告或运行产物。它们不一定立刻删除，但不应该继续作为新功能开发入口：

- 根目录下大量 `qmt_*.py` 旧脚本。
- `shadow_replay/`、`shadow_replay_batch/`、`shadow_trading/` 等早期独立实验目录。
- `local_console_approval/`、`local_console_order_preview/` 这类已经被统一工作台替代的阶段性前端目录。
- `validation_logs/`、`.pytest_cache/`、旧 `reports/`、旧 `runs/`、旧 `backtest_results/` 等运行过程产物。

是否删除必须以脚本扫描和验证结果为准，不能手动乱删。

## 推荐清理流程

先只看计划，不改文件：

```powershell
cd D:\AI\qmt
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_local_workspace.ps1 -Mode plan
```

确认候选项合理后，先归档，不永久删除：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_local_workspace.ps1 -Mode archive
```

归档后重新启动 API 并验证：

```powershell
$conn = Get-NetTCPConnection -LocalPort 8768 -State Listen -ErrorAction SilentlyContinue
if ($conn) { Stop-Process -Id $conn.OwningProcess -Force }

py scripts\run_console_api.py --host 127.0.0.1 --port 8768
```

另开一个 PowerShell：

```powershell
cd D:\AI\qmt
powershell -ExecutionPolicy Bypass -File .\scripts\validate_local_console_workbench.ps1 -RequireApi
```

前端、API、日常操作中心、任务历史、Portfolio 预览和安全旗标都正常后，再考虑提交删除或保留归档。`artifacts\cleanup_archive\` 是本地备份，不要提交到 GitHub。

## 下一步开发方向

当前工作台已经从“验收展示”转向“日常操作入口”。后续主线建议按下面顺序推进：

1. **先整理本地目录**：用 `cleanup_local_workspace.ps1` 把历史阶段产物归档，避免继续在根目录混乱开发。
2. **强化日常工作台**：让“刷新行情 → 研究 → 策略 → 风控 → Paper → 人工复核 → Portfolio 预览”成为主入口。
3. **强化任务历史与日志中心**：当前已支持本地 JSON 持久化；后续可改为 sqlite / duckdb，并增加失败原因、耗时统计、筛选和跨进程长期留存。
4. **接入真实 Data Hub 外部源**：AkShare / Tushare / BaoStock、指数成分、ETF、行业、财务、新闻。
5. **接入研究层模型**：Alpha158 / Alpha360 / Alpha101、LightGBM / Lasso / MLP。
6. **Agent 投研结构化输出**：技术面、基本面、新闻情绪、风险、组合经理 Agent。
7. **实盘前安全审计**：在任何小资金实盘前先做 go/no-go 审计和人工二次确认。
