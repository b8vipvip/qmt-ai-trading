from __future__ import annotations
import json
from .models import *

def format_json(obj): return json.dumps(to_plain(obj),ensure_ascii=False,indent=2)
def _items(items):
    return '\n'.join(f"- {getattr(i,'name','')}: status={getattr(i,'status','')} active={getattr(i,'active','')} satisfied={getattr(i,'satisfied','')} summary={getattr(i,'summary','')}" for i in items) or '- （无）'
def _ev(ev): return '\n'.join(f"- {e.title}: {e.status.value}/{e.severity.value} - {e.summary} ({e.path})" for e in ev) or '- （无）'

def format_pre_gray_final_review_report_markdown(r: PreGrayFinalReviewReport)->str:
    return f"""# Stage60 Pre-gray Final Review and Go/No-go Draft

## Decision
{r.decision.value}

## Go/No-go Draft
{r.go_no_go_decision.value}

## Safety Note
本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。
READY_FOR_PRE_GRAY_FINAL_REVIEW 只表示预灰度最终复核与 go/no-go 材料可供人工复核。
GO_DRAFT 不是实盘授权。

## Evidence Summary
{_ev(r.evidence)}

## Stage59 Read-only Seal Evidence
{_ev([e for e in r.evidence if e.category==PreGrayFinalReviewCategory.STAGE59_READONLY_SEAL])}

## Stage58 Final Approval Evidence
{_ev([e for e in r.evidence if e.category==PreGrayFinalReviewCategory.STAGE58_FINAL_APPROVAL])}

## Stage57 Gray Candidate Evidence
{_ev([e for e in r.evidence if e.category==PreGrayFinalReviewCategory.STAGE57_GRAY_CANDIDATE])}

## Stage56 Real Cache Quality Evidence
{_ev([e for e in r.evidence if e.category==PreGrayFinalReviewCategory.STAGE56_REAL_CACHE_QUALITY])}

## Stage55 QMT Dry-run Calibration Evidence
{_ev([e for e in r.evidence if e.category==PreGrayFinalReviewCategory.STAGE55_QMT_DRYRUN_CALIBRATION])}

## Material Recheck
{_items(r.material_items)}

## Pre-run Checklist Recheck
{_items(r.checklist_items)}

## Manifest Hash Recheck
{_items(r.manifest_items)}

## Risk Gate Final Recheck
{_items([i for i in r.risk_human_items if 'Risk' in i.name or '风控' in i.name])}

## Human Approval Final Recheck
{_items([i for i in r.risk_human_items if 'Human' in i.name or '人工' in i.name or 'Approval' in i.name])}

## Paper Trading / Dry-run Evidence Recheck
{_items(r.paper_items)}

## Register Preview Recheck
- register preview 必须 dry-run only / no task registered；不注册真实 Windows 任务。

## No-go Blockers
{_items(r.blockers)}

## Go Conditions
{_items(r.conditions)}

## Stage61 API Gateway Plan
{_items(r.stage61_items)}

## Roadmap Stage Plan Evidence
{_ev([e for e in r.evidence if e.category==PreGrayFinalReviewCategory.ROADMAP_STAGE_PLAN])}

## UI Productization Plan Evidence
- 已保留 Stage61-75 UI 产品化路线。UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

## Required Manual Confirmations
- 人工确认本材料不代表实盘授权。
- 人工确认 GO_DRAFT 不代表实盘授权。
- 人工确认仍不得自动实盘、不得自动 approve。

## Blocking Reasons
{chr(10).join('- '+x for x in r.blocking_reasons) or '- （无）'}

## Warnings
{chr(10).join('- '+x for x in r.warnings) or '- （无）'}

## Next Stage Preview
Stage61 进入 API Gateway 基础层和 UI 产品化路线；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
"""

def format_material_recheck_report_markdown(r): return '# Stage60 Material Recheck\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
def format_go_no_go_draft_report_markdown(r): return f"# Stage60 Go/No-go Draft\n\n## go/no-go 草案状态\n{r.decision.value}\n\n## GO_DRAFT / NO_GO_DRAFT / NEED_MORE_EVIDENCE_DRAFT\n{r.decision.value}\n\n## 通过条件\n- Stage55-59 READY 且 critical=0；manifest/hash 完整；register preview dry-run only/no task registered。\n\n## 阻断条件\n- 任一 NO_GO、critical>0、真实交易/账户查询/自动 approve。\n\n## 缺证条件\n- 缺 required manifest/hash/checklist/signoff。\n\n## 人工复核条件\n- 必须人工复核，本材料不可自动批准。\n\n## 不代表实盘授权声明\nGO_DRAFT 不是实盘授权。\n\n## 仍不得自动实盘声明\n仍不得自动实盘，不下单，不调用 xttrader。\n\n"+_items(r.items)+'\n'
def format_no_go_blocker_report_markdown(r): return '# Stage60 No-go Blockers\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
def format_go_condition_report_markdown(r): return '# Stage60 Go Conditions\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
def format_stage61_api_gateway_plan_report_markdown(r): return '# Stage61 API Gateway Plan\n\n'+r.safety_note+'\n\n'+_items(r.items)+'\n'
