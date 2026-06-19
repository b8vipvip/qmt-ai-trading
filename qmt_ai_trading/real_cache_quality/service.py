from __future__ import annotations
import json
from pathlib import Path
from .models import *
from .collector import collect_real_cache_quality_evidence
from .cache_probe import probe_cache_coverage, probe_long_sample_completeness, probe_field_quality
from .formatters import *

def build_default_real_cache_quality_config(**kwargs):
    cfg=RealCacheQualityConfig();
    for k,v in kwargs.items(): setattr(cfg,k,v)
    cfg.max_symbols=min(int(cfg.max_symbols),5); cfg.min_days=min(int(cfg.min_days),90)
    return cfg
def _decide(ev, coverage, fields):
    crit=[e.summary for e in ev if e.severity==RealCacheQualitySeverity.CRITICAL]
    if crit: return RealCacheQualityDecision.NO_GO, crit
    if not coverage or any(e.status in (RealCacheQualityStatus.UNAVAILABLE,RealCacheQualityStatus.WARN) for e in ev): return RealCacheQualityDecision.NEED_MORE_EVIDENCE, []
    if any(f.status==RealCacheQualityStatus.FAIL for f in fields): return RealCacheQualityDecision.NEED_MORE_EVIDENCE, []
    return RealCacheQualityDecision.READY_FOR_REAL_CACHE_QUALITY_REVIEW, []
def run_real_cache_quality(cfg: RealCacheQualityConfig):
    ev=collect_real_cache_quality_evidence(cfg); root=Path(cfg.repo_root)/Path(cfg.cache_root)
    coverage=probe_cache_coverage(root,cfg.max_symbols); long=probe_long_sample_completeness(root,cfg.min_days,cfg.max_symbols); fields=probe_field_quality(root,cfg.max_symbols)
    dec,block=_decide(ev,coverage,fields)
    warns=sorted({e.summary for e in ev if e.severity==RealCacheQualitySeverity.WARN} | {f.summary for f in fields if f.status==RealCacheQualityStatus.FAIL})
    return RealCacheQualityReport(decision=dec,evidence=ev,coverage=coverage,long_sample=long,field_quality=fields,blocking_reasons=block,warnings=warns,summary={'target_days':cfg.target_days,'provider':cfg.provider})
def _save(md,json_text,mp,jp):
    Path(mp).parent.mkdir(parents=True,exist_ok=True); Path(jp).parent.mkdir(parents=True,exist_ok=True); Path(mp).write_text(md,encoding='utf-8'); Path(jp).write_text(json_text,encoding='utf-8')
def save_real_cache_quality_report(r, output, json_output): _save(format_real_cache_quality_report_markdown(r),format_real_cache_quality_report_json(r),output,json_output)
def load_real_cache_quality_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def run_long_sample_gap_fill_plan(r): return LongSampleGapFillReport([GapFillPlanItem(x.symbol,r.summary.get('target_days',90),x.bar_count,'missing_days_summary=人工复核；缓存不足则使用 mock/xtdata 只读补齐') for x in r.coverage], r.decision)
def save_long_sample_gap_fill_report(r, output, json_output): _save(format_long_sample_gap_fill_report_markdown(r),format_simple_json(r),output,json_output)
def run_field_quality_review(r): return FieldQualityReviewReport(r.field_quality, r.decision)
def save_field_quality_review_report(r, output, json_output): _save(format_field_quality_review_report_markdown(r),format_simple_json(r),output,json_output)
def run_next_backtest_attribution_plan(r):
    names=['长期回测区间选择','ETF universe 样本选择','基准收益曲线','策略收益曲线','最大回撤','胜率 / 盈亏比','换手率','因子贡献','交易成本模拟','风险暴露','不调用 xttrader','不真实下单','不查询真实账户','不真实通知']
    return NextBacktestAttributionPlanReport([NextBacktestAttributionPlanItem(n,'Stage57/后续长期回测与绩效归因准备项') for n in names], r.decision)
def save_next_backtest_attribution_plan_report(r, output, json_output): _save(format_next_backtest_attribution_plan_report_markdown(r),format_simple_json(r),output,json_output)
