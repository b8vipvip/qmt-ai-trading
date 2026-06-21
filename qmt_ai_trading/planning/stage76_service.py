from __future__ import annotations
import json
from pathlib import Path
from .stage76_models import *
from .stage76_reader import read_json
from .stage76_formatters import format_stage76_report_md, json_md
from .stage76_safety import assert_read_only

def build_default_stage76_config(**kw): return Stage76RoadmapReviewConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _evidence(stage,path):
    obj=read_json(path); data=obj.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}; crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0) if isinstance(data,dict) else 0
    return Stage76Evidence(stage,obj['source'],Stage76ReviewStatus.PASS if obj['status']=='PASS' else Stage76ReviewStatus.UNAVAILABLE,str(data.get('decision','')) if isinstance(data,dict) else '',crit,obj['summary'],obj.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else [])

def build_completed_stage_summary(): return [CompletedStageSummaryItem()]
def build_ui_productization_recap(): return [UiProductizationRecapItem()]
def build_architecture_alignment(): return [ArchitectureAlignmentItem(), ArchitectureAlignmentItem('UI 执行边界',Stage76ReviewStatus.PASS,'UI 只读复核，不能直接访问 QMT，不能绕过 Risk Gate / Human Approval。')]
def build_safety_boundary(): return [SafetyBoundaryRecapItem('不调用 xttrader'), SafetyBoundaryRecapItem('不下单'), SafetyBoundaryRecapItem('不查询真实账户'), SafetyBoundaryRecapItem('不真实发送通知'), SafetyBoundaryRecapItem('不自动 approve')]
def build_data_quality_gaps(): return [DataQualityGapItem('没有完成真实缓存长期质量验证'),DataQualityGapItem('没有完成真实 QMT 环境下 xtdata 稳定性复核'),DataQualityGapItem('mock fallback 使用限制仍需实盘前复核')]
def build_trading_readiness_gaps(): return [TradingReadinessGapItem('没有完成 Paper Trading 长周期复盘'),TradingReadinessGapItem('没有完成小资金灰度参数'),TradingReadinessGapItem('没有完成资金管理与组合层在真实数据上的充分验证')]
def build_ui_maturity(): return [UiMaturityItem(), UiMaturityItem('Stage75 UI 产品化收口',Stage76ReviewStatus.PASS,'READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW 不是交易授权，UI 完成不等于实盘可用。')]
def build_live_readiness_blockers():
    return [LiveReadinessBlocker(x) for x in ['没有完成新的实盘前安全审计重启','没有完成真实缓存长期质量验证','没有完成 Paper Trading 长周期复盘','没有完成小资金灰度参数','没有完成真实 QMT 环境下 xtdata 稳定性复核','没有完成真实通知通道安全审查','没有完成异常监控 / 熔断 / 告警闭环','没有完成 live config 多重确认','没有完成资金管理与组合层在真实数据上的充分验证','UI 完成不等于交易链路成熟']]
def build_next_roadmap(): return [NextRoadmapStageItem('Stage77','实盘前安全审计重启与真实数据质量复核层','P0','仍不直接实盘，只做审计与复核。'),NextRoadmapStageItem('Stage78','真实缓存长期质量报告与异常监控层','P0','继续数据质量与监控验证，不直接实盘。'),NextRoadmapStageItem('Stage79','Paper Trading 长周期复盘与归因层','P1','只做长周期 paper 复盘，不直接实盘。'),NextRoadmapStageItem('Stage80','小资金灰度参数草案与人工审批流程复核层','P1','只形成草案与人工审批复核，不直接实盘。')]
def build_priority_matrix(): return [NextPriorityMatrixItem('安全审计重启','P0'),NextPriorityMatrixItem('真实缓存质量','P0'),NextPriorityMatrixItem('异常监控闭环','P0'),NextPriorityMatrixItem('Paper Trading 长周期复盘','P1'),NextPriorityMatrixItem('小资金灰度参数草案','P1')]
def build_stage77_plan(): return [Stage77PlanItem('重启实盘前安全审计','P0','仍不直接实盘，不调用 xttrader，不查询真实账户，不下单。'),Stage77PlanItem('复核真实缓存质量与 xtdata 稳定性','P0','只复核数据质量，不查询真实账户。'),Stage77PlanItem('复核 live config 多重确认','P0','不启用实盘，只检查确认机制。'),Stage77PlanItem('复核异常监控 / 熔断 / 告警闭环','P0','不发送真实通知。')]

def run_stage76_roadmap_review(config=None):
    cfg=config or Stage76RoadmapReviewConfig(); assert_read_only(cfg.read_only,cfg.no_trade_authorization); root=Path(cfg.repo_root)
    ev=[_evidence('Stage75',root/cfg.closure_dir/'ui_productization_closure_report.json'),_evidence('Stage74',root/cfg.demo_dir/'local_console_demo_package_report.json'),_evidence('Stage73',root/cfg.help_dir/'local_console_help_docs_report.json'),_evidence('Stage72',root/cfg.acceptance_dir/'local_console_ui_acceptance_report.json'),_evidence('Stage71',root/cfg.review_dir/'local_console_review_workbench_report.json')]
    warnings=[]; blocking=[]
    if ev[0].status==Stage76ReviewStatus.UNAVAILABLE: warnings.append('Stage75 closure package unavailable; roadmap review needs more evidence')
    if ev[0].decision=='NO_GO' or ev[0].critical_count>0: blocking.append('Stage75 NO_GO or critical findings present')
    decision=Stage76RoadmapReviewDecision.READY_FOR_NEXT_ROADMAP_REVIEW
    if ev[0].status==Stage76ReviewStatus.UNAVAILABLE: decision=Stage76RoadmapReviewDecision.NEED_MORE_EVIDENCE
    if blocking: decision=Stage76RoadmapReviewDecision.NO_GO
    crit=len(blocking)
    return Stage76RoadmapReviewReport(decision,cfg,ev,build_completed_stage_summary(),build_ui_productization_recap(),build_architecture_alignment(),build_safety_boundary(),build_data_quality_gaps(),build_trading_readiness_gaps(),build_ui_maturity(),build_live_readiness_blockers(),build_next_roadmap(),build_priority_matrix(),build_stage77_plan(),warnings,blocking,summary={'critical_count':crit,'read_only':True,'no_trade_authorization':True})

def save_all_reports(r, paths: dict[str,str]):
    mapping={'output':(format_stage76_report_md(r),r),'completed_output':(json_md('Stage76 Completed Stage Summary',r.completed_stage_summary),r.completed_stage_summary),'ui_output':(json_md('Stage76 UI Productization Recap',r.ui_productization_recap),r.ui_productization_recap),'architecture_output':(json_md('Stage76 Architecture Alignment Review',Stage76ArchitectureReviewReport(r.architecture_alignment)),Stage76ArchitectureReviewReport(r.architecture_alignment)),'safety_output':(json_md('Stage76 Safety Boundary Review',Stage76SafetyBoundaryReviewReport(r.safety_boundary)),Stage76SafetyBoundaryReviewReport(r.safety_boundary)),'data_output':(json_md('Stage76 Data Quality Gap Review',Stage76DataQualityGapReport(r.data_quality_gaps)),Stage76DataQualityGapReport(r.data_quality_gaps)),'trading_output':(json_md('Stage76 Trading Readiness Gap Review',Stage76TradingReadinessGapReport(r.trading_readiness_gaps)),Stage76TradingReadinessGapReport(r.trading_readiness_gaps)),'ui_maturity_output':(json_md('Stage76 UI Maturity Review',Stage76UiMaturityReport(r.ui_maturity)),Stage76UiMaturityReport(r.ui_maturity)),'blockers_output':(json_md('Stage76 Live Readiness Blockers',r.live_readiness_blockers),r.live_readiness_blockers),'next_output':(json_md('Stage76 Next Roadmap Plan',Stage76NextRoadmapPlanReport(r.next_roadmap,r.priority_matrix)),Stage76NextRoadmapPlanReport(r.next_roadmap,r.priority_matrix)),'stage77_output':(json_md('Stage76 Stage77 Plan',r.stage77_plan),r.stage77_plan)}
    for key,(md,obj) in mapping.items():
        if paths.get(key): _write(paths[key],md)
        jk=key.replace('_output','_json_output') if key!='output' else 'json_output'
        if paths.get(jk): _write_json(paths[jk],obj)
