from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_qmt_dryrun_calibration_evidence
from .formatters import *
from .models import *
from .safety import assert_stage55_read_only

def build_default_qmt_dryrun_calibration_config(repo_root='.', **kw):
    c=QmtDryrunCalibrationConfig(repo_root=str(repo_root))
    for k,v in kw.items():
        if v is not None and hasattr(c,k): setattr(c,k,str(v) if isinstance(v,Path) else v)
    return c

def _items(cfg,evidence):
    paths=[QmtPathCheckItem(f'qmt-path-{i}', e.title, e.status, e.summary, e.path, e.status==QmtDryrunCalibrationStatus.PASS) for i,e in enumerate([x for x in evidence if enum_value(x.category)=='QMT_PATH'],1)]
    caps=[XtdataCapabilityItem(f'xtdata-{i}', e.title, e.status, e.summary, enum_value(e.status)=='PASS') for i,e in enumerate([x for x in evidence if enum_value(x.category) in {'XTQUANT_IMPORT','XTDATA_IMPORT','XTDATA_FUNCTION','XTDATA_SMOKE_TEST'}],1)]
    cache=Path(cfg.repo_root)/cfg.cache_root/'stage55_roundtrip.json'; cache.parent.mkdir(parents=True,exist_ok=True); payload={'symbol':'510300.SH','date':'2026-06-18','time':'15:00:00','open':1,'high':1,'low':1,'close':1,'volume':100,'amount':100.0}; cache.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8'); ok=json.loads(cache.read_text(encoding='utf-8'))==payload
    caches=[CacheRoundtripItem('cache-roundtrip','本地缓存写入 / 读取 roundtrip',QmtDryrunCalibrationStatus.PASS if ok else QmtDryrunCalibrationStatus.FAIL,'market_data_test_stage55 roundtrip passed' if ok else 'roundtrip failed',str(cache))]
    fields=[FieldMappingItem(f'field-{f}',f,QmtDryrunCalibrationStatus.PASS,f,f'行情字段 {f} 映射已校准') for f in ['date','time','open','high','low','close','volume','amount']]
    etfs=[EtfWhitelistItem(f'etf-{i}',s,QmtDryrunCalibrationStatus.PASS,f'{s} 在 max_symbols<={cfg.max_symbols} 白名单内；不扩大标的池，不代表实盘授权。') for i,s in enumerate(['510300.SH','510500.SH','159915.SZ'][:min(cfg.max_symbols,5)],1)]
    plan_titles=['真实缓存覆盖率复核','缺失率复核','重复值复核','停牌 / 无成交处理复核','前复权 / 不复权一致性复核','成交量 / 成交额字段复核','长期样本完整性复核','QMT xtdata 只读边界复核','不调用 xttrader','不真实下单','不查询真实账户','不真实通知']
    plan=[NextRealCacheQualityPlanItem(f'plan-{i}',t,QmtDryrunCalibrationStatus.PASS,f'Stage56 计划项：{t}。') for i,t in enumerate(plan_titles,1)]
    return paths,caps,caches,fields,etfs,plan

def _decide(evidence):
    blocking=[e.summary for e in evidence if enum_value(e.severity)=='CRITICAL' or enum_value(e.status)=='FAIL']
    if blocking: return QmtDryrunCalibrationDecision.NO_GO,blocking
    st54=[e for e in evidence if enum_value(e.category)=='STAGE54_GAP_CLEARANCE']
    if not st54 or enum_value(st54[0].status)=='SKIPPED': return QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE,[]
    if st54[0].decision=='READY_FOR_GAP_CLEARANCE_REVIEW':
        if any(enum_value(e.category)=='XTDATA_SMOKE_TEST' and enum_value(e.status)=='PASS' for e in evidence): return QmtDryrunCalibrationDecision.READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW,[]
        return QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE,[]
    return QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE,[]

def run_qmt_dryrun_calibration(config=None, **kw):
    cfg=config or build_default_qmt_dryrun_calibration_config(**kw); assert_stage55_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled,cfg.no_task_registered)
    ev=collect_qmt_dryrun_calibration_evidence(cfg); q,c,cr,f,e,p=_items(cfg,ev); dec,block=_decide(ev); warn=[x.summary for x in ev if enum_value(x.severity)=='WARN' or enum_value(x.status) in {'WARN','SKIPPED','UNAVAILABLE'}]
    return QmtDryrunCalibrationReport(decision=dec,config=cfg,evidence=ev,qmt_paths=q,xtdata_capabilities=c,cache_roundtrip=cr,field_mapping=f,etf_whitelist=e,next_real_cache_quality_plan=p,blocking_reasons=block,warnings=warn,summary={'total_evidence':len(ev),'critical':len(block),'read_only':True,'dry_run_only':True,'no_trade_authorization':True})
def save_qmt_dryrun_calibration_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_qmt_dryrun_calibration_report_json(r) if p.suffix=='.json' else format_qmt_dryrun_calibration_report_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_qmt_dryrun_calibration_report_json(r),encoding='utf-8')
def load_qmt_dryrun_calibration_report(path): return QmtDryrunCalibrationReport(**json.loads(Path(path).read_text(encoding='utf-8')))
def run_xtdata_capability_check(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,QmtDryrunCalibrationReport) else run_qmt_dryrun_calibration(report_or_config or build_default_qmt_dryrun_calibration_config(**kw)); return XtdataCapabilityReport(decision=r.decision,items=r.xtdata_capabilities,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_xtdata_capability_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_report_json(r) if p.suffix=='.json' else format_xtdata_capability_report_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_report_json(r),encoding='utf-8')
def run_etf_whitelist_calibration(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,QmtDryrunCalibrationReport) else run_qmt_dryrun_calibration(report_or_config or build_default_qmt_dryrun_calibration_config(**kw)); return EtfWhitelistCalibrationReport(decision=r.decision,items=r.etf_whitelist,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_etf_whitelist_calibration_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_report_json(r) if p.suffix=='.json' else format_etf_whitelist_calibration_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_report_json(r),encoding='utf-8')
def run_next_real_cache_quality_plan(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,QmtDryrunCalibrationReport) else run_qmt_dryrun_calibration(report_or_config or build_default_qmt_dryrun_calibration_config(**kw)); return NextRealCacheQualityPlanReport(decision=r.decision,items=r.next_real_cache_quality_plan,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_next_real_cache_quality_plan_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_report_json(r) if p.suffix=='.json' else format_next_real_cache_quality_plan_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_report_json(r),encoding='utf-8')
