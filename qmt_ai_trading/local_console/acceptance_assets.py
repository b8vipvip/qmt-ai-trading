from __future__ import annotations
from .acceptance_models import *
SAFETY_BANNER='本地只读控制台；不是实盘授权；不下单；不调用 xttrader；不查询真实账户；不发送真实通知；UI 验收汇总只是本地验收材料，不是审批授权。'
ALLOWED_ROUTES=['#/dashboard','#/ui-acceptance','#/pages','#/features','#/safety-checklist','#/open-items','#/route-coverage','#/asset-coverage','#/acceptance-conclusion','#/acceptance-package','#/review-workbench','#/review-checklist','#/review-notes','#/review-package','#/local-confirmations','#/reports','#/reports/detail','#/reports/preview','#/reports/export','#/filters','#/warnings','#/blocking-reasons','#/manifest','#/validation','#/scheduler','#/safety','#/api','#/next']
FORBIDDEN=['#/order','#/orders','#/trade','#/execute','#/approve','#/approval','#/auto-approve','#/live','#/notify','#/account','#/positions','#/assets']

def build_page_inventory(): return [UiPageInventoryItem(r, r.replace('#/','').replace('-',' ').title(), r.replace('#/','').replace('/','-')+'-panel') for r in ALLOWED_ROUTES]
def build_feature_inventory(): return [UiFeatureInventoryItem('ui-acceptance-summary',LocalConsoleAcceptanceFeatureType.UI_ACCEPTANCE_SUMMARY,'UI 验收汇总'),UiFeatureInventoryItem('page-inventory',LocalConsoleAcceptanceFeatureType.PAGE_INVENTORY,'页面清单'),UiFeatureInventoryItem('feature-inventory',LocalConsoleAcceptanceFeatureType.FEATURE_INVENTORY,'功能清单'),UiFeatureInventoryItem('safety-checklist',LocalConsoleAcceptanceFeatureType.SAFETY_CHECKLIST,'安全清单'),UiFeatureInventoryItem('open-items',LocalConsoleAcceptanceFeatureType.OPEN_ITEMS,'未完成项清单'),UiFeatureInventoryItem('route-coverage',LocalConsoleAcceptanceFeatureType.ROUTE_COVERAGE,'UI route coverage summary'),UiFeatureInventoryItem('asset-coverage',LocalConsoleAcceptanceFeatureType.ASSET_COVERAGE,'UI asset coverage summary'),UiFeatureInventoryItem('acceptance-conclusion',LocalConsoleAcceptanceFeatureType.ACCEPTANCE_CONCLUSION_DRAFT,'验收结论草稿'),UiFeatureInventoryItem('acceptance-package',LocalConsoleAcceptanceFeatureType.ACCEPTANCE_PACKAGE_INDEX,'UI 验收包索引'),UiFeatureInventoryItem('next-stage-plan',LocalConsoleAcceptanceFeatureType.NEXT_STAGE_PLAN,'Stage73 本地文档/帮助层计划')]
def build_safety_checklist(): return [UiSafetyChecklistItem('no-live','不接实盘、不下单、不调用 xttrader'),UiSafetyChecklistItem('no-account','不查询真实账户/资金/持仓/订单/成交'),UiSafetyChecklistItem('no-notify','不发送真实通知'),UiSafetyChecklistItem('no-approval','不自动 approve，不绕过 Risk Gate / Human Approval')]
def build_open_items(): return [UiOpenItem('manual-ui-acceptance','等待人工 UI 验收复核'),UiOpenItem('stage73-help-docs','Stage73 本地文档/帮助层待建设')]
def build_route_coverage(): return [UiRouteCoverageItem(r,True) for r in ALLOWED_ROUTES]+[UiRouteCoverageItem(r,False,LocalConsoleAcceptanceStatus.SKIPPED,'该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。') for r in FORBIDDEN]
def build_asset_coverage(): return [UiAssetCoverageItem(n) for n in ['index.html','app.js','style.css','ui_acceptance_summary.json','page_inventory.json','feature_inventory.json','safety_checklist.json','open_items.json','route_coverage.json','asset_coverage.json','acceptance_conclusion_draft.json','acceptance_package_index.json','ui_acceptance_safety_report.json','local_console_ui_acceptance_report.json','next_local_help_docs_plan.json']]
def build_acceptance_conclusion_draft(decision=LocalConsoleAcceptanceDecision.NEED_MORE_EVIDENCE): return AcceptanceConclusionDraft(decision)
def build_acceptance_package_index(): return [AcceptancePackageIndexItem(n,t) for n,t in [('local_console_ui_acceptance_report.md','总报告'),('ui_acceptance_summary.md','UI 验收汇总'),('page_inventory.md','页面清单'),('feature_inventory.md','功能清单'),('safety_checklist.md','安全清单'),('open_items.md','未完成项'),('route_coverage.md','路由覆盖'),('asset_coverage.md','资产覆盖'),('acceptance_conclusion_draft.md','验收结论草稿'),('ui_acceptance_safety_report.md','安全扫描'),('next_local_help_docs_plan.md','Stage73 计划')]]
def build_ui_acceptance_summary(decision=LocalConsoleAcceptanceDecision.NEED_MORE_EVIDENCE): return UiAcceptanceSummaryReport(decision)
def build_next_local_help_docs_plan(): return NextLocalHelpDocsPlanReport()
def build_ui_acceptance_safety_report(findings=None):
    findings=findings or []; return UiAcceptanceSafetyReport(findings,sum(1 for f in findings if f.severity==LocalConsoleAcceptanceSeverity.CRITICAL),[f'{f.severity.value} {f.marker} {f.path}' for f in findings if f.severity!=LocalConsoleAcceptanceSeverity.CRITICAL])

def build_acceptance_index_html():
    nav=''.join(f'<a href="{r}">{r}</a>' for r in ALLOWED_ROUTES)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Stage72 Local Console UI Acceptance Summary</title><link rel="stylesheet" href="./style.css"></head><body><header><h1>QMT AI Trading 本地只读控制台</h1><p>Header / Project Title - Stage72 本地控制台 UI 验收汇总层</p></header><aside class="safety-banner">Safety Banner：{SAFETY_BANNER}</aside><nav aria-label="Navigation Tabs">{nav}</nav><main id="app"><section id="ui-acceptance-summary-panel"><h2>UI Acceptance Summary Panel</h2><button id="exportAcceptanceSummaryButton" type="button">Export Read Only</button></section><section id="page-inventory-panel"><h2>Page Inventory Panel</h2></section><section id="feature-inventory-panel"><h2>Feature Inventory Panel</h2></section><section id="safety-checklist-panel"><h2>Safety Checklist Panel</h2><button id="toggleAcceptanceItemButton" type="button">Toggle Local Only</button></section><section id="open-items-panel"><h2>Open Items Panel</h2></section><section id="route-coverage-panel"><h2>Route Coverage Panel</h2></section><section id="asset-coverage-panel"><h2>Asset Coverage Panel</h2></section><section id="acceptance-conclusion-draft-panel"><h2>Acceptance Conclusion Draft Panel</h2><button id="copyAcceptanceConclusionButton" type="button">Copy Read Only</button></section><section id="acceptance-package-index-panel"><h2>Acceptance Package Index Panel</h2><button id="openAcceptancePackageButton" type="button">Open Package Index</button></section><section id="stage71-review-evidence-panel"><h2>Stage71 Review Evidence Panel</h2></section><section id="loading-state">Loading State</section><section id="error-state">Error State</section><section id="empty-state">Empty State</section></main><footer>Footer：READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW 只表示本地控制台 UI 验收汇总层材料可供人工复核，不是实盘授权。</footer><script src="./app.js"></script></body></html>'''

def build_acceptance_app_js():
    routes=repr(ALLOWED_ROUTES); forbidden=repr(FORBIDDEN)
    return f'''const ALLOWED_ROUTES={routes};
const FORBIDDEN_ROUTES={forbidden};
const state={{}};
async function loadJson(p){{ const r=await fetch(p); if(!r.ok) throw new Error('local json unavailable'); return r.json(); }}
async function loadAcceptanceSummary(){{ const r=await fetch('./ui_acceptance_summary.json'); state.summary=await r.json(); return state.summary; }}
async function loadPageInventory(){{ const r=await fetch('./page_inventory.json'); state.pages=await r.json(); return state.pages; }}
async function loadFeatureInventory(){{ const r=await fetch('./feature_inventory.json'); state.features=await r.json(); return state.features; }}
async function loadSafetyChecklist(){{ const r=await fetch('./safety_checklist.json'); state.safety=await r.json(); return state.safety; }}
async function loadOpenItems(){{ const r=await fetch('./open_items.json'); state.openItems=await r.json(); return state.openItems; }}
async function loadRouteCoverage(){{ const r=await fetch('./route_coverage.json'); state.routes=await r.json(); return state.routes; }}
async function loadAssetCoverage(){{ const r=await fetch('./asset_coverage.json'); state.assets=await r.json(); return state.assets; }}
async function loadAcceptancePackageIndex(){{ const r=await fetch('./acceptance_package_index.json'); state.package=await r.json(); return state.package; }}
function text(id,v){{ const n=document.getElementById(id); if(n) n.textContent=v; }}
function renderAcceptanceSummary(d){{ text('ui-acceptance-summary-panel','UI acceptance summary 只是本地验收材料，不是审批授权。 '+JSON.stringify(d)); }}
function renderPageInventory(d){{ text('page-inventory-panel',JSON.stringify(d)); }}
function renderFeatureInventory(d){{ text('feature-inventory-panel',JSON.stringify(d)); }}
function renderSafetyChecklist(d){{ text('safety-checklist-panel','不下单、不调用 xttrader、不查询真实账户、不发送真实通知。 '+JSON.stringify(d)); }}
function renderOpenItems(d){{ text('open-items-panel',JSON.stringify(d)); }}
function renderRouteCoverage(d){{ text('route-coverage-panel',JSON.stringify(d)); }}
function renderAssetCoverage(d){{ text('asset-coverage-panel',JSON.stringify(d)); }}
function renderAcceptanceConclusionDraft(d){{ text('acceptance-conclusion-draft-panel','验收结论草稿不是交易授权，不是审批授权。 '+JSON.stringify(d||{{}})); }}
function renderAcceptancePackageIndex(d){{ text('acceptance-package-index-panel','只列本地验收材料，不触发任何任务。 '+JSON.stringify(d||state.package)); }}
function copyAcceptanceConclusionReadOnly(){{ navigator.clipboard&&navigator.clipboard.writeText('只读验收结论草稿，不是审批授权，不是交易授权。'); }}
function exportAcceptanceSummaryReadOnly(){{ const blob=new Blob([JSON.stringify(state.summary||{{}},null,2)],{{type:'application/json'}}); return blob; }}
function renderForbiddenRouteState(route){{ text('error-state','该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。 '+route); }}
function renderCurrentRoute(){{ let route=window.location.hash||'#/ui-acceptance'; if(route==='#/'||route==='') route='#/ui-acceptance'; if(FORBIDDEN_ROUTES.includes(route)){{ renderForbiddenRouteState(route); return; }} if(!ALLOWED_ROUTES.includes(route)){{ text('empty-state','Empty State'); return; }} text('loading-state','Loaded '+route); updateLastLoadedAt(); }}
function updateLastLoadedAt(){{ document.body.dataset.lastLoadedAt=new Date().toISOString(); }}
window.addEventListener('hashchange',renderCurrentRoute);
window.addEventListener('DOMContentLoaded',async()=>{{ try{{ await Promise.all([loadAcceptanceSummary(),loadPageInventory(),loadFeatureInventory(),loadSafetyChecklist(),loadOpenItems(),loadRouteCoverage(),loadAssetCoverage(),loadAcceptancePackageIndex()]); renderAcceptanceSummary(state.summary); renderPageInventory(state.pages); renderFeatureInventory(state.features); renderSafetyChecklist(state.safety); renderOpenItems(state.openItems); renderRouteCoverage(state.routes); renderAssetCoverage(state.assets); renderAcceptanceConclusionDraft(state.summary&&state.summary.conclusion); renderAcceptancePackageIndex(state.package); renderCurrentRoute(); }}catch(e){{ text('error-state',String(e)); }} }});
'''

def build_acceptance_style_css(): return 'body{font-family:system-ui;margin:0;background:#f8fafc;color:#111827}header,footer,.safety-banner,nav,section{margin:12px;padding:16px;border-radius:12px;background:white} .safety-banner{border:2px solid #f59e0b;background:#fffbeb} nav a{display:inline-block;margin:4px;color:#2563eb} button{border:1px solid #94a3b8;background:#e2e8f0;border-radius:8px;padding:8px}'
