from __future__ import annotations
from .models import ConsoleTask
TASK_SPECS=[
('data_cache_check','本地缓存质量检查','DATA','检查测试缓存完整性与缺口'),('qmt_data_diagnostics_readonly','QMT 行情只读诊断','DATA','仅检查行情可读性，不接账户'),('market_snapshot_readonly','只读行情快照','DATA','读取本地/模拟 OHLCV 快照'),
('research_score_etf','ETF 研究评分','RESEARCH','输出 ETF score/rank/reasons'),('model_lab_evaluate','模型实验评估','RESEARCH','dry-run 模型指标摘要'),('factor_scan','多因子扫描','RESEARCH','生成多因子候选'),
('etf_rotation_candidates','ETF 轮动候选','STRATEGY','生成候选池，不下单'),('strategy_dry_run_signals','策略 dry-run 信号','STRATEGY','输出 dry-run signal / TradeIntent'),('daily_pipeline_dry_run','日线流水线 dry-run','STRATEGY','固定模板运行日线任务'),
('agent_research_brief','Agent 投研简报','AGENTS','结构化建议'),('agent_risk_review','Agent 风险复核','AGENTS','结构化风险建议'),('agent_portfolio_review','Agent 组合复核','AGENTS','组合建议，不交易'),
('shadow_replay_backtest','Shadow Replay 回测','BACKTEST','回放式回测摘要'),('backtest_report','回测报告生成','BACKTEST','生成回测摘要'),
('risk_gate_dry_run_check','Risk Gate dry-run','RISK','风控闸门校验'),('live_readiness_blockers_review','实盘阻断项复核','RISK','列出阻断项'),
('generate_daily_report','生成日报','REPORT','生成 dry-run 报告摘要'),('list_latest_reports','最新报告列表','REPORT','列出白名单报告摘要')]
def _schema(): return {'symbol': {'type':'string','required':False}, 'limit': {'type':'integer','min':1,'max':20,'required':False}}
def build_task(task_id,title,cat,desc): return ConsoleTask(task_id,title,cat,desc,_schema(),{'limit':5},True,True,False,True,'python_callable','mock_safe_task',[f'{task_id}_summary.json'])
TASK_REGISTRY={tid:build_task(tid,t,c,d) for tid,t,c,d in TASK_SPECS}
def list_tasks(): return list(TASK_REGISTRY.values())
def get_task(task_id): return TASK_REGISTRY.get(task_id)
