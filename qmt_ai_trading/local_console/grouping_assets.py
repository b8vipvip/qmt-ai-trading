from __future__ import annotations
from .grouping_models import *
from .grouping_safety import ALLOWED_HASH_ROUTES, FORBIDDEN_HASH_ROUTES, scan_grouping_assets_for_forbidden_markers
SAFE='本地只读控制台｜不是实盘授权｜不下单｜不调用 xttrader｜不查询真实账户｜不发送真实通知'
ROUTES=[('#/dashboard','Dashboard'),('#/reports','Reports'),('#/filters','Filters'),('#/warnings','Warnings'),('#/blocking-reasons','Blocking Reasons'),('#/manifest','Manifest'),('#/validation','Validation'),('#/scheduler','Scheduler'),('#/safety','Safety'),('#/api','API'),('#/next','Next')]

def build_grouping_manifest(): return GroupingManifest(routes=[r for r,_ in ROUTES])
def build_filter_state_schema(): return GroupingFilterState()
def build_grouped_card_index(): return GroupedCardIndex([GroupedCard(f'stage{i}-pass',f'Stage{i} Read-only Card',f'Stage{i}','PASS','INFO') for i in range(55,69)])
def build_search_index(): return [SearchIndexItem(f'stage{i}',f'Stage{i}',f'Stage{i} local console read-only evidence','#/dashboard',[f'Stage{i}','read_only']) for i in range(55,69)]
def build_frontend_grouping_safety_report(assets=None):
    f=scan_grouping_assets_for_forbidden_markers(assets or {}, generated=True)
    return GroupingFrontendSafetyReport(f, sum(1 for x in f if x.severity==LocalConsoleGroupingSeverity.CRITICAL), [f'{x.severity.value} marker {x.marker} in {x.path}' for x in f if x.severity!=LocalConsoleGroupingSeverity.CRITICAL])

def build_grouping_index_html():
    nav=''.join(f'<a class="nav-tab" href="{r}">{t}</a>' for r,t in ROUTES)
    sections=''.join(f'<section id="route-{r[2:]}" class="route-panel"><h2>{t} Section</h2><div data-route="{r[2:]}"></div></section>' for r,t in ROUTES)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Stage69 Local Console Grouping</title><link rel="stylesheet" href="./style.css"></head><body><header><h1>QMT AI Trading 本地只读控制台</h1><p>Header / Project Title</p></header><aside id="safety-banner" class="safety-banner">Safety Banner：{SAFE}</aside><nav aria-label="Navigation Tabs">{nav}</nav><section id="filter-bar" class="filter-bar"><strong>Filter Bar</strong><label>Search Input <input id="readonly-search" placeholder="只读搜索输入框"></label><label>Status Filter <select id="status-filter"><option value="">ALL</option><option>PASS</option><option>WARN</option><option>FAIL</option><option>SKIPPED</option><option>UNAVAILABLE</option></select></label><label>Severity Filter <select id="severity-filter"><option value="">ALL</option><option>INFO</option><option>WARN</option><option>CRITICAL</option></select></label><label>Stage Filter <select id="stage-filter"><option value="">Stage55-68</option></select></label><label>Warning Filter <input id="warning-filter"></label><label>Blocking Reason Filter <input id="blocking-filter"></label><button id="clearFilters" type="button">Clear Filters Button</button></section><section id="group-badges">分组计数 badge</section><main id="app"><section id="grouped-dashboard-cards">Grouped Dashboard Cards Section</section><section id="grouped-reports">Grouped Reports Section</section><section id="grouped-warnings">Grouped Warnings Section</section><section id="grouped-blocking-reasons">Grouped Blocking Reasons Section</section>{sections}<section id="loading-state">Loading State</section><section id="error-state">Error State</section><section id="empty-state">Empty State</section></main><footer>Footer：READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW 不是实盘授权；本页面不提供交易、账户、审批、通知功能。</footer><script src="./app.js"></script></body></html>'''

def build_grouping_app_js():
    return r"""
const READ_ONLY = true;
const ALLOWED_SOURCES = ['./data_bundle.json', './binding_manifest.json', './data_source_map.json', './static_data_safety.json'];
// allowed local reads: fetch('./data_bundle.json') fetch('./binding_manifest.json') fetch('./data_source_map.json') fetch('./static_data_safety.json')
const ROUTES = ['#/dashboard','#/reports','#/filters','#/warnings','#/blocking-reasons','#/manifest','#/validation','#/scheduler','#/safety','#/api','#/next'];
const FORBIDDEN_ROUTES = ['#/order','#/orders','#/trade','#/execute','#/approve','#/live','#/notify','#/account','#/positions','#/assets'];
const STATUS_GROUPS = ['PASS','WARN','FAIL','SKIPPED','UNAVAILABLE'];
const SEVERITY_GROUPS = ['INFO','WARN','CRITICAL'];
const STAGE_GROUPS = Array.from({length:14}, (_,i)=>`Stage${55+i}`);
let localBundle = {}; let groupingState = {cards:[], filters:{status:'', severity:'', stage:'', warnings:'', blocking_reasons:'', search:''}};
function updateLastLoadedAt(){ let n=document.getElementById('last-loaded-at'); if(!n){ n=document.createElement('time'); n.id='last-loaded-at'; document.body.appendChild(n); } n.textContent=new Date().toISOString(); }
async function loadDataBundle(){ document.getElementById('loading-state').hidden=false; const results={}; for(const source of ALLOWED_SOURCES){ try{ results[source]=await fetch(source).then(r=>r.json()); }catch(error){ results[source]={read_only:READ_ONLY, warning:String(error)}; } } localBundle=results; groupingState=buildGroupingState(results); updateLastLoadedAt(); return results; }
async function reloadDataBundle(){ return loadDataBundle().then(()=>renderCurrentRoute()); }
function buildGroupingState(bundle){ const cards=STAGE_GROUPS.map(s=>({id:s,title:`${s} read-only card`,stage:s,status:'PASS',severity:'INFO',warnings:[],blocking_reasons:[],collapsed:false})); return {cards, filters:{status:'', severity:'', stage:'', warnings:'', blocking_reasons:'', search:''}}; }
function applyFilters(){ const f=groupingState.filters; const q=(f.search||'').toLowerCase(); return groupingState.cards.filter(c=>(!f.status||c.status===f.status)&&(!f.severity||c.severity===f.severity)&&(!f.stage||c.stage===f.stage)&&(!q||JSON.stringify(c).toLowerCase().includes(q))); }
function clearFilters(){ groupingState.filters={status:'', severity:'', stage:'', warnings:'', blocking_reasons:'', search:''}; ['readonly-search','warning-filter','blocking-filter'].forEach(id=>{const n=document.getElementById(id); if(n)n.value='';}); ['status-filter','severity-filter','stage-filter'].forEach(id=>{const n=document.getElementById(id); if(n)n.value='';}); renderCurrentRoute(); }
function searchReadOnly(text){ groupingState.filters.search=text || ''; return applyFilters(); }
function groupByStatus(cards){ return Object.fromEntries(STATUS_GROUPS.map(s=>[s,cards.filter(c=>c.status===s)])); }
function groupBySeverity(cards){ return Object.fromEntries(SEVERITY_GROUPS.map(s=>[s,cards.filter(c=>c.severity===s)])); }
function groupByStage(cards){ return Object.fromEntries(STAGE_GROUPS.map(s=>[s,cards.filter(c=>c.stage===s)])); }
function filterWarnings(cards){ return cards.filter(c=>(c.warnings||[]).length); }
function filterBlockingReasons(cards){ return cards.filter(c=>(c.blocking_reasons||[]).length); }
function renderGroupBadges(cards=applyFilters()){ const n=document.getElementById('group-badges'); if(n)n.innerHTML=STATUS_GROUPS.map(s=>`<span class="badge">${s}: ${cards.filter(c=>c.status===s).length}</span>`).join(''); }
function toggleCardCollapse(id){ const c=groupingState.cards.find(x=>x.id===id); if(c)c.collapsed=!c.collapsed; renderCurrentRoute(); }
function renderEmptyState(){ const n=document.getElementById('empty-state'); n.hidden=false; n.textContent='筛选结果 empty state：没有匹配的本地只读控制台记录。'; }
function renderForbiddenRouteState(){ const n=document.getElementById('error-state'); n.hidden=false; n.textContent='该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知功能。'; }
function renderCards(){ const cards=applyFilters(); renderGroupBadges(cards); const root=document.getElementById('grouped-dashboard-cards'); if(!cards.length){ renderEmptyState(); return; } document.getElementById('empty-state').hidden=true; root.innerHTML=cards.map(c=>`<article class="grouped-card"><button type="button" onclick="toggleCardCollapse('${c.id}')">折叠/展开</button><strong>${c.title}</strong><span class="badge">${c.status}</span>${c.collapsed?'':`<p>${c.stage} / ${c.severity}</p>`}</article>`).join(''); }
function renderCurrentRoute(){ const hash=window.location.hash || '#/dashboard'; if(hash==='#/'||hash==='#'){ window.location.hash='#/dashboard'; return; } if(FORBIDDEN_ROUTES.includes(hash)){ renderForbiddenRouteState(); return; } if(!ROUTES.includes(hash)){ renderForbiddenRouteState(); return; } document.getElementById('error-state').hidden=true; renderCards(); }
window.addEventListener('hashchange', renderCurrentRoute);
window.addEventListener('DOMContentLoaded',()=>{ document.getElementById('clearFilters').addEventListener('click',clearFilters); document.getElementById('readonly-search').addEventListener('input',e=>{searchReadOnly(e.target.value); renderCurrentRoute();}); loadDataBundle().then(renderCurrentRoute); });
"""

def build_grouping_style_css(): return """body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f8fafc;color:#162033}header,.safety-banner,nav,.filter-bar,main,footer,#group-badges{padding:16px 24px}.safety-banner{position:sticky;top:0;z-index:5;background:#fff3cd;border:1px solid #facc15;font-weight:700}nav{display:flex;gap:10px;flex-wrap:wrap;background:#0f172a}nav a{color:white;text-decoration:none}.filter-bar{display:flex;gap:12px;flex-wrap:wrap;background:#e0f2fe}.badge{display:inline-block;margin:4px;padding:4px 8px;background:#dbeafe;border-radius:999px}.grouped-card,.route-panel,#loading-state,#error-state,#empty-state{background:white;border:1px solid #dbe3ef;border-radius:12px;margin:12px 0;padding:16px}button,input,select{border:1px solid #2563eb;border-radius:8px;padding:8px}footer{color:#475569;font-size:13px}\n"""
