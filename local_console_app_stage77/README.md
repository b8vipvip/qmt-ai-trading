# Stage77 QMT AI 本地业务控制台

Stage77 是业务控制台 MVP，不是开发验收台。前端可以调用本地 API 触发白名单 dry-run / shadow / read-only 任务，并查看任务状态、日志摘要和报告摘要。

## 静态前端
```powershell
cd D:\AI\qmt\local_console_app_stage77
py -m http.server 8767 --bind 127.0.0.1
```
访问 http://127.0.0.1:8767/ 。此方式 API 离线，按钮会提示启动 API。

## 业务控制台 API
```powershell
cd D:\AI\qmt
py scripts\run_console_api.py --host 127.0.0.1 --port 8768 --static-dir local_console_app_stage77
```
访问 http://127.0.0.1:8768/ 。只能运行白名单 dry-run 任务。

## 安全边界
不接实盘、不查询真实账户、不真实下单、不调用 xttrader、不自动 approve、不开放 0.0.0.0。
