from __future__ import annotations
from .help_models import *
SAFETY_BANNER='本地只读控制台；不是实盘授权；不下单；不调用 xttrader；不查询真实账户；不发送真实通知；本地文档/帮助层只是说明材料，不是审批授权。'
ALLOWED_ROUTES=['#/help','#/help/pages','#/help/features','#/help/safety','#/help/faq','#/help/errors','#/help/glossary','#/help/routes','#/help/package','#/ui-acceptance','#/pages','#/features','#/safety-checklist','#/open-items','#/route-coverage','#/asset-coverage','#/acceptance-conclusion','#/acceptance-package','#/review-workbench','#/reports','#/dashboard','#/next']
FORBIDDEN_ROUTES=['#/order','#/orders','#/trade','#/execute','#/approve','#/approval','#/auto-approve','#/live','#/notify','#/account','#/positions','#/assets']

def build_help_home(): return [HelpHomeItem('stage73-overview','Stage73 本地文档/帮助层','汇总帮助首页、页面说明、功能说明、安全说明、FAQ、错误处理、术语表、路由帮助映射与帮助包索引。'),HelpHomeItem('readonly-boundary','只读边界',SAFETY_BANNER)]
def build_page_help(): return [PageHelpItem(r,r.replace('#/','').replace('/',' / ') or 'help','只读页面说明：本地静态帮助材料，不是审批授权。') for r in ALLOWED_ROUTES]
def build_feature_help(): return [FeatureHelpItem('help-home',LocalConsoleHelpFeatureType.HELP_HOME,'帮助首页','展示 Stage73 帮助范围。'),FeatureHelpItem('page-help',LocalConsoleHelpFeatureType.PAGE_HELP,'页面说明','解释每个只读路由。'),FeatureHelpItem('feature-help',LocalConsoleHelpFeatureType.FEATURE_HELP,'功能说明','解释只读搜索、复制与包索引。'),FeatureHelpItem('safety-help',LocalConsoleHelpFeatureType.SAFETY_HELP,'安全说明','强调不接实盘、不下单、不查账户。'),FeatureHelpItem('faq',LocalConsoleHelpFeatureType.FAQ,'FAQ','回答本地帮助层常见问题。')]
def build_safety_help(): return [SafetyHelpItem('no-live','不是实盘授权','不下单，不调用 xttrader，不查询真实账户，不发送真实通知。'),SafetyHelpItem('no-approval','不是审批授权','help docs / FAQ / glossary 都不是审批授权，不自动 approve。'),SafetyHelpItem('no-risk-bypass','不绕过风控','UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT。')]
def build_faq(): return [FaqItem('Stage73 是否可以下单？','不可以。Stage73 只生成本地帮助文档，不提供下单按钮。'),FaqItem('FAQ 是否会引导开启实盘？','不会。FAQ 只解释只读边界，并要求保留 Risk Gate 与 Human Approval。'),FaqItem('READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW 是否代表 approval？','不是。它只表示本地文档/帮助层材料可供人工复核，不是审批授权。')]
def build_error_handling_guide(): return [ErrorHandlingItem(),ErrorHandlingItem('LOCAL_JSON_UNAVAILABLE','本地 JSON 不可用','显示 Error State，等待人工补充证据，不执行任何交易或账户动作。'),ErrorHandlingItem('EMPTY_ROUTE','空路由','默认跳转到 #/help。')]
def build_glossary(): return [GlossaryItem(),GlossaryItem('help docs','本地说明材料；不是审批授权，也不是交易授权。'),GlossaryItem('Risk Gate','风险门禁；Stage73 UI 不能绕过。'),GlossaryItem('Human Approval','人工审批边界；Stage73 不自动 approve。')]
def build_route_help_map(): return [RouteHelpMapItem(r,r.replace('#/','').replace('/','-')+'-panel',True,'只读帮助/验收路由。') for r in ALLOWED_ROUTES]+[RouteHelpMapItem(r,'forbidden-route-panel',False,'该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。') for r in FORBIDDEN_ROUTES]
def build_help_package_index(): return [HelpPackageIndexItem(n,t) for n,t in [('help_home.md','Help Home'),('page_help.md','Page Help'),('feature_help.md','Feature Help'),('safety_help.md','Safety Help'),('faq.md','FAQ'),('error_handling_guide.md','Error Handling Guide'),('glossary.md','Glossary'),('route_help_map.md','Route Help Map'),('help_package_index.md','Help Package Index'),('docs_safety_report.md','Docs Safety Report'),('next_local_demo_package_plan.md','Stage74 Plan')]]
def build_docs_safety_report(findings=None):
    findings=findings or []; return DocsSafetyReport(findings,sum(1 for f in findings if f.severity==LocalConsoleHelpSeverity.CRITICAL),[f'{f.severity.value} {f.marker} {f.path}' for f in findings if f.severity!=LocalConsoleHelpSeverity.CRITICAL])
def build_next_local_demo_package_plan(): return NextLocalDemoPackagePlanReport()

def build_help_index_html():
    nav=''.join(f'<a href="{r}">{r}</a>' for r in ALLOWED_ROUTES)
    panels=''.join([f'<section id="{pid}"><h2>{title}</h2></section>' for pid,title in [('help-home-panel','Help Home Panel'),('page-help-panel','Page Help Panel'),('feature-help-panel','Feature Help Panel'),('safety-help-panel','Safety Help Panel'),('faq-panel','FAQ Panel'),('error-handling-panel','Error Handling Panel'),('glossary-panel','Glossary Panel'),('route-help-map-panel','Route Help Map Panel'),('help-package-index-panel','Help Package Index Panel'),('stage72-ui-acceptance-evidence-panel','Stage72 UI Acceptance Evidence Panel')]])
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Stage73 Local Documentation and Help Layer</title><link rel="stylesheet" href="./style.css"></head><body><header><h1>QMT AI Trading 本地只读控制台</h1><p>Header / Project Title - Stage73 本地文档/帮助层</p></header><aside class="safety-banner">Safety Banner：{SAFETY_BANNER}</aside><nav aria-label="Navigation Tabs">{nav}</nav><main id="app"><div class="toolbar"><input id="helpSearchInput" placeholder="只读搜索帮助"><button id="searchHelpButton" type="button">Search Help</button><button id="copyHelpSectionButton" type="button">Copy Help Section</button><button id="openHelpPackageButton" type="button">Open Help Package</button><button id="toggleFaqItemButton" type="button">Toggle FAQ</button></div>{panels}<section id="loading-state">Loading State</section><section id="error-state">Error State</section><section id="empty-state">Empty State</section></main><footer>Footer：READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW 只表示本地文档/帮助层材料可供人工复核，不是实盘授权。</footer><script src="./app.js"></script></body></html>'''

def build_help_app_js():
    return f'''const ALLOWED_ROUTES={ALLOWED_ROUTES!r};
const FORBIDDEN_ROUTES={FORBIDDEN_ROUTES!r};
const state={{}};
async function loadHelpHome(){{ const r=await fetch('./help_home.json'); state.helpHome=await r.json(); return state.helpHome; }}
async function loadPageHelp(){{ const r=await fetch('./page_help.json'); state.pageHelp=await r.json(); return state.pageHelp; }}
async function loadFeatureHelp(){{ const r=await fetch('./feature_help.json'); state.featureHelp=await r.json(); return state.featureHelp; }}
async function loadSafetyHelp(){{ const r=await fetch('./safety_help.json'); state.safetyHelp=await r.json(); return state.safetyHelp; }}
async function loadFaq(){{ const r=await fetch('./faq.json'); state.faq=await r.json(); return state.faq; }}
async function loadErrorHandlingGuide(){{ const r=await fetch('./error_handling_guide.json'); state.errors=await r.json(); return state.errors; }}
async function loadGlossary(){{ const r=await fetch('./glossary.json'); state.glossary=await r.json(); return state.glossary; }}
async function loadRouteHelpMap(){{ const r=await fetch('./route_help_map.json'); state.routes=await r.json(); return state.routes; }}
async function loadHelpPackageIndex(){{ const r=await fetch('./help_package_index.json'); state.package=await r.json(); return state.package; }}
async function loadDocsSafetyReport(){{ const r=await fetch('./docs_safety_report.json'); state.docsSafety=await r.json(); return state.docsSafety; }}
function text(id,v){{ const n=document.getElementById(id); if(n) n.textContent=v; }}
function renderHelpHome(d){{ text('help-home-panel','本地文档/帮助层只是说明材料，不是审批授权。 '+JSON.stringify(d)); }}
function renderPageHelp(d){{ text('page-help-panel',JSON.stringify(d)); }}
function renderFeatureHelp(d){{ text('feature-help-panel',JSON.stringify(d)); }}
function renderSafetyHelp(d){{ text('safety-help-panel','不调用 xttrader；不下单；不查询真实账户；不发送真实通知。 '+JSON.stringify(d)); }}
function renderFaq(d){{ text('faq-panel','FAQ 不引导开启实盘或绕过风控。 '+JSON.stringify(d)); }}
function renderErrorHandlingGuide(d){{ text('error-handling-panel',JSON.stringify(d)); }}
function renderGlossary(d){{ text('glossary-panel','glossary 不把 approval 描述成自动授权。 '+JSON.stringify(d)); }}
function renderRouteHelpMap(d){{ text('route-help-map-panel',JSON.stringify(d)); }}
function renderHelpPackageIndex(d){{ text('help-package-index-panel','只列本地帮助材料，不触发任何任务。 '+JSON.stringify(d)); }}
function searchHelpReadOnly(){{ return (document.getElementById('helpSearchInput')||{{value:''}}).value; }}
function copyHelpSectionReadOnly(){{ if(navigator.clipboard) navigator.clipboard.writeText('只读帮助材料，不是审批授权，不是交易授权。'); }}
function renderForbiddenRouteState(route){{ text('error-state','该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。 '+route); }}
function renderCurrentRoute(){{ let route=window.location.hash||'#/help'; if(route==='#/'||route==='') route='#/help'; if(FORBIDDEN_ROUTES.includes(route)){{ renderForbiddenRouteState(route); return; }} if(!ALLOWED_ROUTES.includes(route)){{ text('empty-state','Empty State'); return; }} text('loading-state','Loaded '+route); updateLastLoadedAt(); }}
function updateLastLoadedAt(){{ document.body.dataset.lastLoadedAt=new Date().toISOString(); }}
window.addEventListener('hashchange',renderCurrentRoute);
window.addEventListener('DOMContentLoaded',async()=>{{ try{{ await Promise.all([loadHelpHome(),loadPageHelp(),loadFeatureHelp(),loadSafetyHelp(),loadFaq(),loadErrorHandlingGuide(),loadGlossary(),loadRouteHelpMap(),loadHelpPackageIndex(),loadDocsSafetyReport()]); renderHelpHome(state.helpHome); renderPageHelp(state.pageHelp); renderFeatureHelp(state.featureHelp); renderSafetyHelp(state.safetyHelp); renderFaq(state.faq); renderErrorHandlingGuide(state.errors); renderGlossary(state.glossary); renderRouteHelpMap(state.routes); renderHelpPackageIndex(state.package); renderCurrentRoute(); }}catch(e){{ text('error-state',String(e)); }} }});
'''
def build_help_style_css(): return 'body{font-family:system-ui;margin:0;background:#f8fafc;color:#111827}header,footer,.safety-banner,nav,section,.toolbar{margin:12px;padding:16px;border-radius:12px;background:white}.safety-banner{border:2px solid #f59e0b;background:#fffbeb}nav a{display:inline-block;margin:4px;color:#2563eb}button{border:1px solid #94a3b8;background:#e2e8f0;border-radius:8px;padding:8px}input{padding:8px;border:1px solid #94a3b8;border-radius:8px}'
