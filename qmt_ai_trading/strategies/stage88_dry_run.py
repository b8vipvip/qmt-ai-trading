from __future__ import annotations
import json
from pathlib import Path
SAFETY={'dry_run':True,'read_only':True,'not_live_trading':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'requires_human_approval':True}
WHITELIST={'510300.SH','510500.SH','588000.SH','159915.SZ','512100.SH'}
def build_strategy(candidates,max_weight=.25):
    signals=[]; intents=[]
    for c in candidates:
        if c['symbol'] not in WHITELIST: continue
        action='buy' if c.get('rank',99)<=2 and not c.get('risk_flags') else 'hold'
        weight=round(min(max_weight, max(0.0, float(c.get('composite_score',0))/5)),4) if action=='buy' else 0.0
        sig={'symbol':c['symbol'],'signal':action.upper(),'target_weight':weight,'score':c.get('composite_score'),**SAFETY}
        signals.append(sig); intents.append({'intent_id':f"stage88-{c['symbol']}",'symbol':c['symbol'],'side':action,'quantity':0 if action=='hold' else 100,'target_weight':weight,'max_weight':max_weight,'dry_run_only':True,**SAFETY})
    return signals,intents
def write_strategy(repo_root='.', candidates_path='local_console_research_stage88/factor_candidates.json', output_dir='local_console_strategy_stage88'):
    root=Path(repo_root); c=json.loads((root/candidates_path).read_text(encoding='utf-8')).get('candidates',[])
    sig,intents=build_strategy(c)
    ctx={'stage':'Stage88','input_candidates':candidates_path,'allowed_universe':sorted(WHITELIST),**SAFETY}
    report={'stage':'Stage88','module':'Strategy Engine','status':'SUCCESS','signal_count':len(sig),'trade_intent_count':len(intents),**SAFETY}
    contract={'module':'stage88_strategy','apis':['/api/v1/stage88/strategy/signals','/api/v1/stage88/strategy/trade-intents'],**report}
    files={'strategy_input_context':ctx,'strategy_signals':{'signals':sig,**SAFETY},'trade_intents':{'trade_intents':intents,**SAFETY},'strategy_report':report,'frontend_strategy_contract':contract}
    for base in [root/output_dir, root/'artifacts/reports/stage88/strategy']:
      base.mkdir(parents=True,exist_ok=True)
      for stem,obj in files.items(): (base/f'{stem}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8'); (base/f'{stem}.md').write_text(f'# {stem}\n\n```json\n'+json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n```\n',encoding='utf-8')
    return report
