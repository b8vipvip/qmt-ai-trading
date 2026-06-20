from __future__ import annotations
from .refresh_models import *
from .refresh_safety import FORBIDDEN_HASH_ROUTES, scan_refresh_assets_for_forbidden_markers
SAFE='本地只读控制台｜不是实盘授权｜不下单｜不调用 xttrader｜不查询真实账户｜不发送真实通知'
ROUTES=[('#/dashboard','Dashboard'),('#/reports','Reports'),('#/filters','Filters'),('#/manifest','Manifest'),('#/validation','Validation'),('#/scheduler','Scheduler'),('#/safety','Safety'),('#/api','API'),('#/next','Next')]

def build_navigation_route_map(): return [NavigationRoute(r,t,True,LocalConsoleRefreshSeverity.INFO,'read-only hash route') for r,t in ROUTES]
def build_refresh_manifest(): return RefreshManifest()
def build_ui_state_placeholders(): return [UiStatePlaceholder('loading','#loading-state','Loading State'),UiStatePlaceholder('error','#error-state','Error State'),UiStatePlaceholder('empty','#empty-state','Empty State')]
def build_frontend_safety_report(assets=None):
    f=scan_refresh_assets_for_forbidden_markers(assets or {}, generated=True)
    return FrontEndSafetyReport(f, sum(1 for x in f if x.severity==LocalConsoleRefreshSeverity.CRITICAL), [f'{x.severity.value} marker {x.marker} in {x.path}' for x in f if x.severity!=LocalConsoleRefreshSeverity.CRITICAL])
def build_refresh_index_html():
    nav=''.join(f'<a class="nav-tab" href="{r}">{t}</a>' for r,t in ROUTES)
    secs=[('dashboard','Dashboard Overview Section'),('reports','Reports Section'),('filters','Filters Section'),('manifest','Manifest Section'),('validation','Validation Section'),('scheduler','Scheduler Section'),('safety','Safety Section'),('api','API Section'),('next','Next Stage Section')]
    body=''.join(f'<section id="route-{i}" class="route-panel"><h2>{t}</h2><div data-route="{i}"></div></section>' for i,t in secs)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>QMT AI Trading Stage68 Local Console Refresh</title><link rel="stylesheet" href="./style.css"></head><body><header><h1>QMT AI Trading 本地只读控制台</h1><p>Header / Project Title</p></header><aside id="safety-banner" class="safety-banner">Safety Banner：{SAFE}</aside><nav aria-label="Navigation Tabs">{nav}</nav><section class="toolbar"><button id="readonlyRefresh" type="button">只读刷新本地 data bundle</button><span>Latest updated: <time id="last-loaded-at">UNAVAILABLE</time></span></section><main id="app">{body}<section id="loading-state">Loading State</section><section id="error-state">Error State</section><section id="empty-state">Empty State</section></main><footer>Footer：READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW 不是实盘授权；本页面不提供交易、账户、审批、通知功能。</footer><script src="./app.js"></script></body></html>'''
def build_refresh_app_js():
    return r"""
const READ_ONLY = true;
const ALLOWED_SOURCES = ['./data_bundle.json', './binding_manifest.json', './data_source_map.json', './static_data_safety.json'];
// allowed local reads: fetch('./data_bundle.json') fetch('./binding_manifest.json') fetch('./data_source_map.json') fetch('./static_data_safety.json')
const ROUTES = ['#/dashboard','#/reports','#/filters','#/manifest','#/validation','#/scheduler','#/safety','#/api','#/next'];
const FORBIDDEN_ROUTES = ['#/order','#/orders','#/trade','#/execute','#/approve','#/live','#/notify','#/account','#/positions','#/assets'];
let localBundle = {};
function updateLastLoadedAt(){ const node=document.getElementById('last-loaded-at'); if(node) node.textContent=new Date().toISOString(); }
function showLoading(){ document.getElementById('loading-state').hidden=false; document.getElementById('error-state').hidden=true; document.getElementById('empty-state').hidden=true; }
function showError(message){ document.getElementById('loading-state').hidden=true; const n=document.getElementById('error-state'); n.hidden=false; n.textContent=message || '该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知功能。'; }
function showEmpty(message){ document.getElementById('loading-state').hidden=true; const n=document.getElementById('empty-state'); n.hidden=false; n.textContent=message || 'Empty State：本地只读数据暂不可用。'; }
function renderSafetyBanner(){ document.getElementById('safety-banner').textContent='Safety Banner：本地只读控制台｜不是实盘授权｜不下单｜不调用 xttrader｜不查询真实账户｜不发送真实通知'; }
async function loadDataBundle(){ showLoading(); const results={}; for (const source of ALLOWED_SOURCES){ try{ results[source]=await fetch(source).then(r=>r.json()); } catch(error){ results[source]={read_only:READ_ONLY, warning:String(error)}; } } localBundle=results; updateLastLoadedAt(); return results; }
async function reloadDataBundle(){ return loadDataBundle().then(()=>renderCurrentRoute()); }
function renderValue(v){ if(!v){ showEmpty(); } return `<pre>${JSON.stringify(v || {read_only:READ_ONLY, placeholder:'empty'}, null, 2)}</pre>`; }
function panel(name){ return document.querySelector(`[data-route="${name}"]`); }
function renderDashboard(){ panel('dashboard').innerHTML=renderValue(localBundle['./data_bundle.json']?.dashboard || localBundle); }
function renderReports(){ panel('reports').innerHTML=renderValue(localBundle['./data_bundle.json']?.report_list); }
function renderFilters(){ panel('filters').innerHTML=renderValue(localBundle['./data_bundle.json']?.detail_filters); }
function renderManifest(){ panel('manifest').innerHTML=renderValue(localBundle['./binding_manifest.json']); }
function renderValidation(){ panel('validation').innerHTML=renderValue(localBundle['./data_bundle.json']?.latest_validation); }
function renderScheduler(){ panel('scheduler').innerHTML=renderValue(localBundle['./data_bundle.json']?.scheduler_preview); }
function renderSafety(){ panel('safety').innerHTML=renderValue(localBundle['./static_data_safety.json']); }
function renderApi(){ panel('api').innerHTML=renderValue(localBundle['./data_bundle.json']?.api_capability); }
function renderNext(){ panel('next').innerHTML=renderValue({stage:'Stage69', plan:'本地控制台状态分组与筛选体验层', read_only:READ_ONLY}); }
function renderCurrentRoute(){ renderSafetyBanner(); const hash=window.location.hash || '#/dashboard'; if(hash==='#/' || hash==='#'){ window.location.hash='#/dashboard'; return; } document.querySelectorAll('.route-panel').forEach(x=>x.hidden=true); if(FORBIDDEN_ROUTES.includes(hash)){ showError('该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知功能。'); return; } if(!ROUTES.includes(hash)){ showError('Unknown read-only route.'); return; } document.getElementById('error-state').hidden=true; const name=hash.slice(2); document.getElementById(`route-${name}`).hidden=false; ({dashboard:renderDashboard,reports:renderReports,filters:renderFilters,manifest:renderManifest,validation:renderValidation,scheduler:renderScheduler,safety:renderSafety,api:renderApi,next:renderNext}[name])(); }
window.addEventListener('hashchange', renderCurrentRoute);
window.addEventListener('DOMContentLoaded', () => { document.getElementById('readonlyRefresh').addEventListener('click', reloadDataBundle); loadDataBundle().then(renderCurrentRoute); });
"""
def build_refresh_style_css(): return """body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f8fafc;color:#162033}header,.safety-banner,nav,.toolbar,main,footer{padding:16px 24px}.safety-banner{position:sticky;top:0;z-index:5;background:#fff3cd;border:1px solid #facc15;font-weight:700}nav{display:flex;gap:10px;flex-wrap:wrap;background:#0f172a}nav a{color:white;text-decoration:none}.toolbar{display:flex;gap:16px;align-items:center}button{border:1px solid #2563eb;background:#dbeafe;border-radius:8px;padding:8px 12px}.route-panel,#loading-state,#error-state,#empty-state{background:white;border:1px solid #dbe3ef;border-radius:12px;margin:12px 0;padding:16px}pre{white-space:pre-wrap;overflow:auto}footer{color:#475569;font-size:13px}\n"""
