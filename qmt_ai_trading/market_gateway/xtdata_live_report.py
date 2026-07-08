from __future__ import annotations
import json, hashlib
from pathlib import Path
from .xtdata_live_config import XtDataLiveReadOnlyConfig
from .xtdata_live_provider import XtDataLiveReadOnlyProvider
from .xtdata_live_safety import evaluate_live_config, scan_xtdata_live_safety

INPUTS=['docs/qmt-ai-trading-project-roadmap.md','docs/qmt-ai-trading-architecture.md','local_console_xtdata_enable_stage86/xtdata_enable_report.json','local_console_xtdata_enable_stage86/xtdata_enable_decision.json','local_console_xtdata_enable_stage86/xtdata_environment_check.json','local_console_xtdata_enable_stage86/xtdata_manual_checklist.json','local_console_xtdata_enable_stage86/frontend_xtdata_enable_contract.json','local_console_xtdata_stage85/xtdata_boundary_report.json','local_console_xtdata_stage85/xtdata_adapter_config.json','local_console_xtdata_stage85/xtdata_safety_report.json','local_console_market_stage84/market_gateway_report.json','local_console_market_stage84/market_symbols.json','local_console_market_stage84/frontend_market_contract.json']


from qmt_ai_trading.common.json_safe import json_safe as _json_safe

def _load(root, rel):
    p=root/rel
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: return {'error':str(e),'path':rel}

def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True); text=json.dumps(_json_safe(data), ensure_ascii=False, indent=2, sort_keys=True)
    if not path.exists() or path.read_text(encoding='utf-8') != text: path.write_text(text,encoding='utf-8')

def _md(path, title, data):
    text='# '+title+'\n\n```json\n'+json.dumps(_json_safe(data), ensure_ascii=False, indent=2, sort_keys=True)+'\n```\n'
    if not path.exists() or path.read_text(encoding='utf-8') != text: path.write_text(text,encoding='utf-8')

def _first_error(*docs):
    for doc in docs:
        if isinstance(doc, dict):
            for key in ('error_message','get_full_tick_error','get_market_data_ex_error','error'):
                if doc.get(key):
                    return str(doc.get(key))
    return ''

def _collect_symbol_bars(provider, symbols, period, limit):
    all_rows=[]; per_symbol=[]
    real_any=False; fallback_any=False; errors=[]
    for symbol in symbols:
        item=provider.get_bars(symbol, period, limit)
        per_symbol.append(item)
        real_any=real_any or bool(item.get('real_market_data'))
        fallback_any=fallback_any or bool(item.get('sandbox_fallback'))
        if item.get('error_message') or item.get('get_market_data_ex_error'):
            errors.append(item.get('error_message') or item.get('get_market_data_ex_error'))
        for row in item.get('bars') or []:
            if isinstance(row, dict):
                copied=dict(row); copied.setdefault('symbol', symbol); all_rows.append(copied)
    return {'status':'REAL_MARKET_DATA' if real_any else 'FALLBACK_TO_SANDBOX','symbol':'MULTI','symbols':symbols,'period':period,'limit':limit,'bars':all_rows,'per_symbol':per_symbol,'real_market_data':real_any,'sandbox_fallback':fallback_any,'error_message':'; '.join(errors[:3]) if errors else ''}

def run_xtdata_live_stage87(repo_root='.', output_dir='local_console_xtdata_live_stage87', **kwargs):
    root=Path(repo_root); out=root/output_dir
    loaded={rel:_load(root,rel) for rel in INPUTS}; missing=[k for k,v in loaded.items() if v is None]
    h=hashlib.sha256(json.dumps(loaded,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()[:12]
    cfg_data=XtDataLiveReadOnlyConfig().to_dict(); cfg_data.update({k:v for k,v in kwargs.items() if k in cfg_data and v is not None})
    cfg_data['limit']=max(1,min(int(cfg_data.get('limit',100)),500)); cfg=XtDataLiveReadOnlyConfig(**cfg_data)
    provider=XtDataLiveReadOnlyProvider(cfg); status=provider.get_status(); snapshots=provider.get_snapshot(cfg.symbols); bars=_collect_symbol_bars(provider, cfg.symbols, cfg.period, cfg.limit)
    safety=evaluate_live_config(cfg); scan=scan_xtdata_live_safety([root/'qmt_ai_trading'/'market_gateway'/'xtdata_live_provider.py', root/'qmt_ai_trading'/'market_gateway'/'xtdata_live_safety.py']); safety['import_scan']=scan
    real_market_data=bool(status.get('real_market_data') and (bars.get('real_market_data') or snapshots.get('real_market_data')))
    sandbox_fallback=bool(status.get('sandbox_fallback',True) or bars.get('sandbox_fallback',False) or snapshots.get('sandbox_fallback',False) or not real_market_data)
    failure_reason=_first_error(status, snapshots, bars)
    if not failure_reason and sandbox_fallback:
        failure_reason='真实 xtdata 未启用、不可用，或 QMT 客户端未启动/未登录，已回退到沙盒行情。'
    context={'stage':'Stage87','created_at':f'2026-01-01T00:00:00+00:00#Stage87-{h}','input_files':INPUTS,'missing_inputs':missing,'fallback_used':bool(missing) or sandbox_fallback,'sandbox_fallback':sandbox_fallback,'read_only':True,'not_live_trading':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True}
    report={'stage':'Stage87','status':'REAL_MARKET_DATA' if real_market_data else 'FALLBACK_TO_SANDBOX','task_id':'xtdata_live_readonly_smoke','output_dir':output_dir,'provider':'xtdata_live_readonly','symbols':cfg.symbols,'symbol_count':len(cfg.symbols),'bar_count':len(bars.get('bars') or []),'real_market_data':real_market_data,'sandbox_fallback':sandbox_fallback,'qmt_login_required':True,'qmt_started_or_xtdata_imported':bool(status.get('xtdata_imported')),'mini_qmt_connected':bool(status.get('mini_qmt_connected') or snapshots.get('mini_qmt_connected') or bars.get('mini_qmt_connected')),'import_status':status.get('import_status'),'status_message':status.get('status'),'snapshot_status':snapshots.get('status'),'bars_status':bars.get('status'),'failure_reason':failure_reason,'read_only':True,'not_live_trading':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'allow_xttrader':False,'allow_order_submit':False,'allow_account_query':False,'safety_status':safety['safety_status'],'api_count':6}
    frontend={'page':'xtdata 只读行情','apis':['GET /api/v1/market/xtdata-live/status','GET /api/v1/market/xtdata-live/snapshots','GET /api/v1/market/xtdata-live/bars','GET /api/v1/market/xtdata-live/safety','GET /api/v1/market/xtdata-live/report','POST /api/v1/tasks/run task_id=xtdata_live_readonly_smoke'],'sections':['xtdata 连接状态','MiniQMT 状态','当前 provider','行情 snapshot 表格','K线 bars 表格','sandbox fallback 状态','安全边界说明','禁止交易项检查'],'read_only':True,'no_xttrader':True,'no_order_submitted':True,'no_account_query':True,'allow_order_submit':False,'allow_xttrader':False}
    files={'xtdata_live_input_context':context,'xtdata_live_config':cfg.to_dict(),'xtdata_live_status':status,'xtdata_live_snapshots':snapshots,'xtdata_live_bars':bars,'xtdata_live_safety_report':safety,'xtdata_live_report':report,'frontend_xtdata_live_contract':frontend}
    for n,d in files.items(): _write(out/f'{n}.json',d); _md(out/f'{n}.md',n,d)
    return _json_safe(report)
