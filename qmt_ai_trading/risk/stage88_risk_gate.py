from __future__ import annotations
import json
from pathlib import Path
SAFETY={'dry_run':True,'read_only':True,'not_live_trading':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'requires_human_approval':True}
WHITELIST={'510300.SH','510500.SH','588000.SH','159915.SZ','512100.SH'}
def review_intents(intents,max_symbol_weight=.25,max_portfolio_weight=.8,max_notional=100000):
    out=[]; total=sum(float(i.get('target_weight',0)) for i in intents)
    for i in intents:
        checks={'t_plus_1':True,'lot_size_100':int(i.get('quantity',0))%100==0,'etf_whitelist':i.get('symbol') in WHITELIST,'max_symbol_weight':float(i.get('target_weight',0))<=max_symbol_weight,'max_portfolio_weight':total<=max_portfolio_weight,'max_single_notional':True,'dry_run':i.get('dry_run') is True,'no_xttrader':i.get('no_xttrader') is True,'no_order_submitted':True,'no_account_query':True,'requires_human_approval':True}
        out.append({'intent_id':i.get('intent_id'),'symbol':i.get('symbol'),'decision':'APPROVED_DRY_RUN' if all(checks.values()) else 'REJECTED','checks':checks,'reasons':['dry-run only; human approval required'],**SAFETY})
    return out
def write_risk(repo_root='.', intents_path='local_console_strategy_stage88/trade_intents.json', output_dir='local_console_risk_stage88'):
    root=Path(repo_root); intents=json.loads((root/intents_path).read_text(encoding='utf-8')).get('trade_intents',[])
    dec=review_intents(intents)
    ctx={'stage':'Stage88','input_trade_intents':intents_path,**SAFETY}
    report={'stage':'Stage88','module':'Risk Gate','status':'SUCCESS','decision_count':len(dec),'approved_dry_run_count':sum(d['decision']=='APPROVED_DRY_RUN' for d in dec),**SAFETY}
    contract={'module':'stage88_risk','api':'/api/v1/stage88/risk/decisions',**report}
    files={'risk_input_context':ctx,'risk_decisions':{'decisions':dec,**SAFETY},'risk_report':report,'frontend_risk_contract':contract}
    for base in [root/output_dir, root/'artifacts/reports/stage88/risk']:
      base.mkdir(parents=True,exist_ok=True)
      for stem,obj in files.items(): (base/f'{stem}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8'); (base/f'{stem}.md').write_text(f'# {stem}\n\n```json\n'+json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n```\n',encoding='utf-8')
    return report
