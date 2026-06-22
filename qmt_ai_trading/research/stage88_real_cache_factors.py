from __future__ import annotations
import json, statistics
from pathlib import Path
SAFETY={'dry_run':True,'read_only':True,'not_live_trading':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'requires_human_approval':True}
def _ret(closes,n): return (closes[-1]/closes[-1-n]-1) if len(closes)>n and closes[-1-n] else 0.0
def compute_factors(cache):
    vals=[]
    for sym,item in cache.get('symbols',{}).items():
        bars=item.get('bars',[]); closes=[float(b['close']) for b in bars if 'close'in b]; vols=[float(b.get('volume',0)) for b in bars]
        r=[closes[i]/closes[i-1]-1 for i in range(1,len(closes))] if len(closes)>1 else [0]
        vol20=statistics.pstdev(r[-20:]) if len(r)>=2 else 0.0
        max20=max(closes[-20:]) if closes else 1; dd=closes[-1]/max20-1 if max20 else 0
        vc=(statistics.mean(vols[-5:])/statistics.mean(vols[-20:])-1) if len(vols)>=20 and statistics.mean(vols[-20:]) else 0
        m5=_ret(closes,5); m20=_ret(closes,20); score=round(m5*35+m20*45-vol20*10+vc*5+dd*5,6)
        flags=[]
        if vol20>.05: flags.append('high_volatility')
        if dd<-.08: flags.append('drawdown_watch')
        vals.append({'symbol':sym,'momentum_5':m5,'momentum_20':m20,'volatility_20':vol20,'volume_change_20':vc,'drawdown_20':dd,'composite_score':score,'risk_flags':flags,**SAFETY})
    return sorted(vals,key=lambda x:x['composite_score'],reverse=True)
def build_candidates(vals): return [{**v,'rank':i+1,'action_bias':'BUY' if i<2 and not v['risk_flags'] else 'HOLD'} for i,v in enumerate(vals)]
def write_research(repo_root='.', input_cache='local_console_datahub_stage88/datahub_real_cache.json', output_dir='local_console_research_stage88'):
    root=Path(repo_root); cache=json.loads((root/input_cache).read_text(encoding='utf-8'))
    vals=compute_factors(cache); cands=build_candidates(vals)
    ctx={'stage':'Stage88','input_cache':input_cache,'source':'Data Hub Real Cache',**SAFETY}
    report={'stage':'Stage88','module':'Research Factor Engine','status':'SUCCESS','factor_count':len(vals),'candidate_count':len(cands),**SAFETY}
    contract={'module':'stage88_research','apis':['/api/v1/stage88/research/factors','/api/v1/stage88/research/candidates'],**report}
    files={'research_input_context':ctx,'factor_values':{'factors':vals,**SAFETY},'factor_candidates':{'candidates':cands,**SAFETY},'factor_report':report,'frontend_research_contract':contract}
    out=root/output_dir; canon=root/'artifacts/reports/stage88/research'
    for base in [out,canon]:
      base.mkdir(parents=True,exist_ok=True)
      for stem,obj in files.items():
        (base/f'{stem}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8')
        (base/f'{stem}.md').write_text(f'# {stem}\n\n```json\n'+json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n```\n',encoding='utf-8')
    return report
