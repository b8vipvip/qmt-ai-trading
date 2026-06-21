from __future__ import annotations

def build_candidates(rows:list[dict], limit:int=5)->list[dict]:
    return [{'rank':r['rank'],'symbol':r['symbol'],'score':r.get('composite_score'),'reasons':r.get('reasons',[]),'risk_flags':r.get('risk_flags',['not_live_trading'])} for r in sorted(rows,key=lambda x:x.get('rank',999))[:limit]]
