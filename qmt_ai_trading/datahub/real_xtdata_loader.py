from __future__ import annotations
import json
from pathlib import Path
SAFETY={'dry_run':True,'read_only':True,'not_live_trading':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'requires_human_approval':True}

def _mock_bars(symbols, limit):
    bars=[]
    for s_i,s in enumerate(symbols):
        base=3.0+s_i*.35
        for i in range(limit):
            close=round(base+i*.01,4); vol=1000000+s_i*100000+i*1000
            bars.append({'symbol':s,'timestamp':f'2026-01-{(i%28)+1:02d}T15:00:00+00:00','open':round(close-.02,4),'high':round(close+.03,4),'low':round(close-.05,4),'close':close,'volume':vol,'amount':round(close*vol,2),'timeframe':'1d','mock_data':True,'source':'stage88_fallback_mock',**SAFETY})
    return bars

def load_stage88_bars(repo_root='.', symbols=None, period='1d', limit=120, enable_xtdata=False, allow_import_xtdata=False, allow_real_market_data=False, allow_connect_miniqmt=False):
    root=Path(repo_root); symbols=symbols or ['510300.SH','510500.SH','588000.SH','159915.SZ','512100.SH']
    ctx={'stage':'Stage88','source':'stage87_artifact_or_xtdata_provider','symbols':symbols,'period':period,'limit':limit,**SAFETY}
    bars=[]; warnings=[]; status={}
    if enable_xtdata:
        from qmt_ai_trading.market_gateway.xtdata_live_provider import XtDataLiveReadOnlyProvider
        from qmt_ai_trading.market_gateway.xtdata_live_config import XtDataLiveReadOnlyConfig
        provider=XtDataLiveReadOnlyProvider(XtDataLiveReadOnlyConfig(enabled=True,allow_import_xtdata=allow_import_xtdata,allow_real_market_data=allow_real_market_data,allow_connect_miniqmt=allow_connect_miniqmt,read_only=True,allow_xttrader=False,allow_account_query=False,allow_order_submit=False,symbols=symbols,period=period,limit=limit))
        status=provider.get_status()
        for sym in symbols:
            bars.extend(provider.get_bars(sym,period,limit).get('bars',[]))
    else:
        p=root/'local_console_xtdata_live_stage87'/'xtdata_live_bars.json'
        sp=root/'local_console_xtdata_live_stage87'/'xtdata_live_status.json'
        if p.exists():
            data=json.loads(p.read_text(encoding='utf-8')); bars=data.get('bars',[]); status=json.loads(sp.read_text(encoding='utf-8')) if sp.exists() else {}
            ctx['stage87_input_found']=True
        else:
            warnings.append('Stage87 xtdata live bars missing; fallback mock data used')
            bars=_mock_bars(symbols, limit); status={'real_market_data':False,'sandbox_fallback':True,'mock_data':True}
            ctx.update({'fallback_used':True,'mock_data':True,'real_market_data':False})
    wanted=set(symbols); bars=[{**b,**SAFETY} for b in bars if b.get('symbol') in wanted][:limit*len(wanted)]
    fallback=not bool(status.get('real_market_data'))
    ctx.update({'fallback_used':fallback,'mock_data':fallback,'real_market_data':bool(status.get('real_market_data')),'sandbox_fallback':bool(status.get('sandbox_fallback',fallback)),'xtdata_imported':bool(status.get('xtdata_imported')),'mini_qmt_connected':bool(status.get('mini_qmt_connected')),'warnings':warnings})
    return ctx,bars,status
