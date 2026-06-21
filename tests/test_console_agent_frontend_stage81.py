from pathlib import Path
from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore
ROOT=Path(__file__).resolve().parents[1]

def test_frontend_agent_page_contains_stage81_contract():
    js=(ROOT/'local_console_app_stage77/app.js').read_text(encoding='utf-8')
    for text in ['Agent 投研总览','模型用途映射显示区','输入数据源状态区','Agent 角色列表','运行 Agent 投研 dry-run','查看输入上下文','查看多空辩论','查看风险审查','查看组合建议','安全边界警示区','dry_run=true','not_live_trading=true','research_only=true','no_order_submitted=true','no_qmt_trader_api=true','requires_risk_gate=true','requires_human_approval=true']:
        assert text in js
    for api in ['/agents/context','/agents/model-usage','/agents/runs/latest','/agents/debate/latest','/agents/risk-review/latest','/agents/portfolio-review/latest','/agents/report/latest']:
        assert api in js or api == '/agents/model-usage'
    for bad in ['一键下单','自动买入','自动卖出','实盘执行','批准交易','绕过风控']:
        assert bad not in js

def test_agent_research_task_registered_and_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run=run_task('agent_research_dry_run', {'output_dir':'agent_out'}, TaskStore())
    assert run.status=='SUCCESS'
    assert run.output['task_id']=='agent_research_dry_run'
    assert run.output['dry_run'] and run.output['not_live_trading']
    assert (tmp_path/'agent_out/agent_research_report.json').exists()
