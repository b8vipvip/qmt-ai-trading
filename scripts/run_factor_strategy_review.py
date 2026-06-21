from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.research.factor_engine import run_factor_scan
from qmt_ai_trading.strategies.factor_strategy_engine import build_factor_strategy
from qmt_ai_trading.risk.factor_strategy_risk_review import review_trade_intents
from qmt_ai_trading.strategies.strategy_report import build_strategy_report

def write_json(p: Path, obj): p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
def write_md(p: Path, title: str, obj): p.write_text(f"# {title}\n\n```json\n{json.dumps(obj, ensure_ascii=False, indent=2)}\n```\n", encoding='utf-8')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root', default='.'); ap.add_argument('--factor-dir', default='local_console_factor_stage79'); ap.add_argument('--output-dir', default='local_console_strategy_stage80'); ap.add_argument('--app-dir', default='local_console_app_stage77'); args=ap.parse_args()
    root=Path(args.repo_root); out=root/args.output_dir; out.mkdir(parents=True, exist_ok=True)
    scan=run_factor_scan({'factor_set':['momentum_20d','volatility_20d','volume_ratio_20d']})
    built=build_factor_strategy(scan['factor_candidates'], 3)
    decisions=review_trade_intents(built['trade_intents'])
    report=build_strategy_report(built['strategy_signals'], built['trade_intents'], decisions)
    artifacts={
      'factor_strategy_signals': built['strategy_signals'], 'factor_trade_intents': built['trade_intents'], 'factor_risk_decisions': decisions, 'factor_strategy_report': report,
      'frontend_strategy_contract': {'menu':'策略任务','apis':['/api/v1/strategy/factor-signals','/api/v1/strategy/trade-intents','/api/v1/strategy/risk-decisions','/api/v1/strategy/report'],'button':'生成 dry-run TradeIntent','warnings':['mock_data','not_live_trading']},
      'next_agent_research_plan': {'stage81':'TradingAgents 多 Agent 投研工作台与模型用途映射联调层','live_trading':False},
      'run_qmt_tasks_logging_fix_report': {'target':'../run_qmt_tasks.ps1','validation_logs':'validation_logs/stage<stage>_validation_<yyyyMMdd_HHmmss>.log','installed_by':'scripts/install_run_qmt_tasks_logging.ps1','validate_stage80_auto_installs':True}
    }
    for name,obj in artifacts.items(): write_json(out/f'{name}.json', obj); write_md(out/f'{name}.md', name, obj)
if __name__ == '__main__': main()
