from __future__ import annotations
import json
from .models import *
def _json(o): return json.dumps(to_plain(o), ensure_ascii=False, indent=2)
def format_live_gray_final_approval_report_json(r): return _json(r)
def format_simple_json(r): return _json(r)
def _items(items):
    out=[]
    for x in items:
        name=getattr(x,'name',getattr(x,'role','')) ; detail=getattr(x,'value',getattr(x,'trigger',getattr(x,'statement',''))); summary=getattr(x,'summary',getattr(x,'action',''))
        out.append(f'- {name}: {detail} {summary}'.strip())
    return '\n'.join(out) or '- 无'
def _section(r,cat):
    xs=[e for e in r.evidence if e.category==cat]
    return '\n'.join(f'- [{e.status.value}/{e.severity.value}] {e.title}: {e.summary}' for e in xs) or '- UNAVAILABLE'
def format_live_gray_final_approval_report_markdown(r: LiveGrayFinalApprovalReport) -> str:
    ev='\n'.join(f'- [{e.severity.value}] {e.title}: {e.summary}' for e in r.evidence) or '- 无'
    return f'''# Stage58 Final Human Approval Package Before Small-money Gray

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{ev}

## Stage57 Gray Candidate Evidence
{_section(r, LiveGrayFinalApprovalCategory.STAGE57_GRAY_CANDIDATE)}

## Stage56 Real Cache Quality Evidence
{_section(r, LiveGrayFinalApprovalCategory.STAGE56_REAL_CACHE_QUALITY)}

## Stage55 QMT Dry-run Calibration Evidence
{_section(r, LiveGrayFinalApprovalCategory.STAGE55_QMT_DRYRUN_CALIBRATION)}

## Capital and Position Approval
{_items(r.capital_position_items)}

## Risk Gate and Human Approval Review
{_items(r.risk_human_items)}

## Rollback and Circuit Breaker Approval
{_items(r.rollback_circuit_items)}

## Final Signoff Checklist
{_items(r.signoff_items)}

## Roadmap Stage Plan Evidence
{_section(r, LiveGrayFinalApprovalCategory.ROADMAP_STAGE_PLAN)}

## UI Productization Plan Evidence
- 本阶段继续检查完整 Stage1-75 工程阶段计划和 Stage61-75 UI 产品化计划；不提前开发 UI。
- UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

## Final Human Approval Package
{_items(r.checklist_items)}
- 不代表实盘授权声明：本报告不产生授权、不注册真实任务、不把审批包变成真实订单。

## Next Read-only Seal Plan
{_items(r.next_seal_plan_items)}

## Required Manual Confirmations
- 人工确认资金上限、单笔上限、单日上限、ETF 白名单、最大持仓数、单标的上限、组合暴露上限、现金保留比例、亏损阈值、回撤阈值、最大下单次数和冷却期。
- 人工确认 Risk Gate、Human Approval、Paper Trading / dry-run 证据、回滚 / 熔断计划、日志 / 复盘要求和最终签字清单。

## Blocking Reasons
{chr(10).join('- '+x for x in r.blocking_reasons) or '- 无'}

## Warnings
{chr(10).join('- '+x for x in r.warnings) or '- 无'}

## Next Stage Preview
Stage59 仍不得直接实盘；只能做灰度前只读封版与运行前检查清单，不调用 xttrader、不查询真实账户、不下单。
'''
def format_capital_position_approval_report_markdown(r): return '# Stage58 Capital and Position Approval\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
def format_risk_human_approval_review_report_markdown(r): return '# Stage58 Risk Gate and Human Approval Review\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
def format_rollback_circuit_approval_report_markdown(r): return '# Stage58 Rollback and Circuit Breaker Approval\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
def format_final_signoff_checklist_report_markdown(r): return '# Stage58 Final Signoff Checklist\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
def format_next_readonly_seal_plan_report_markdown(r): return '# Stage59 Next Read-only Seal Plan\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
