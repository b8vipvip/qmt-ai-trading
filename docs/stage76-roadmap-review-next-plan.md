# Stage76 路线重审与下一轮开发计划层

Stage76 是路线重审与下一轮开发计划层，在 Stage61-75 UI 产品化路线收口之后执行。Stage76 基于 Stage1-75 已完成成果，重新审查当前项目路线、架构一致性、安全边界、数据质量、UI 成熟度、实盘前缺口和下一轮开发优先级。

## 安全边界

- Stage76 不等于实盘授权。
- Stage76 不提供下单按钮。
- Stage76 不提供账户/持仓/订单/成交查询入口。
- Stage76 不调用 xttrader。
- Stage76 不真实下单。
- Stage76 不查询资金/持仓/订单/成交。
- Stage76 不真实发送通知。
- Stage76 不自动 approve。
- Stage76 只生成路线重审、缺口复盘和下一轮开发计划。
- READY_FOR_NEXT_ROADMAP_REVIEW 只表示路线重审材料可供人工复核。
- Stage76 通过后也不直接进入实盘；建议 Stage77 做实盘前安全审计重启与真实数据质量复核层。

## 只读成果

Stage76 默认生成到 `stage76_roadmap_review/`，该目录是运行产物，不提交。报告覆盖 Stage1-75 成果总览、Stage61-75 UI 产品化路线复盘、架构一致性、安全边界、数据质量缺口、交易就绪缺口、UI 成熟度、实盘前阻断项、下一轮路线建议、优先级矩阵和 Stage77 计划。

## 实盘前阻断项

1. 没有完成新的实盘前安全审计重启。
2. 没有完成真实缓存长期质量验证。
3. 没有完成 Paper Trading 长周期复盘。
4. 没有完成小资金灰度参数。
5. 没有完成真实 QMT 环境下 xtdata 稳定性复核。
6. 没有完成真实通知通道安全审查。
7. 没有完成异常监控 / 熔断 / 告警闭环。
8. 没有完成 live config 多重确认。
9. 没有完成资金管理与组合层在真实数据上的充分验证。
10. UI 完成不等于交易链路成熟。

## 下一轮路线建议

- Stage77：实盘前安全审计重启与真实数据质量复核层，仍不直接实盘。
- Stage78：真实缓存长期质量报告与异常监控层，仍不直接实盘。
- Stage79：Paper Trading 长周期复盘与归因层，仍不直接实盘。
- Stage80：小资金灰度参数草案与人工审批流程复核层，仍不直接实盘。

## UTF-8 与乱码防回归

Stage76 Python 源码、Markdown 和 JSON 使用 UTF-8；读写文件显式使用 `encoding="utf-8"`，JSON 使用 `ensure_ascii=False`。验证脚本打印 Markdown 时使用 `Get-Content -Encoding UTF8`，并在最终 sync scan/status 前执行 `Clean-PythonCache`。
