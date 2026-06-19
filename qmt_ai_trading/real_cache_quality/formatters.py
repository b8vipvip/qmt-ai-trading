from __future__ import annotations
import json
from .models import *
def _v(x): return x.value if hasattr(x,'value') else x
def _bul(items): return '\n'.join(f"- {getattr(i,'title',getattr(i,'symbol',''))}: {_v(getattr(i,'status',''))} {getattr(i,'summary','')}" for i in items) or '- 无'
def format_real_cache_quality_report_json(r): return json.dumps(to_plain(r),ensure_ascii=False,indent=2)
def format_real_cache_quality_report_markdown(r):
    return f"""# Stage56 Real Cache Quality Review and Long Sample Gap Fill

## Decision
{_v(r.decision)}

## Safety Note
本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。
READY_FOR_REAL_CACHE_QUALITY_REVIEW 只表示真实缓存质量复核与长期样本补齐材料可供人工复核。

## Evidence Summary
- evidence={len(r.evidence)}
- coverage_symbols={len(r.coverage)}
- field_quality_items={len(r.field_quality)}
- no_trade_authorization=True

## Stage55 QMT Dry-run Calibration Evidence
{_bul([e for e in r.evidence if _v(e.category)=='STAGE55_QMT_DRYRUN_CALIBRATION'])}

## Cache Root Evidence
{_bul([e for e in r.evidence if _v(e.category)=='CACHE_COVERAGE'])}

## ETF Whitelist Evidence
{_bul([e for e in r.evidence if _v(e.category)=='ETF_WHITELIST'])}

## Cache Coverage Evidence
{_bul(r.coverage)}

## Long Sample Completeness Evidence
{_bul(r.long_sample)}

## Field Quality Evidence
{_bul(r.field_quality)}

## Roadmap Stage Plan Evidence
{_bul([e for e in r.evidence if _v(e.category)=='ROADMAP_STAGE_PLAN'])}

## UI Productization Plan Evidence
{_bul([e for e in r.evidence if _v(e.category)=='UI_PRODUCTIZATION_PLAN'])}

## Real Cache Quality Review
包含 Stage55 读取状态、缓存 root、ETF universe/whitelist、symbol 覆盖率、bar count、缺失率、重复值、OHLC、成交量/成交额、交易日/时间字段复核。本阶段材料状态不代表实盘授权。

## Long Sample Gap Fill Plan
目标样本区间 target_days={r.summary.get('target_days',90)}；缺失 symbol/日期仅生成摘要。未来只允许 xtdata 只读补齐，不调用 xttrader，不真实下单，不查询真实账户。

## Field Quality Review
date/time、open/high/low/close、volume、amount、非负、OHLC 逻辑、重复值、缺失值均按本地缓存只读复核；异常字段需人工修复建议。

## Next Backtest Attribution Plan
Stage57 前准备长期回测区间、ETF universe、基准收益曲线、策略收益曲线、最大回撤、胜率/盈亏比、换手率、因子贡献、交易成本模拟、风险暴露；不调用 xttrader、不真实下单、不查询真实账户、不真实通知。

## Required Manual Confirmations
- 人工确认 Stage55 输出与本地缓存可信度。
- 人工确认停牌 / 无成交日期处理策略。
- 人工确认前复权 / 不复权一致性说明。

## Blocking Reasons
{chr(10).join('- '+x for x in r.blocking_reasons) or '- 无'}

## Warnings
{chr(10).join('- '+x for x in r.warnings) or '- 无'}

## Next Stage Preview
Stage57 仍不得直接实盘；只能做小资金灰度候选计划生成，不调用 xttrader、不查询真实账户、不下单。
"""
def format_long_sample_gap_fill_report_markdown(r): return '# Stage56 Long Sample Gap Fill Plan\n\n目标样本区间、当前样本覆盖、缺失 symbol、缺失日期摘要、mock 补齐 roundtrip、未来 xtdata 只读补齐计划。\n\n- 不调用 xttrader\n- 不真实下单\n- 不查询真实账户\n'+'\n'.join(f'- {i.symbol}: current_days={i.current_days}, target_days={i.target_days}, {i.missing_summary}' for i in r.items)
def format_field_quality_review_report_markdown(r): return '# Stage56 Field Quality Review\n\n覆盖 date/time、open/high/low/close、volume、amount、非负检查、OHLC 逻辑、重复值、缺失值、异常字段修复建议。\n'+'\n'.join(f'- {i.symbol} {i.field}: {_v(i.status)} {i.summary}' for i in r.items)
def format_next_backtest_attribution_plan_report_markdown(r): return '# Stage56 Next Backtest Attribution Plan\n\n- 长期回测区间选择\n- ETF universe 样本选择\n- 基准收益曲线\n- 策略收益曲线\n- 最大回撤\n- 胜率 / 盈亏比\n- 换手率\n- 因子贡献\n- 交易成本模拟\n- 风险暴露\n- 不调用 xttrader\n- 不真实下单\n- 不查询真实账户\n- 不真实通知\n'+'\n'.join(f'- {i.name}: {i.summary}' for i in r.items)
def format_simple_json(r): return json.dumps(to_plain(r),ensure_ascii=False,indent=2)
