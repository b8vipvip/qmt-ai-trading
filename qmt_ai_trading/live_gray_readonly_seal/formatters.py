from __future__ import annotations
import json
from .models import *
def _json(o): return json.dumps(to_plain(o),ensure_ascii=False,indent=2)
def format_live_gray_readonly_seal_report_json(r): return _json(r)
def format_simple_json(r): return _json(r)
def _items(items):
    return '\n'.join(f"- {getattr(x,'name',getattr(x,'role',''))}: {getattr(x,'status','')} {getattr(x,'summary',getattr(x,'statement',''))}" for x in items) or '- 无'
def _manifest(items):
    return '\n'.join(f"- {i.relative_path}: exists={i.exists} size_bytes={i.size_bytes} sha256={i.sha256} category={i.category.value} required={i.required}" for i in items) or '- 无'
def _section(r,cat):
    xs=[e for e in r.evidence if e.category==cat]
    return '\n'.join(f'- [{e.status.value}/{e.severity.value}] {e.title}: {e.summary}' for e in xs) or '- UNAVAILABLE'
def format_live_gray_readonly_seal_report_markdown(r: LiveGrayReadonlySealReport)->str:
    ev='\n'.join(f'- [{e.severity.value}] {e.title}: {e.summary}' for e in r.evidence) or '- 无'
    return f'''# Stage59 Read-only Seal and Pre-run Checklist Before Gray

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{ev}

## Stage58 Final Approval Evidence
{_section(r, LiveGrayReadonlySealCategory.STAGE58_FINAL_APPROVAL)}

## Stage57 Gray Candidate Evidence
{_section(r, LiveGrayReadonlySealCategory.STAGE57_GRAY_CANDIDATE)}

## Stage56 Real Cache Quality Evidence
{_section(r, LiveGrayReadonlySealCategory.STAGE56_REAL_CACHE_QUALITY)}

## Stage55 QMT Dry-run Calibration Evidence
{_section(r, LiveGrayReadonlySealCategory.STAGE55_QMT_DRYRUN_CALIBRATION)}

## Material Lock Report
{_items(r.material_lock_items)}

## Pre-run Checklist
{_items(r.checklist_items)}

## Read-only Seal Manifest
{_manifest(r.manifest_items)}

## Final Signoff Recheck
{_items(r.signoff_items)}

## Roadmap Stage Plan Evidence
{_section(r, LiveGrayReadonlySealCategory.ROADMAP_STAGE_PLAN)}

## UI Productization Plan Evidence
- 本阶段继续检查完整 Stage1-75 工程阶段计划和 Stage61-75 UI 产品化计划；不提前开发 UI。
- UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

## Next Pre-gray Review Plan
{_items(r.next_plan_items)}

## Required Manual Confirmations
- 人工确认 Stage59 不代表实盘授权。
- 人工确认 READY_FOR_READONLY_SEAL_REVIEW 只表示灰度前只读封版与运行前检查清单材料可供人工复核。
- 人工确认 Stage60 仍不得直接实盘。

## Blocking Reasons
{chr(10).join('- '+x for x in r.blocking_reasons) or '- 无'}

## Warnings
{chr(10).join('- '+x for x in r.warnings) or '- 无'}

## Next Stage Preview
Stage60 仍不得直接实盘；只能做预灰度最终复核与 go/no-go 材料，不调用 xttrader、不查询真实账户、不下单。
'''
def format_material_lock_report_markdown(r): return '# Stage59 Material Lock Report\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n\n- 只读锁定声明：本报告仅封存材料。\n- 不代表实盘授权声明：本报告不产生真实交易授权。\n'
def format_pre_run_checklist_report_markdown(r): return '# Stage59 Pre-run Checklist\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
def format_readonly_seal_manifest_report_markdown(r): return '# Stage59 Read-only Seal Manifest\n\n'+r.safety_note+'\n\n'+_manifest(r.items)+'\n'
def format_final_signoff_recheck_report_markdown(r): return '# Stage59 Final Signoff Recheck\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
def format_next_pre_gray_review_plan_report_markdown(r): return '# Stage60 Next Pre-gray Review Plan\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
