from __future__ import annotations
import json
from .models import *

def _json(obj): return json.dumps(to_plain(obj), ensure_ascii=False, indent=2)
def format_live_gray_candidate_report_json(r): return _json(r)
def format_simple_json(r): return _json(r)
def _items(items): return "\n".join(f"- {getattr(x,'name','')}: {getattr(x,'value',getattr(x,'limit',getattr(x,'summary','')))} {getattr(x,'summary','')}" for x in items) or "- 无"

def format_live_gray_candidate_report_markdown(r: LiveGrayCandidateReport) -> str:
    ev="\n".join(f"- [{e.severity.value}] {e.title}: {e.summary}" for e in r.evidence) or "- 无"
    return f"""# Stage57 Small-money Gray Candidate Plan

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{ev}

## Stage56 Real Cache Quality Evidence
{_section(r, LiveGrayCandidateCategory.STAGE56_REAL_CACHE_QUALITY)}

## Stage55 QMT Dry-run Calibration Evidence
{_section(r, LiveGrayCandidateCategory.STAGE55_QMT_DRYRUN_CALIBRATION)}

## ETF Whitelist Evidence
- Stage56 validated symbols / ETF whitelist: {', '.join(r.allowed_symbols) if r.allowed_symbols else 'UNAVAILABLE'}

## Gray Capital Limit Evidence
{_items(r.capital_limits)}

## Gray Risk Limit Evidence
{_items(r.risk_limits)}

## Human Approval Evidence
{_items(r.approval_items)}

## Rollback and Circuit Breaker Evidence
{_items(r.rollback_items)}

## Roadmap Stage Plan Evidence
{_section(r, LiveGrayCandidateCategory.ROADMAP_STAGE_PLAN)}

## UI Productization Plan Evidence
- 本阶段继续检查完整 Stage1-75 工程阶段计划和 Stage61-75 UI 产品化计划；不提前开发 UI。
- UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

## Small-money Gray Candidate Plan
- 小资金灰度资金上限、单笔交易上限、单日交易上限、ETF 白名单、最大持仓数、最大单标的仓位、组合最大仓位、现金保留比例、最大回撤触发阈值、单日亏损触发阈值、最大下单次数、冷却期均只作为候选计划。
- 不代表实盘授权声明：本报告不产生授权、不注册真实任务、不把候选计划变成真实订单。

## Gray Risk Limit Review
{_items(r.risk_limits)}

## Gray Approval Checklist
{_items(r.approval_items)}

## Gray Rollback and Circuit Breaker Plan
{_items(r.rollback_items)}

## Next Gray Approval Package Plan
{_items(r.next_plan_items)}

## Required Manual Confirmations
- 人工确认 Stage57 不代表实盘授权。
- 人工确认未来真实执行仍需单独审批。

## Blocking Reasons
{chr(10).join('- '+x for x in r.blocking_reasons) or '- 无'}

## Warnings
{chr(10).join('- '+x for x in r.warnings) or '- 无'}

## Next Stage Preview
Stage58 仍不得直接实盘；只能做小资金灰度前最终人工审批包，不调用 xttrader、不查询真实账户、不下单。
"""

def _section(r, cat):
    xs=[e for e in r.evidence if e.category==cat]
    return "\n".join(f"- [{e.status.value}/{e.severity.value}] {e.summary}" for e in xs) or "- UNAVAILABLE"

def format_gray_risk_limit_report_markdown(r): return "# Stage57 Gray Risk Limits\n\n"+r.safety_note+"\n\n"+_items(r.items)+"\n"
def format_gray_approval_checklist_report_markdown(r): return "# Stage57 Gray Approval Checklist\n\n"+r.safety_note+"\n\n"+_items(r.items)+"\n"
def format_gray_rollback_circuit_breaker_report_markdown(r): return "# Stage57 Gray Rollback and Circuit Breaker\n\n"+r.safety_note+"\n\n"+_items(r.rollback_items+r.stop_conditions)+"\n"
def format_next_gray_approval_package_plan_report_markdown(r): return "# Stage58 Next Gray Approval Package Plan\n\n"+r.safety_note+"\n\n"+_items(r.items)+"\n"
