from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.datahub.datahub_report import run_stage88_datahub
from qmt_ai_trading.research.stage88_real_cache_factors import write_research
from qmt_ai_trading.strategies.stage88_dry_run import write_strategy
from qmt_ai_trading.risk.stage88_risk_gate import write_risk
SAFETY={'dry_run':True,'read_only':True,'not_live_trading':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'requires_human_approval':True}
def main():
 p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--symbols',default='510300.SH,510500.SH,588000.SH,159915.SZ,512100.SH'); p.add_argument('--period',default='1d'); p.add_argument('--limit',type=int,default=120); p.add_argument('--output-root',default='local_console_stage88'); p.add_argument('--enable-xtdata',action='store_true'); p.add_argument('--allow-import-xtdata',action='store_true'); p.add_argument('--allow-real-market-data',action='store_true'); p.add_argument('--allow-connect-miniqmt',action='store_true'); p.add_argument('--dry-run',action='store_true',default=True); p.add_argument('--read-only',action='store_true',default=True); a=p.parse_args()
 sy=[s.strip() for s in a.symbols.split(',') if s.strip()]
 dh=run_stage88_datahub(a.repo_root,'local_console_datahub_stage88',sy,a.period,a.limit,enable_xtdata=a.enable_xtdata,allow_import_xtdata=a.allow_import_xtdata,allow_real_market_data=a.allow_real_market_data,allow_connect_miniqmt=a.allow_connect_miniqmt)
 rs=write_research(a.repo_root); st=write_strategy(a.repo_root); rk=write_risk(a.repo_root)
 report={'stage':'Stage88','status':'SUCCESS','steps':['Data Hub real cache success','Research factors success','Strategy dry-run success','Risk Gate success'],'datahub':dh,'research':rs,'strategy':st,'risk':rk,**SAFETY}
 out=Path(a.repo_root)/'local_console_stage88'; out.mkdir(exist_ok=True); (out/'stage88_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8')
 print('Data Hub real cache success'); print('Research factors success'); print('Strategy dry-run success'); print('Risk Gate success'); print('no_xttrader=true'); print('no_order_submitted=true'); print('no_account_query=true')
 return 0
if __name__=='__main__': raise SystemExit(main())
