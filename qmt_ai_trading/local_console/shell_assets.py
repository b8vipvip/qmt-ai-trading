from __future__ import annotations
from .shell_models import *
SAFETY_BANNER='本地只读控制台｜不是实盘授权｜不下单｜不调用 xttrader｜不查询真实账户｜不发送真实通知'
def build_index_html():
    sections=['Dashboard Overview Section','Stage Status Cards Section','Latest Validation Card Section','Warning / Blocking Stats Section','Manifest / Hash Section','Scheduler Preview Section','Safety Boundary Section','API Capability Section','Detail / Filter Section','Report List Section']
    body='\n'.join(f'<section id="{s.lower().replace(" / ","-").replace(" ","-")}"><h2>{s}</h2><div class="card" data-placeholder="readonly">Stage66 static data binding placeholder</div></section>' for s in sections)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>QMT AI Trading Local Console Shell</title><link rel="stylesheet" href="./style.css"></head><body><header><h1>QMT AI Trading 本地只读控制台</h1><p>{SAFETY_BANNER}</p></header><aside class="safety-banner" id="safety-banner">Safety Banner：{SAFETY_BANNER}</aside><nav><a href="#/dashboard">Dashboard</a><a href="#/reports">Reports</a><a href="#/reports/detail">Detail</a><a href="#/filters">Filters</a><a href="#/manifest">Manifest</a><a href="#/validation">Validation</a><a href="#/scheduler">Scheduler</a><a href="#/safety">Safety</a><a href="#/api">API</a><a href="#/next">Stage66</a></nav><main>{body}</main><footer>READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW 不是实盘授权；本页面不提供下单按钮、审批按钮、账户查询入口或真实通知入口。</footer><script src="./app.js"></script></body></html>'''
def build_app_js():
    return """const READ_ONLY = true;
const SAFE_SOURCES = ['./shell_manifest.json', './route_map.json', './data_binding_placeholders.json'];
async function loadStaticShellData() {
  const results = {};
  for (const source of SAFE_SOURCES) {
    try { results[source] = await fetch(source).then((response) => response.json()); }
    catch (error) { results[source] = { warning: String(error), read_only: READ_ONLY }; }
  }
  document.body.dataset.readOnly = String(READ_ONLY);
  return results;
}
window.addEventListener('DOMContentLoaded', () => { loadStaticShellData(); });
"""
def build_style_css():
    return """body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f6f7fb;color:#182033}header,.safety-banner,nav,main,footer{padding:16px 24px}.safety-banner{background:#fff3cd;border:1px solid #ffe08a;color:#664d03;font-weight:700}nav{display:flex;gap:12px;flex-wrap:wrap;background:#102033}nav a{color:#fff;text-decoration:none}.card,section{background:#fff;border:1px solid #d9e1ef;border-radius:12px;margin:14px 0;padding:16px;box-shadow:0 1px 3px #0001}h1,h2{margin:0 0 8px}footer{font-size:13px;color:#4b5563}
"""
def build_shell_route_map():
    return [LocalConsoleShellRoute('/','Home'),LocalConsoleShellRoute('#/dashboard','Dashboard Overview'),LocalConsoleShellRoute('#/reports','Report List'),LocalConsoleShellRoute('#/reports/detail','Report Detail'),LocalConsoleShellRoute('#/filters','Filters'),LocalConsoleShellRoute('#/manifest','Manifest'),LocalConsoleShellRoute('#/validation','Validation'),LocalConsoleShellRoute('#/scheduler','Scheduler Preview'),LocalConsoleShellRoute('#/safety','Safety Boundary'),LocalConsoleShellRoute('#/api','API Capability'),LocalConsoleShellRoute('#/next','Stage66 Plan')]
def build_data_binding_placeholders():
    return [LocalConsoleDataBindingPlaceholder('dashboard_cards','local_console_dashboard_stage64/dashboard_card_index.json','#dashboard-overview-section','Stage66 binds dashboard card JSON'),LocalConsoleDataBindingPlaceholder('report_list','local_console_stage62/report_list.json','#report-list-section','Stage66 binds report list'),LocalConsoleDataBindingPlaceholder('detail_filters','local_console_detail_stage63/filter_index.json','#detail-filter-section','Stage66 binds filters'),LocalConsoleDataBindingPlaceholder('api_capability','api_gateway_stage61/api_gateway_report.json','#api-capability-section','Stage66 binds API capability')]
def build_static_safety_boundary(): return LocalConsoleStaticSafetyReport()
def build_shell_manifest(assets=None): return LocalConsoleShellManifest(assets=assets or [])
