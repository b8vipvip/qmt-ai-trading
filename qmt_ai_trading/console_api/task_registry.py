from __future__ import annotations
from .models import ConsoleTask
TASK_SPECS=[
('data_cache_check','本地缓存质量检查','DATA','检查测试缓存完整性与缺口'),('qmt_data_diagnostics_readonly','QMT 行情只读诊断','DATA','仅检查行情可读性，不接账户'),('market_snapshot_readonly','只读行情快照','DATA','读取本地/模拟 OHLCV 快照'),
('research_score_etf','ETF 研究评分','RESEARCH','输出 ETF score/rank/reasons'),('model_lab_evaluate','模型实验评估','RESEARCH','dry-run 模型指标摘要'),('factor_scan','多因子扫描','RESEARCH','生成多因子候选'),
('etf_rotation_candidates','ETF 轮动候选','STRATEGY','生成候选池，不下单'),('strategy_dry_run_signals','策略 dry-run 信号','STRATEGY','输出 dry-run signal / TradeIntent'),('factor_strategy_dry_run','因子策略 dry-run 联调','STRATEGY','读取 factor_candidates 生成 TradeIntent 并进入 Risk Gate dry-run'),('daily_pipeline_dry_run','日线流水线 dry-run','STRATEGY','固定模板运行日线任务'),
('agent_research_dry_run','Agent 投研 dry-run','AGENTS','运行 Stage81 多 Agent 投研工作流'),('agent_research_brief','Agent 投研简报','AGENTS','结构化建议'),('agent_risk_review','Agent 风险复核','AGENTS','结构化风险建议'),('agent_portfolio_review','Agent 组合复核','AGENTS','组合建议，不交易'),
('shadow_replay_backtest','Shadow Replay 回测','BACKTEST','回放式回测摘要'),('backtest_report','回测报告生成','BACKTEST','生成回测摘要'),('backtest_dashboard_dry_run','回测分析联动看板 dry-run','BACKTEST','生成 Stage82 回测分析与 Agent 对比看板'),
('monitoring_alert_dry_run','监控告警 dry-run','RISK','生成 Stage83 异常监控、告警与熔断 dry-run 看板'),
('risk_gate_dry_run_check','Risk Gate dry-run','RISK','风控闸门校验'),('live_readiness_blockers_review','实盘阻断项复核','RISK','列出阻断项'),
('generate_daily_report','生成日报','REPORT','生成 dry-run 报告摘要'),('list_latest_reports','最新报告列表','REPORT','列出白名单报告摘要'),('ai_model_discovery','AI 模型发现','AI_PROVIDER','本地调用模型列表接口'),('ai_model_stress_test','AI 模型压力测试','AI_PROVIDER','串行 1000/3000/5000 字模型测试'),('ai_model_usage_draft','AI 模型用途映射草稿','AI_PROVIDER','保存 Agent 模型用途映射草稿')]
def _schema(): return {'symbol': {'type':'string','required':False}, 'limit': {'type':'integer','min':1,'max':20,'required':False}}
def build_task(task_id,title,cat,desc): return ConsoleTask(task_id,title,cat,desc,_schema(),{'limit':5},True,True,False,True,'python_callable','mock_safe_task',[f'{task_id}_summary.json'])
TASK_REGISTRY={tid:build_task(tid,t,c,d) for tid,t,c,d in TASK_SPECS}
def list_tasks(): return list(TASK_REGISTRY.values())
def get_task(task_id): return TASK_REGISTRY.get(task_id)
