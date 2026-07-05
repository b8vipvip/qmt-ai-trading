# qmt-ai-trading 当前目录说明与清理规则

本文档用于区分“真正还在用的系统目录”和“历史阶段产物 / 临时验收产物”。本项目后续应按业务模块维护，不再按 `stageXX` 目录继续堆叠。

## 1. 现在真正要看的目录

```text
D:\AI\qmt
├─ local_console_app\                 # 前端：本地浏览器工作台，访问 http://127.0.0.1:8768/
├─ qmt_ai_trading\console_api\        # 后端：本地 HTTP API、路由、任务注册、任务执行器
├─ qmt_ai_trading\datahub\            # 数据层：行情、标的、缓存接口
├─ qmt_ai_trading\research\           # 研究层：因子、评分、候选池
├─ qmt_ai_trading\strategies\         # 策略层：ETF 轮动、多因子信号、TradeIntent
├─ qmt_ai_trading\risk\               # 风控层：Risk Gate、订单预览、安全边界
├─ qmt_ai_trading\trading_gateway\    # QMT / xtquant 边界，含账户只读适配
├─ scripts\run_console_api.py         # 启动本地工作台 API
├─ scripts\sync_all.ps1               # GitHub 同步脚本，不随便改
├─ scripts\validate_local_console_workbench.ps1  # 验证脚本，只用于检查，不是用户主入口
├─ artifacts\reports\console\        # 工作台当前读取的统一 JSON / Markdown 产物
├─ docs\                              # 路线、架构和阶段说明
└─ tests\                             # 自动化测试
```

## 2. 前端在哪里

前端主目录是：

```text
local_console_app\
├─ index.html              # 页面入口
├─ app.js                  # 基础模块渲染、API 读取、任务面板
├─ task_params.js          # 任务参数、一键 dry-run 链路、产物快照
├─ workbench.css           # 工作台样式
├─ workbench_overrides.js  # 工作台模块名称、能力地图、页面覆盖逻辑
├─ task_params.css         # 任务参数表单样式
└─ ui_sanitize.js          # UI 安全辅助
```

浏览器访问：

```powershell
http://127.0.0.1:8768/
```

## 3. 后端在哪里

后端主入口是：

```text
scripts\run_console_api.py
```

它实际调用：

```text
qmt_ai_trading\console_api\api_server.py
```

核心后端文件：

```text
qmt_ai_trading\console_api\
├─ api_server.py       # HTTP server，静态前端和 /api/v1 接口
├─ routes\             # 各业务模块 API 路由
├─ task_registry.py    # 白名单任务目录
├─ task_runner.py      # 任务执行器
├─ task_store.py       # 本次运行任务记录
├─ safety.py           # 本地绑定、危险方法、实盘禁用边界
└─ serializers.py      # 任务输出序列化
```

启动方式：

```powershell
cd D:\AI\qmt
py scripts\run_console_api.py --host 127.0.0.1 --port 8768
```

这个 PowerShell 窗口会被 API 服务占住。要跑其它命令，请另开一个 PowerShell。

## 4. 工作台当前读哪里

前端不是直接读散落目录，而是读后端 API。后端 API 再从统一产物目录读取：

```text
artifacts\reports\console\
├─ datahub\
├─ research\
├─ strategy\
├─ risk\
├─ paper\
├─ approval\
├─ account_readonly\
├─ portfolio\
├─ workflow\
└─ validation_logs\
```

所以后续开发目标应该是：业务模块写入 `artifacts\reports\console\...`，前端从 `/api/v1/...` 读取，而不是继续生成新的 `local_console_xxx_stageNN` 页面目录。

## 5. 可以清理或归档的历史产物

这些目录通常是阶段开发、临时验收、一次性报告或旧入口，后续不应再作为主系统入口：

```text
*_stageNN
local_console_*_stageNN
market_data_test_stageNN
live_*_stageNN
agent_reports_stageNN
monitoring_reports_stageNN
smoke_reports_stageNN
```

这些文件通常是一次性修复脚本或旧备份，确认不需要后可归档：

```text
config.json.bak_*
fix_*.py
patch_*.py
update_qmt_project_old_broken.ps1
```

不要直接删除以下目录 / 文件：

```text
.env
.git\
docs\
scripts\
qmt_ai_trading\
local_console_app\
artifacts\reports\console\
tests\
market_data\
config.json
config.example.json
README.md
```

## 6. 清理建议

先只看计划：

```powershell
cd D:\AI\qmt
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_local_workspace.ps1 -Mode plan
```

确认列表没问题后归档到 `artifacts\cleanup_archive\时间戳\`：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_local_workspace.ps1 -Mode archive
```

确认归档后的系统仍正常，再考虑删除归档目录或使用 delete 模式。默认建议先 archive，不建议第一次直接 delete。
