from __future__ import annotations
from .safety import with_safety

def build_attribution(shadow, metrics, context):
    rows=shadow.get('shadow_replay',[])
    contrib=[{'symbol':r['symbol'],'return_contribution':r.get('mock_return',0),'drawdown_contribution':r.get('max_drawdown',0),'factor_link':'Stage79 candidate','risk_note':'watch only; not executable'} for r in rows]
    return with_safety({'performance_attribution':contrib,'top_contributors':contrib[:3],'risk_contributors':sorted(contrib,key=lambda x:x['drawdown_contribution'],reverse=True)[:3],'portfolio_summary':{'total_return':metrics.get('total_return'),'max_drawdown':metrics.get('max_drawdown'),'sharpe_like':metrics.get('sharpe_like')}})
