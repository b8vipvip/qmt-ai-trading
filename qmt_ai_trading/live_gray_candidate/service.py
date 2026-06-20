from __future__ import annotations
import json
from pathlib import Path
from .models import *
from .collector import collect_live_gray_candidate_evidence
from .formatters import *

def build_default_live_gray_candidate_config(**kwargs):
    cfg=LiveGrayCandidateConfig()
    for k,v in kwargs.items(): setattr(cfg,k,v)
    cfg.gray_total_capital_limit=min(float(cfg.gray_total_capital_limit),1000.0); cfg.single_trade_capital_limit=min(float(cfg.single_trade_capital_limit), cfg.gray_total_capital_limit, 200.0); cfg.daily_trade_capital_limit=min(float(cfg.daily_trade_capital_limit), cfg.gray_total_capital_limit, 300.0); cfg.max_single_symbol_weight=min(float(cfg.max_single_symbol_weight),0.20); cfg.max_portfolio_exposure=min(float(cfg.max_portfolio_exposure),0.50); cfg.cash_reserve_ratio=max(float(cfg.cash_reserve_ratio),0.50); cfg.max_positions=min(int(cfg.max_positions),2); cfg.max_orders_per_day=min(int(cfg.max_orders_per_day),2)
    return cfg

def _capital(cfg):
    return [GrayCapitalLimitItem("小资金灰度资金上限", f"{cfg.gray_total_capital_limit:.2f}", summary="只用于候选计划"), GrayCapitalLimitItem("单笔交易上限", f"{cfg.single_trade_capital_limit:.2f}"), GrayCapitalLimitItem("单日交易上限", f"{cfg.daily_trade_capital_limit:.2f}"), GrayCapitalLimitItem("现金保留比例", f"{cfg.cash_reserve_ratio:.2%}")]
def _risk(cfg):
    return [GrayRiskLimitItem("总资金上限",f"{cfg.gray_total_capital_limit:.2f}","超限阻断"),GrayRiskLimitItem("单笔上限",f"{cfg.single_trade_capital_limit:.2f}","超限阻断"),GrayRiskLimitItem("单日上限",f"{cfg.daily_trade_capital_limit:.2f}","超限阻断"),GrayRiskLimitItem("单标的上限",f"{cfg.max_single_symbol_weight:.0%}","超限阻断"),GrayRiskLimitItem("组合暴露上限",f"{cfg.max_portfolio_exposure:.0%}","超限阻断"),GrayRiskLimitItem("最大持仓数",str(cfg.max_positions),"超限阻断"),GrayRiskLimitItem("最大订单数",str(cfg.max_orders_per_day),"超限阻断"),GrayRiskLimitItem("最大单日亏损",f"{cfg.max_daily_loss_ratio:.0%}","触发熔断"),GrayRiskLimitItem("最大总回撤",f"{cfg.max_total_drawdown_ratio:.0%}","触发熔断"),GrayRiskLimitItem("熔断触发条件","数据质量/Risk Gate/Human Approval/连续错误异常","停止候选推进"),GrayRiskLimitItem("停止灰度条件","亏损/回撤/人工暂停/证据缺失","停止"),GrayRiskLimitItem("人工复核条件","任何 WARN/UNAVAILABLE/计划变更","人工复核")]
def _approval():
    names=["人工确认 Stage57 不代表实盘授权","人工确认候选资金上限","人工确认 ETF 白名单","人工确认 Risk Gate 不可绕过","人工确认 Human Approval 不可绕过","人工确认不自动 approve","人工确认未来真实执行仍需单独审批","人工确认不调用 xttrader","人工确认不真实下单","人工确认不查询真实账户"]
    return [GrayApprovalItem(n, True, "必须人工勾选确认") for n in names]
def _rollback():
    names=["数据质量异常回滚","Risk Gate 异常回滚","Human Approval 缺失回滚","单日亏损触发熔断","总回撤触发熔断","连续错误触发熔断","通知失败时处理","日志缺失时处理","人工暂停流程","恢复前复核流程"]
    return [GrayRollbackItem(n,n,"停止候选流程，保留材料，人工复核") for n in names]
def _stops(cfg):
    return [GrayStopConditionItem("单日亏损触发阈值",f"{cfg.max_daily_loss_ratio:.0%}"),GrayStopConditionItem("最大回撤触发阈值",f"{cfg.max_total_drawdown_ratio:.0%}"),GrayStopConditionItem("冷却期",f"{cfg.cooldown_days_after_stop} days")]
def _next():
    names=["灰度候选计划人工签字","资金上限人工确认","ETF 白名单人工确认","Risk Gate 规则复核","Human Approval 流程复核","Paper Trading / dry-run 证据复核","回滚 / 熔断计划复核","不调用 xttrader","不真实下单","不查询真实账户","不真实通知","下一阶段仍不自动实盘"]
    return [NextApprovalPackagePlanItem(n,"Stage58 最终人工审批包准备项") for n in names]

def run_live_gray_candidate(cfg):
    ev, symbols=collect_live_gray_candidate_evidence(cfg); block=[]; warn=[]
    for e in ev:
        if e.severity==LiveGrayCandidateSeverity.CRITICAL: block.append(e.summary)
        elif e.severity==LiveGrayCandidateSeverity.WARN: warn.append(e.summary)
    s56=next((e for e in ev if e.category==LiveGrayCandidateCategory.STAGE56_REAL_CACHE_QUALITY and e.metadata.get("decision") is not None), None)
    if block: dec=LiveGrayCandidateDecision.NO_GO
    elif s56 and s56.metadata.get("decision")=="READY_FOR_REAL_CACHE_QUALITY_REVIEW": dec=LiveGrayCandidateDecision.READY_FOR_GRAY_CANDIDATE_REVIEW
    else: dec=LiveGrayCandidateDecision.NEED_MORE_EVIDENCE
    return LiveGrayCandidateReport(dec, evidence=ev, allowed_symbols=symbols, capital_limits=_capital(cfg), risk_limits=_risk(cfg), approval_items=_approval(), rollback_items=_rollback(), stop_conditions=_stops(cfg), next_plan_items=_next(), blocking_reasons=block, warnings=warn, summary=to_plain(cfg))

def _save(md,j,mp,jp): Path(mp).parent.mkdir(parents=True,exist_ok=True); Path(jp).parent.mkdir(parents=True,exist_ok=True); Path(mp).write_text(md,encoding='utf-8'); Path(jp).write_text(j,encoding='utf-8')
def save_live_gray_candidate_report(r,o,j): _save(format_live_gray_candidate_report_markdown(r), format_live_gray_candidate_report_json(r), o, j)
def load_live_gray_candidate_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def run_gray_risk_limit_review(r): return GrayRiskLimitReport(r.risk_limits, r.decision)
def save_gray_risk_limit_report(r,o,j): _save(format_gray_risk_limit_report_markdown(r), format_simple_json(r), o, j)
def run_gray_approval_checklist(r): return GrayApprovalChecklistReport(r.approval_items, r.decision)
def save_gray_approval_checklist_report(r,o,j): _save(format_gray_approval_checklist_report_markdown(r), format_simple_json(r), o, j)
def run_gray_rollback_circuit_breaker_plan(r): return GrayRollbackCircuitBreakerReport(r.rollback_items, r.stop_conditions, r.decision)
def save_gray_rollback_circuit_breaker_report(r,o,j): _save(format_gray_rollback_circuit_breaker_report_markdown(r), format_simple_json(r), o, j)
def run_next_gray_approval_package_plan(r): return NextApprovalPackagePlanReport(r.next_plan_items, r.decision)
def save_next_gray_approval_package_plan_report(r,o,j): _save(format_next_gray_approval_package_plan_report_markdown(r), format_simple_json(r), o, j)
