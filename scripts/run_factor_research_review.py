from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.research.factor_registry import catalog_as_dict
from qmt_ai_trading.research.factor_config import config_seed_as_dict
from qmt_ai_trading.research.factor_engine import run_factor_scan

def write_json_md(out:Path,name:str,obj):
    (out/f'{name}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/f'{name}.md').write_text('# '+name+'\n\n```json\n'+json.dumps(obj,ensure_ascii=False,indent=2)+'\n```\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--output-dir',default='local_console_factor_stage79'); ap.add_argument('--app-dir',default='local_console_app_stage79'); a=ap.parse_args()
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    scan=run_factor_scan({'universe':'ETF','start_date':'2026-03-21','end_date':'2026-06-18','frequency':'1d','factor_set':['momentum_20d','volatility_20d','volume_ratio_20d']})
    write_json_md(out,'factor_catalog',catalog_as_dict()); write_json_md(out,'factor_config_seed',config_seed_as_dict()); write_json_md(out,'factor_results',scan['factor_results']); write_json_md(out,'factor_evaluation',scan['factor_evaluation']); write_json_md(out,'factor_candidates',scan['factor_candidates']); write_json_md(out,'factor_report',scan['factor_report'])
    contract={'menus':['总览','行情数据','AI 模型配置','因子研究','选股中心','策略任务','Agent 投研','回测分析','风控中心','报告中心','任务中心','系统设置'],'apis':['GET /api/v1/factors/catalog','GET /api/v1/factors/config','GET /api/v1/factors/results','GET /api/v1/factors/evaluation','GET /api/v1/factors/candidates','POST /api/v1/tasks/run factor_scan']}
    write_json_md(out,'frontend_factor_contract',contract)
    plan={'stage80':'阶段八十：因子候选池到 Strategy Engine dry-run TradeIntent 联调层','not_live_trading':True}
    write_json_md(out,'next_strategy_integration_plan',plan)
if __name__=='__main__': main()
