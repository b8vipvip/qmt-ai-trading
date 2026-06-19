from __future__ import annotations
import json
from dataclasses import asdict
from .models import *
def _v(x): return x.value if hasattr(x,'value') else x
def _bul(items, attr='summary'):
    return "\n".join(f"- {getattr(i, attr, '') or getattr(i,'title','') or getattr(i,'name','')}: {getattr(i,'status','')} {getattr(i,'summary','')}" for i in items) or "- 无"
def format_qmt_dryrun_calibration_report_json(r): return json.dumps(to_plain(r),ensure_ascii=False,indent=2)
def format_qmt_dryrun_calibration_report_markdown(r):
    return f"""# Stage55 QMT Dry-run Environment Calibration

## Decision
{_v(r.decision)}

## Safety Note
{r.safety_note}

## Evidence Summary
- total_evidence={r.summary.get('total_evidence', len(r.evidence))}
- critical={r.summary.get('critical', 0)}
- warnings={len(r.warnings)}
- no_trade_authorization=True

## Stage54 Gap Clearance Evidence
{_bul([e for e in r.evidence if _v(e.category)=='STAGE54_GAP_CLEARANCE'])}

## QMT / MiniQMT Path Evidence
{_bul(r.qmt_paths)}

## xtdata Capability Evidence
{_bul(r.xtdata_capabilities, 'summary')}

## Cache Roundtrip Evidence
{_bul(r.cache_roundtrip)}

## Field Mapping Evidence
{_bul(r.field_mapping)}

## ETF Whitelist Evidence
{_bul(r.etf_whitelist)}

## Roadmap Stage Plan Evidence
{_bul([e for e in r.evidence if _v(e.category)=='ROADMAP_STAGE_PLAN'])}

## UI Productization Plan Evidence
{_bul([e for e in r.evidence if _v(e.category)=='UI_PRODUCTIZATION_PLAN'])}

## QMT Dry-run Calibration Review
READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW 不是实盘授权；仅表示材料可供人工复核。

## xtdata Capability Report
覆盖 xtquant import、xtdata import、只读行情函数、禁止 xttrader import、禁止账户查询/交易函数、unavailable 降级、只读 smoke test。

## ETF Whitelist Calibration
覆盖 ETF universe 读取、代码格式、max_symbols、whitelist 限制、不扩大标的池、不代表实盘授权。

## Next Real Cache Quality Plan
{_bul(r.next_real_cache_quality_plan)}

## Required Manual Confirmations
{chr(10).join('- '+x for x in r.required_manual_confirmations)}

## Blocking Reasons
{chr(10).join('- '+x for x in r.blocking_reasons) or '- 无'}

## Warnings
{chr(10).join('- '+x for x in r.warnings) or '- 无'}

## Next Stage Preview
Stage56 仍不得直接实盘；只能做真实缓存质量复核与长期样本补齐，不调用 xttrader、不查询真实账户、不下单。
"""
def format_xtdata_capability_report_markdown(r): return f"# Stage55 xtdata Capability Report\n\n## Decision\n{_v(r.decision)}\n\n## Safety Note\n{r.safety_note}\n\n## Coverage\n- xtquant import\n- xtdata import\n- xtdata 只读行情函数存在性\n- 禁止 xttrader import 检查\n- 禁止账户查询函数检查\n- 禁止交易函数检查\n- xtdata unavailable 时的降级说明\n- 只读 smoke test 结果\n\n## Items\n{_bul(r.items)}\n"
def format_etf_whitelist_calibration_markdown(r): return f"# Stage55 ETF Whitelist Calibration\n\n## Decision\n{_v(r.decision)}\n\n## Safety Note\n{r.safety_note}\n\n## Coverage\nETF universe 文件 / 默认标的池读取状态、标的代码格式、max_symbols 限制、symbol whitelist 限制、不扩大标的池声明、不代表实盘授权声明。\n\n## Items\n{_bul(r.items)}\n"
def format_next_real_cache_quality_plan_markdown(r): return f"# Stage56 Next Real Cache Quality Plan\n\n## Decision\n{_v(r.decision)}\n\n## Safety Note\n{r.safety_note}\n\n## Items\n{_bul(r.items)}\n"
def format_report_json(r): return json.dumps(to_plain(r),ensure_ascii=False,indent=2)
