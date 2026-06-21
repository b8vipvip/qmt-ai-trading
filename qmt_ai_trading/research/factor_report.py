from __future__ import annotations

def build_factor_report(results:list[dict], evaluation:dict, candidates:list[dict], params:dict)->dict:
    return {'title':'Stage79 因子研究工作台报告','summary':'基于 Data Hub mock ETF universe 的离线因子扫描；不接实盘、不下单、不查账户。','params':params,'result_count':len(results),'candidate_count':len(candidates),'IC':evaluation.get('IC'),'RankIC':evaluation.get('RankIC'),'not_live_trading':True}
