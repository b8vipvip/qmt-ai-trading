from __future__ import annotations
import json, hashlib
from pathlib import Path
from .sandbox_gateway import SandboxMarketDataGateway
from .replay_bus import ReplayBus
from .data_quality import build_quality_report
from .safety import safety_report
STABLE_TS='2026-01-01T00:00:00+00:00'
def write_json_if_changed(path, data):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); text=json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)
    if not p.exists() or p.read_text(encoding='utf-8')!=text: p.write_text(text,encoding='utf-8')
def write_text_if_changed(path, text):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists() or p.read_text(encoding='utf-8')!=text: p.write_text(text,encoding='utf-8')
def md(title, data): return '# '+title+'\n\n```json\n'+json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n```\n'
def run_market_gateway_stage84(repo_root='.', output_dir='local_console_market_stage84', provider='mock_provider', symbols=None, timeframe='1d', limit=20, speed=1.0):
    root=Path(repo_root); out=root/output_dir; symbols=symbols or ['510300.SH','510500.SH','588000.SH']
    gw=SandboxMarketDataGateway(provider_type=provider); syms=[s.to_dict() for s in gw.list_symbols()]; snaps=[s.to_dict() for s in gw.get_snapshot(symbols)]; bars=[]
    for s in symbols: bars.extend([b.to_dict() for b in gw.get_bars(s,timeframe, min(limit,20))])
    session=gw.subscribe(symbols).to_dict(); session.update({'speed':speed,'limit':limit})
    events=ReplayBus(gw,speed).replay(symbols,timeframe,limit); session['event_count']=len(events); quality=build_quality_report(syms,snaps,bars)
    ctx={'stage':'Stage84','created_at':STABLE_TS,'input_files':['docs/qmt-ai-trading-project-roadmap.md','docs/qmt-ai-trading-architecture.md'],'fallback_used':True,'mock_data':provider=='mock_provider','recorded_data':provider=='recorded_provider','not_live_trading':True,'research_only':True,'sandbox_only':True,'sandbox':True,'read_only':True,'no_qmt_trader_api':True,'no_order_submitted':True,'provider':provider,'symbols':symbols}
    contract={'page':'行情回放','apis':['GET /api/v1/market/sandbox/context','GET /api/v1/market/sandbox/symbols','GET /api/v1/market/sandbox/snapshots','GET /api/v1/market/sandbox/bars','GET /api/v1/market/sandbox/replay/latest','GET /api/v1/market/sandbox/quality/latest','GET /api/v1/market/sandbox/report/latest','POST /api/v1/tasks/run task_id=market_replay_sandbox'],'sections':['Sandbox 行情网关状态','Provider 类型显示','标的列表','行情快照表','K线数据表','Replay Bus 状态','Replay Event 时间线','数据质量报告','安全边界说明','下一阶段真实 xtdata 接入边界说明'],'sandbox':True,'mock_data':provider=='mock_provider','recorded_data':provider=='recorded_provider','read_only':True,'not_live_trading':True,'no_qmt_trader_api':True,'no_order_submitted':True}
    boundary={'stage':'Stage85','goal':'真实 xtdata interface adapter dry-run；默认 disabled；不连接真实行情；不调用 xttrader；不下单','sandbox':True,'not_live_trading':True,'no_qmt_trader_api':True}
    report={'stage':'Stage84','created_at':STABLE_TS,'summary':'Sandbox Market Data Gateway 与 Replay Bus 已生成；仅只读回放，不连接真实行情，不下单。','output_dir':output_dir,'report_path':f'{output_dir}/market_gateway_report.md','provider':provider,'symbol_count':len(syms),'replay_event_count':len(events),'quality':quality,'safety':safety_report({'provider':provider}),'sandbox':True,'mock_data':provider=='mock_provider','read_only':True,'not_live_trading':True,'no_qmt_trader_api':True,'no_order_submitted':True,'warnings':quality.get('warnings',[])}
    files={'market_input_context':ctx,'market_symbols':{'symbols':syms,'sandbox':True,'read_only':True,'not_live_trading':True,'no_qmt_trader_api':True},'market_snapshots':{'snapshots':snaps},'market_bars':{'bars':bars},'replay_events':{'events':events},'replay_session':session,'market_data_quality':quality,'market_gateway_report':report,'frontend_market_contract':contract,'next_qmt_xtdata_boundary_plan':boundary}
    for name,data in files.items(): write_json_if_changed(out/f'{name}.json',data); write_text_if_changed(out/f'{name}.md',md(name,data))
    return report
