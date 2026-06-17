# Stage 11: Windows Task Scheduler 标准化

## 职责

Windows Task Scheduler 仅负责在本地 Windows 环境定时启动项目的每日 dry-run / shadow pipeline。它不是实盘交易入口，不绕过 Risk Gate，也不直接连接 QMT 下单接口。

## 默认安全模式

- 默认 dry-run / shadow。
- 默认不真实下单。
- 默认不真实发送 Email、Telegram、企业微信等通知。
- 默认只生成本地报告和本地日志。
- 注册和删除计划任务脚本默认只预览命令，不实际修改系统计划任务。

## 默认执行时间与输出

- 默认任务名：`QmtAiTradingDailyDryRun`
- 默认执行时间：`15:30`，本地收盘后运行。
- 默认报告目录：`reports/`
- 默认日志目录：`logs/daily_pipeline/`

`reports/`、`logs/` 和 `*.log` 已由 `.gitignore` 忽略，不提交到 Git。

## 注册计划任务

Dry-run 预览（默认，不注册）：

```powershell
py scripts/register_daily_pipeline_task.py
```

真实注册（仅在确认命令后使用）：

```powershell
py scripts/register_daily_pipeline_task.py --execute
```

可选参数：

```powershell
py scripts/register_daily_pipeline_task.py --task-name QmtAiTradingDailyDryRun --time 15:30 --report-dir reports
```

## 删除计划任务

Dry-run 预览（默认，不删除）：

```powershell
py scripts/unregister_daily_pipeline_task.py
```

真实删除（仅在确认命令后使用）：

```powershell
py scripts/unregister_daily_pipeline_task.py --execute
```

## dry-run 预览与 --execute 区别

不传 `--execute` 时，脚本只打印将要执行的 `schtasks` 命令，并显示 `DRY-RUN ONLY` 提示，绝不调用真实 `schtasks /Create` 或 `schtasks /Delete`。

传入 `--execute` 时，脚本才会调用 Windows `schtasks` 命令注册或删除计划任务。该操作只影响本地 Windows 计划任务，不修改项目配置、不写系统环境变量、不写敏感信息。

## 计划任务实际入口

计划任务调用：

```powershell
py scripts/run_scheduled_daily_pipeline.py
```

该入口等价于安全执行：

```powershell
py scripts/run_daily_pipeline.py --write-reports --report-dir reports --notify-dry-run
```

执行日志写入 `logs/daily_pipeline/`。遇到异常时，脚本返回非 0 exit code，并把异常堆栈写入日志文件。

## 后续方向

后续可以接入 UI、手动确认、通知实发审批或更完整的运维面板。在这些能力上线前，Stage 11 保持本地调度、离线报告和 dry-run 通知占位，不接真实实盘。
