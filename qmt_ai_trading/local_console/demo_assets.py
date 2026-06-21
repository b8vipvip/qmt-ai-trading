from __future__ import annotations
from .demo_models import *
SAFETY_BANNER='本地只读控制台；不是实盘授权；不下单；不调用 xttrader；不查询真实账户；不发送真实通知；本地演示包只是静态演示材料，不是审批授权。'
ALLOWED_ROUTES=['#/demo','#/demo/guide','#/demo/routes','#/demo/assets','#/demo/package','#/demo/safety','#/demo/validation','#/help','#/help/pages','#/help/features','#/help/safety','#/help/faq','#/help/errors','#/help/glossary','#/help/routes','#/help/package','#/ui-acceptance','#/dashboard','#/next']
FORBIDDEN_ROUTES=['#/order','#/orders','#/trade','#/execute','#/approve','#/approval','#/auto-approve','#/live','#/notify','#/account','#/positions','#/assets']
PACKAGE_FILES=['index.html','app.js','style.css','demo_manifest.md','demo_manifest.json','demo_guide.md','demo_guide.json','demo_route_map.md','demo_route_map.json','demo_asset_manifest.md','demo_asset_manifest.json','demo_package_index.md','demo_package_index.json','demo_safety_report.md','demo_safety_report.json','demo_validation_summary.md','demo_validation_summary.json','local_console_demo_package_report.md','local_console_demo_package_report.json','next_ui_productization_closure_plan.md','next_ui_productization_closure_plan.json']

def build_demo_home(): return [DemoHomeItem('stage74-overview','Stage74 本地演示打包层','汇总本地演示包目录、静态资源清单、演示入口页、演示说明、只读 manifest、route map、asset manifest、package index、安全报告、验收摘要与 Stage75 计划。'),DemoHomeItem('readonly-boundary','只读边界',SAFETY_BANNER)]
def build_demo_manifest(): return DemoManifest(files=PACKAGE_FILES)
def build_demo_guide(): return [DemoGuideItem('如何打开演示','打开本地 index.html；只读取同目录 JSON；不是审批授权，不是实盘授权。'),DemoGuideItem('安全说明','不下单，不调用 xttrader，不查询真实账户，不发送真实通知，不自动 approve。')]
def build_demo_route_map(): return [DemoRouteMapItem(r,r.replace('#/','').replace('/','-')+'-panel',True,'只读演示/帮助路由。') for r in ALLOWED_ROUTES]+[DemoRouteMapItem(r,'forbidden-route-panel',False,'该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。') for r in FORBIDDEN_ROUTES]
def build_demo_asset_manifest(): return [DemoStaticAssetItem('index.html','html','演示入口页',True,'包含 Header / Project Title、Safety Banner、各演示面板、Loading/Error/Empty/Footer。'),DemoStaticAssetItem('app.js','javascript','只读前端逻辑',True,'只 fetch 本地相对 JSON 文件，不调用交易/账户/审批/通知 API。'),DemoStaticAssetItem('style.css','css','演示样式',True,'静态样式，无外部依赖。')]+[DemoStaticAssetItem(f,'markdown/json' if f.endswith(('.md','.json')) else 'asset',f,True,'本地只读演示材料。') for f in PACKAGE_FILES if f not in {'index.html','app.js','style.css'}]
def build_demo_package_index(): return [DemoPackageIndexItem(f,f,True,'只列本地演示材料，不触发任务，不包含敏感文件、运行日志、真实行情数据或账户数据。') for f in PACKAGE_FILES]
def build_demo_safety_report(findings=None):
    findings=findings or []
    return DemoSafetyReport(findings,sum(1 for f in findings if f.severity==LocalConsoleDemoSeverity.CRITICAL),[f'{f.severity.value} {f.marker} {f.path}' for f in findings if f.severity!=LocalConsoleDemoSeverity.CRITICAL])
def build_demo_validation_summary(critical_count=0): return DemoValidationSummary(LocalConsoleDemoStatus.PASS if critical_count==0 else LocalConsoleDemoStatus.FAIL,'本地演示包只读验证通过。' if critical_count==0 else '发现 CRITICAL 安全问题。',critical_count)
def build_next_ui_productization_closure_plan(): return NextUiProductizationClosurePlanReport()

def build_demo_index_html():
    nav=''.join(f'<a href="{r}">{r}</a>' for r in ALLOWED_ROUTES)
    panels=''.join([f'<section id="{pid}"><h2>{title}</h2></section>' for pid,title in [('demo-home-panel','Demo Home Panel'),('demo-guide-panel','Demo Guide Panel'),('demo-route-map-panel','Demo Route Map Panel'),('demo-asset-manifest-panel','Demo Asset Manifest Panel'),('demo-package-index-panel','Demo Package Index Panel'),('demo-safety-report-panel','Demo Safety Report Panel'),('demo-validation-summary-panel','Demo Validation Summary Panel'),('stage73-help-evidence-panel','Stage73 Help Evidence Panel')]])
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Stage74 Local Demo Package Layer</title><link rel="stylesheet" href="./style.css"></head><body><header><h1>QMT AI Trading 本地只读控制台</h1><p>Header / Project Title - Stage74 本地演示打包层</p></header><aside class="safety-banner">Safety Banner：{SAFETY_BANNER}</aside><nav aria-label="Navigation Tabs">{nav}</nav><main id="app"><div class="toolbar"><input id="demoSearchInput" placeholder="只读搜索演示材料"><button id="searchDemoButton" type="button">Search Demo</button><button id="copyDemoSectionButton" type="button">Copy Demo Section</button><button id="openDemoPackageButton" type="button">Open Demo Package</button><button id="toggleDemoItemButton" type="button">Toggle Demo Item</button></div>{panels}<section id="loading-state">Loading State</section><section id="error-state">Error State</section><section id="empty-state">Empty State</section></main><footer>Footer：READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW 只表示本地演示打包层材料可供人工复核，不是实盘授权。</footer><script src="./app.js"></script></body></html>'''

def build_demo_app_js():
    return f'''const ALLOWED_ROUTES={ALLOWED_ROUTES!r};
const FORBIDDEN_ROUTES={FORBIDDEN_ROUTES!r};
const state={{}};
async function loadDemoManifest(){{ const r=await fetch('./demo_manifest.json'); state.manifest=await r.json(); return state.manifest; }}
async function loadDemoGuide(){{ const r=await fetch('./demo_guide.json'); state.guide=await r.json(); return state.guide; }}
async function loadDemoRouteMap(){{ const r=await fetch('./demo_route_map.json'); state.routes=await r.json(); return state.routes; }}
async function loadDemoAssetManifest(){{ const r=await fetch('./demo_asset_manifest.json'); state.assets=await r.json(); return state.assets; }}
async function loadDemoPackageIndex(){{ const r=await fetch('./demo_package_index.json'); state.package=await r.json(); return state.package; }}
async function loadDemoSafetyReport(){{ const r=await fetch('./demo_safety_report.json'); state.safety=await r.json(); return state.safety; }}
async function loadDemoValidationSummary(){{ const r=await fetch('./demo_validation_summary.json'); state.validation=await r.json(); return state.validation; }}
function text(id,v){{ const n=document.getElementById(id); if(n) n.textContent=v; }}
function renderDemoHome(d){{ text('demo-home-panel','本地演示包只是静态演示材料，不是审批授权。 '+JSON.stringify(d)); }}
function renderDemoGuide(d){{ text('demo-guide-panel','demo guide 不是审批授权，不下单。 '+JSON.stringify(d)); }}
function renderDemoRouteMap(d){{ text('demo-route-map-panel',JSON.stringify(d)); }}
function renderDemoAssetManifest(d){{ text('demo-asset-manifest-panel',JSON.stringify(d)); }}
function renderDemoPackageIndex(d){{ text('demo-package-index-panel','只列本地演示材料，不触发任何任务。 '+JSON.stringify(d)); }}
function renderDemoSafetyReport(d){{ text('demo-safety-report-panel','不调用 xttrader；不下单；不查询真实账户；不发送真实通知。 '+JSON.stringify(d)); }}
function renderDemoValidationSummary(d){{ text('demo-validation-summary-panel',JSON.stringify(d)); }}
function searchDemoReadOnly(){{ return (document.getElementById('demoSearchInput')||{{value:''}}).value; }}
function copyDemoSectionReadOnly(){{ if(navigator.clipboard) navigator.clipboard.writeText('只读演示材料，不是审批授权，不是交易授权。'); }}
function renderForbiddenRouteState(route){{ text('error-state','该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。 '+route); }}
function renderCurrentRoute(){{ let route=window.location.hash||'#/demo'; if(route==='#/'||route==='') route='#/demo'; if(FORBIDDEN_ROUTES.includes(route)){{ renderForbiddenRouteState(route); return; }} if(!ALLOWED_ROUTES.includes(route)){{ text('empty-state','Empty State'); return; }} text('loading-state','Loaded '+route); updateLastLoadedAt(); }}
function updateLastLoadedAt(){{ document.body.dataset.lastLoadedAt=new Date().toISOString(); }}
window.addEventListener('hashchange',renderCurrentRoute);
window.addEventListener('DOMContentLoaded',async()=>{{ try{{ await Promise.all([loadDemoManifest(),loadDemoGuide(),loadDemoRouteMap(),loadDemoAssetManifest(),loadDemoPackageIndex(),loadDemoSafetyReport(),loadDemoValidationSummary()]); renderDemoHome(state.manifest); renderDemoGuide(state.guide); renderDemoRouteMap(state.routes); renderDemoAssetManifest(state.assets); renderDemoPackageIndex(state.package); renderDemoSafetyReport(state.safety); renderDemoValidationSummary(state.validation); renderCurrentRoute(); }}catch(e){{ text('error-state',String(e)); }} }});
'''
def build_demo_style_css(): return 'body{font-family:system-ui;margin:0;background:#f8fafc;color:#111827}header,footer,.safety-banner,nav,section,.toolbar{margin:12px;padding:16px;border-radius:12px;background:white}.safety-banner{border:2px solid #f59e0b;background:#fffbeb}nav a{display:inline-block;margin:4px;color:#2563eb}button{border:1px solid #94a3b8;background:#e2e8f0;border-radius:8px;padding:8px}input{padding:8px;border:1px solid #94a3b8;border-radius:8px}'
