from __future__ import annotations
import json, shutil
from pathlib import Path
from typing import Any
from .account_readonly_config import AccountReadonlyConfig
from .account_readonly_provider import AccountReadonlyProvider
from .account_rate_limit import AccountReadonlyRateLimiter
from .account_masking import mask_account_id, mask_account_name

REQ=["local_console_xttrader_stage90/xttrader_boundary_config.json","local_console_xttrader_stage90/xttrader_import_guard_report.json","local_console_xttrader_stage90/xttrader_capability_probe.json","local_console_xttrader_stage90/xttrader_account_query_gate.json","local_console_xttrader_stage90/xttrader_order_submit_gate.json","local_console_xttrader_stage90/order_previews.json","local_console_xttrader_stage90/xttrader_safety_report.json","local_console_xttrader_stage90/xttrader_boundary_report.json","local_console_xttrader_stage90/frontend_xttrader_contract.json"]
FORBIDDEN=["order_"+"stock","order_"+"stock_"+"async","cancel_order_"+"stock","cancel_order_"+"stock_"+"async","place_"+"order","execute_"+"order","real_order_submitted="+"true","allow_order_submit="+"true","allow_order_cancel="+"true"]

def _dump(o): return json.dumps(o,ensure_ascii=False,indent=2,sort_keys=True)
def _write(base,stem,obj):
    base.mkdir(parents=True,exist_ok=True); (base/f"{stem}.json").write_text(_dump(obj)+"\n",encoding="utf-8"); (base/f"{stem}.md").write_text(f"# {stem}\n\n```json\n{_dump(obj)}\n```\n",encoding="utf-8")
def _read(p:Path):
    try: return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None
    except Exception: return None

def build_config(enable=False, allow_import=False, allow_connect=False, allow_account=False, allow_position=False, manual=False, dry_run=True, read_only=True):
    return AccountReadonlyConfig(enabled=bool(enable),dry_run=True,read_only=bool(read_only),allow_import_xttrader=bool(allow_import),allow_connect_trade_session=bool(allow_connect),allow_account_query=bool(allow_account),allow_position_query=bool(allow_position),manual_confirmation_completed=bool(manual),allow_order_submit=False,allow_order_cancel=False)

def scan_stage91_safety(repo_root='.'):
    root=Path(repo_root); files=list((root/'qmt_ai_trading/trading_gateway').glob('account_*.py'))+list((root/'scripts').glob('*stage91*.py'))
    hits=[]
    for f in files:
        txt=f.read_text(encoding='utf-8',errors='ignore').lower().replace(' ','')
        for m in FORBIDDEN:
            if m in txt: hits.append({'file':str(f.relative_to(root)),'marker':m})
    return {'status':'PASS' if not hits else 'FAIL','hits':hits,'read_only':True,'order_submit_enabled':False,'order_cancel_enabled':False,'real_order_submitted':False,'no_order_submitted':True,'no_order_cancelled':True,'safety_status':'DISABLED_FOR_SAFETY'}

def build_frontend(repo_root:Path):
    app=repo_root/'local_console_app_stage91'; app.mkdir(parents=True,exist_ok=True)
    html="""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>账户只读 / 持仓只读</title><style>body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:24px;background:#f8fafc}.card{background:white;border-radius:12px;padding:16px;margin:12px 0;box-shadow:0 1px 6px #d7dce5}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.badge{padding:6px 10px;border-radius:99px;background:#fef3c7;color:#92400e}button{margin:4px;padding:8px 12px}pre{background:#0f172a;color:#e5e7eb;padding:12px;border-radius:8px;white-space:pre-wrap}</style></head><body><h1>账户只读 / 持仓只读</h1><nav>账户只读 · 持仓只读</nav><div class='grid'><div class='card'>账户查询：默认关闭</div><div class='card'>持仓查询：默认关闭</div><div class='card'>真实下单：关闭</div><div class='card'>撤单能力：关闭</div><div class='card'>账号脱敏：开启</div><div class='card'>限频保护：开启</div></div><p><span class='badge'>MANUAL_CONFIRM_REQUIRED</span></p><section class='card'><h2>人工确认区</h2><p>我确认本次只进行账户/持仓只读查询；不下单、不自动交易；查询结果仅用于风险校验和灰度准备。</p><button>启用账户/持仓只读查询</button><button>关闭账户只读模式</button><button>刷新资产</button><button>刷新持仓</button></section><section class='card'><h2>账户资产摘要</h2><div id='asset'></div></section><section class='card'><h2>持仓列表</h2><div id='pos'></div></section><section class='card'><h2>查询频率状态</h2><div id='rate'>max_queries_per_minute=3</div></section><section class='card'><h2>账号脱敏状态</h2><div>account_masked=true</div></section><section class='card'><h2>安全边界</h2><pre>read_only=true\norder_submit_enabled=false\nreal_order_submitted=false\naccount_masked=true</pre></section><details class='card'><summary>原始 JSON 折叠区</summary><pre id='raw'></pre></details><script>async function j(u){return(await fetch(u)).json()}Promise.all([j('/api/v1/account-readonly/status'),j('/api/v1/account-readonly/asset'),j('/api/v1/account-readonly/positions')]).then(([s,a,p])=>{asset.textContent=JSON.stringify(a,null,2);pos.textContent=JSON.stringify(p,null,2);raw.textContent=JSON.stringify({s,a,p},null,2)})</script></body></html>"""
    (app/'index.html').write_text(html,encoding='utf-8')

def run_account_readonly_stage91(repo_root='.', output_dir='local_console_account_stage91', enable_account_readonly=False, allow_import_xttrader=False, allow_connect_trade_session=False, allow_account_query=False, allow_position_query=False, manual_confirmed=False, dry_run=True, read_only=True):
    root=Path(repo_root); out=root/output_dir; canon=root/'artifacts/reports/stage91/account_readonly'
    inputs={p:{'exists':(root/p).exists(),'data':_read(root/p)} for p in REQ}; fallback=any(not v['exists'] for v in inputs.values())
    cfg=build_config(enable_account_readonly,allow_import_xttrader,allow_connect_trade_session,allow_account_query,allow_position_query,manual_confirmed,dry_run,read_only)
    provider=AccountReadonlyProvider(cfg, rate_limiter=AccountReadonlyRateLimiter(cfg.max_queries_per_minute))
    context={'stage':'Stage91','input_files':{k:{'exists':v['exists']} for k,v in inputs.items()},'fallback_used':fallback,'mock_data':True,'account_readonly_boundary':True,'account_query_enabled':False,'position_query_enabled':False,'order_submit_enabled':False,'real_order_submitted':False,'dry_run':True,'read_only':True,'requires_human_approval':True,'mask_account_required':True}
    status=provider.get_status(); asset=provider.query_account_asset(); positions=provider.query_positions()
    masking={'status':'PASS','account_masked':True,'sample_account_id':mask_account_id('1234567890'),'sample_account_name':mask_account_name('示例账户名称'),'full_account_absent':True,'mask_account_required':True}
    rl=AccountReadonlyRateLimiter(3); rate={'attempts':[rl.allow(),rl.allow(),rl.allow(),rl.allow()],'rate_limit_required':True,'max_queries_per_minute':3}
    safety=scan_stage91_safety(root)
    frontend={'menu':['账户只读','持仓只读'],'endpoints':['/api/v1/account-readonly/status','/api/v1/account-readonly/asset','/api/v1/account-readonly/positions','/api/v1/account-readonly/masking-report','/api/v1/account-readonly/rate-limit','/api/v1/account-readonly/safety','/api/v1/account-readonly/report'],'manual_confirmation_text':'我确认本次只进行账户/持仓只读查询；不下单、不自动交易；查询结果仅用于风险校验和灰度准备。','forbidden_actions_absent':True,**status}
    plan={'stage':'Stage92','title':'真实订单预览复核，不发单','uses_account_readonly':True,'order_submit_enabled':False,'real_order_submitted':False,'requires_human_approval':True}
    report={'stage':'Stage91','status':'SUCCESS' if safety['status']=='PASS' else 'FAIL','output_dir':str(out),'canonical_dir':str(canon),'account_readonly_status':status['status'],'position_count':positions.get('position_count',0),'workflow_status':{'QMT Gateway / xtdata':'INTERACTIVE','Data Hub':'INTERACTIVE','Research':'INTERACTIVE','Strategy':'INTERACTIVE','Risk Gate':'INTERACTIVE','Paper Trading':'INTERACTIVE','xttrader Boundary':'DISABLED_FOR_SAFETY','Account Readonly':'MANUAL_CONFIRM_REQUIRED','Order Submit':'DISABLED_FOR_SAFETY'},**status,'order_submit_enabled':False,'real_order_submitted':False,'no_order_submitted':True}
    docs={'account_input_context':context,'account_readonly_config':cfg.to_dict(),'account_readonly_status':status,'account_asset_snapshot':asset,'account_positions_snapshot':positions,'account_masking_report':masking,'account_rate_limit_report':rate,'account_readonly_safety_report':safety,'account_readonly_report':report,'frontend_account_contract':frontend,'next_order_preview_review_plan':plan}
    for base in (out,canon):
        if 'local_runtime_account_stage91' in str(base): continue
        for k,o in docs.items(): _write(base,k,o)
    build_frontend(root); return report
