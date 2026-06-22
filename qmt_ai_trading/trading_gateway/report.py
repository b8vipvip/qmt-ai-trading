from __future__ import annotations
import json, shutil
from pathlib import Path
from typing import Any
from .xttrader_config import default_xttrader_boundary_config
from .xttrader_boundary import XtTraderBoundaryAdapter, disabled_payload
from .import_guard import scan_imports
from .capability_probe import run_capability_probe
from .account_query_gate import account_query_gate
from .order_submit_gate import order_submit_gate
from .safety import validate_config

REQUIRED_INPUTS = [
"local_console_paper_stage89/paper_trading_report.json","local_console_paper_stage89/paper_orders.json","local_console_paper_stage89/paper_fills.json","local_console_paper_stage89/shadow_positions.json","local_console_paper_stage89/shadow_portfolio.json","local_console_paper_stage89/shadow_pnl.json","local_console_paper_stage89/risk_replay.json","local_console_paper_stage89/frontend_paper_contract.json","local_console_strategy_stage88/trade_intents.json","local_console_risk_stage88/risk_decisions.json","local_console_datahub_stage88/datahub_status.json"]
SAFE_FLAGS = {"fallback_used": True, "mock_data": True, "trading_boundary_only": True, "xttrader_enabled": False, "xttrader_imported": False, "account_query_enabled": False, "order_submit_enabled": False, "real_order_submitted": False, "dry_run": True, "read_only": True, "requires_human_approval": True}

def _read(path: Path, default: Any):
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception: return default

def _dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)

def _write_pair(base: Path, stem: str, obj: Any):
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{stem}.json").write_text(_dump(obj) + "\n", encoding="utf-8")
    (base / f"{stem}.md").write_text(f"# {stem}\n\n```json\n{_dump(obj)}\n```\n", encoding="utf-8")

def _risk_map(risk: dict) -> dict[str, dict]:
    rows = risk.get("decisions", risk.get("results", [])) if isinstance(risk, dict) else []
    return {str(r.get("intent_id") or r.get("order_id") or r.get("source_paper_order_id")): r for r in rows if isinstance(r, dict)}

def _build_frontend_app(repo_root: Path):
    app = repo_root / "local_console_app_stage90"; app.mkdir(parents=True, exist_ok=True)
    html = """<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>xttrader 边界</title><style>body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:24px;background:#f7f8fb;color:#172033}.card{background:white;border-radius:12px;padding:16px;margin:12px 0;box-shadow:0 1px 6px #d7dce5}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.badge{display:inline-block;padding:6px 10px;border-radius:999px;background:#fee2e2;color:#991b1b;font-weight:700}table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left}code,pre{white-space:pre-wrap;background:#0f172a;color:#e5e7eb;padding:12px;border-radius:8px}</style></head><body><h1>xttrader 边界 / 交易接口边界</h1><div class='grid'><div class='card'><b>xttrader：未接入</b></div><div class='card'><b>账户查询：关闭</b></div><div class='card'><b>真实下单：关闭</b></div><div class='card'><b>撤单能力：关闭</b></div><div class='card'><b>人工确认：必须</b></div><div class='card'><b>Risk Gate：必须</b><br><b>Kill Switch：必须</b></div></div><p><span class='badge'>DISABLED_FOR_SAFETY</span></p><nav>查看订单预览 · 查看安全边界 · 查看下一阶段计划</nav><section class='card'><h2>xttrader 配置状态</h2><div id='config'></div></section><section class='card'><h2>Import Guard</h2><div id='guard'></div></section><section class='card'><h2>账户查询闸门</h2><div id='account'></div></section><section class='card'><h2>下单闸门</h2><div id='submit'></div></section><section class='card'><h2>订单预览</h2><table><thead><tr><th>标的</th><th>方向</th><th>数量</th><th>参考价</th><th>预估金额</th><th>来源 Paper Order</th><th>风控结果</th><th>预览状态</th><th>阻断原因</th></tr></thead><tbody id='orders'></tbody></table></section><section class='card'><h2>安全扫描</h2><div id='safety'></div></section><section class='card'><h2>下一阶段计划</h2><div id='plan'></div></section><details class='card'><summary>原始 JSON 折叠区</summary><pre id='raw'></pre></details><script>async function j(u){return (await fetch(u)).json()} function show(id,o){document.getElementById(id).innerHTML='<pre>'+JSON.stringify(o,null,2)+'</pre>'} Promise.all([j('/api/v1/trading/xttrader-boundary/config'),j('/api/v1/trading/xttrader-boundary/import-guard'),j('/api/v1/trading/xttrader-boundary/account-query-gate'),j('/api/v1/trading/xttrader-boundary/order-submit-gate'),j('/api/v1/trading/xttrader-boundary/order-previews'),j('/api/v1/trading/xttrader-boundary/safety')]).then(([c,g,a,s,o,sa])=>{show('config',c);show('guard',g);show('account',a);show('submit',s);show('safety',sa);document.getElementById('orders').innerHTML=(o.order_previews||o.previews||[]).map(x=>`<tr><td>${x.symbol}</td><td>${x.side}</td><td>${x.quantity}</td><td>${x.reference_price}</td><td>${x.estimated_amount}</td><td>${x.source_paper_order_id}</td><td>${x.risk_decision}</td><td>${x.preview_status}</td><td>${x.block_reason}</td></tr>`).join('');document.getElementById('raw').textContent=JSON.stringify({c,g,a,s,o,sa},null,2)});j('/api/v1/trading/xttrader-boundary/report').then(r=>show('plan',r.report&&r.report.next_stage_plan||r))</script></body></html>"""
    (app / "index.html").write_text(html, encoding="utf-8")

def run_xttrader_boundary_stage90(repo_root=".", input_stage=89, output_dir="local_console_xttrader_stage90", dry_run=True, read_only=True):
    root=Path(repo_root); out=root/output_dir; canon=root/"artifacts/reports/stage90/xttrader_boundary"
    files={p:_read(root/p, None) for p in REQUIRED_INPUTS}
    fallback=any(v is None for v in files.values())
    context={"stage":"Stage90","input_stage":input_stage,"input_files":{k:{"exists":v is not None} for k,v in files.items()}, **({} if not fallback else SAFE_FLAGS), "dry_run":True,"read_only":True,"trading_boundary_only":True,"xttrader_enabled":False,"xttrader_imported":False,"account_query_enabled":False,"order_submit_enabled":False,"real_order_submitted":False,"requires_human_approval":True}
    cfg=default_xttrader_boundary_config(); adapter=XtTraderBoundaryAdapter(cfg)
    orders=(files.get("local_console_paper_stage89/paper_orders.json") or {}).get("orders", []) or []
    risks=_risk_map(files.get("local_console_risk_stage88/risk_decisions.json") or {})
    previews=[adapter.build_order_preview(o, risks.get(str(o.get("intent_id"))) or risks.get(str(o.get("order_id"))) or {}) for o in orders]
    config=cfg.to_dict(); import_guard=scan_imports(repo_root=str(root)); cap=run_capability_probe(cfg); account=account_query_gate(); submit=order_submit_gate(); safety={**validate_config(cfg), "import_guard_status":import_guard["status"], "forbidden_runtime_actions":["account_query","position_query","order_query","trade_query","order_submit","order_cancel"], "no_account_query":True,"no_order_submitted":True,"no_xttrader":True}
    frontend={"menu":["xttrader 边界","交易接口边界"],"endpoints":["/api/v1/trading/xttrader-boundary/config","/api/v1/trading/xttrader-boundary/order-previews"],"forbidden_actions_absent":True,**disabled_payload()}
    plan={"stage":"Stage91","title":"账户/持仓只读查询边界，默认 disabled，人工确认后只读查询","order_submit_enabled":False,"requires_human_approval":True,"rate_limit_required":True,"mask_account_required":True,"auto_trading_allowed":False,**disabled_payload()}
    report={"stage":"Stage90","status":"SUCCESS","output_dir":str(out),"canonical_dir":str(canon),"order_preview_count":len(previews),"safety_report_status":safety["status"],"workflow_status":{"xttrader Boundary":"DISABLED_FOR_SAFETY","Account Query":"DISABLED_FOR_SAFETY","Order Submit":"DISABLED_FOR_SAFETY","Live Trading":"DISABLED_FOR_SAFETY"},"next_stage_plan":plan,**disabled_payload()}
    docs={"xttrader_input_context":context,"xttrader_boundary_config":config,"xttrader_import_guard_report":import_guard,"xttrader_capability_probe":cap,"xttrader_account_query_gate":account,"xttrader_order_submit_gate":submit,"order_previews":{"order_previews":previews,**disabled_payload()},"xttrader_safety_report":safety,"xttrader_boundary_report":report,"frontend_xttrader_contract":frontend,"next_account_readonly_plan":plan}
    for base in (out, canon):
        for stem,obj in docs.items(): _write_pair(base, stem, obj)
    _build_frontend_app(root)
    return report
