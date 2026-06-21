from __future__ import annotations
from .closure_models import *
SAFETY_BANNER='本地只读控制台；不是实盘授权；不下单；不调用 xttrader；不查询真实账户；不发送真实通知；UI 产品化收口材料只是本地复核材料，不是审批授权。'
ALLOWED_ROUTES=['#/closure','#/closure/stages','#/closure/capabilities','#/closure/safety','#/closure/demo','#/closure/routes','#/closure/assets','#/closure/risks','#/closure/conclusion','#/closure/roadmap','#/demo','#/demo/guide','#/demo/package','#/help','#/ui-acceptance','#/dashboard','#/next']
FORBIDDEN_ROUTES=['#/order','#/orders','#/trade','#/execute','#/approve','#/approval','#/auto-approve','#/live','#/notify','#/account','#/positions','#/assets']
PACKAGE_FILES=['index.html','app.js','style.css','ui_productization_closure_report.md','ui_productization_closure_report.json','stage_overview.md','stage_overview.json','capability_matrix.md','capability_matrix.json','safety_boundary_table.md','safety_boundary_table.json','readonly_demo_entry.md','readonly_demo_entry.json','route_coverage_summary.md','route_coverage_summary.json','asset_coverage_summary.md','asset_coverage_summary.json','risk_limitation_summary.md','risk_limitation_summary.json','final_acceptance_conclusion_draft.md','final_acceptance_conclusion_draft.json','future_roadmap_recommendation.md','future_roadmap_recommendation.json','closure_safety_report.md','closure_safety_report.json']

def build_stage_overview(): return [UiStageOverviewItem('Stage61-75','API Gateway / 本地控制台 / UI 产品化路线',LocalConsoleClosureStatus.PASS,'Stage75 是 Stage61-75 UI 产品化路线收口层。'),UiStageOverviewItem('Stage75','UI 产品化收口层',LocalConsoleClosureStatus.PASS,'只生成本地静态只读收口材料。')]
def build_capability_matrix(): return [UiCapabilityMatrixItem('UI 产品化阶段总览',LocalConsoleClosureFeatureType.STAGE_OVERVIEW),UiCapabilityMatrixItem('UI 能力矩阵',LocalConsoleClosureFeatureType.CAPABILITY_MATRIX),UiCapabilityMatrixItem('安全边界总表',LocalConsoleClosureFeatureType.SAFETY_BOUNDARY_TABLE),UiCapabilityMatrixItem('只读演示入口汇总',LocalConsoleClosureFeatureType.READONLY_DEMO_ENTRY),UiCapabilityMatrixItem('最终验收结论草稿',LocalConsoleClosureFeatureType.FINAL_ACCEPTANCE_DRAFT,'True'== 'True','只是本地复核草稿，不是审批授权。')]
def build_safety_boundary_table(): return [SafetyBoundaryTableItem('不调用 xttrader',LocalConsoleClosureSeverity.INFO,LocalConsoleClosureStatus.PASS,'安全声明；在可执行代码中出现真实调用才是 CRITICAL。'),SafetyBoundaryTableItem('不下单',LocalConsoleClosureSeverity.INFO,LocalConsoleClosureStatus.PASS,'不提供交易按钮。'),SafetyBoundaryTableItem('不查询真实账户',LocalConsoleClosureSeverity.INFO,LocalConsoleClosureStatus.PASS,'不提供账户/持仓/订单/成交入口。'),SafetyBoundaryTableItem('不发送真实通知',LocalConsoleClosureSeverity.INFO,LocalConsoleClosureStatus.PASS,'无通知接口。'),SafetyBoundaryTableItem('不自动 approve',LocalConsoleClosureSeverity.INFO,LocalConsoleClosureStatus.PASS,'不生成审批动作。')]
def build_readonly_demo_entry(): return [ReadonlyDemoEntryItem('#/demo','Stage74 demo package',True,'只读演示首页入口。'),ReadonlyDemoEntryItem('#/demo/guide','Stage74 demo guide',True,'只读说明入口。'),ReadonlyDemoEntryItem('#/demo/package','Stage74 demo package index',True,'只读包索引入口。')]
def build_route_coverage_summary(): return [UiRouteCoverageSummaryItem(r,r not in FORBIDDEN_ROUTES,r.replace('#/','').replace('/','-')+'-panel','只读路由。' if r not in FORBIDDEN_ROUTES else '该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。') for r in ALLOWED_ROUTES+FORBIDDEN_ROUTES]
def build_asset_coverage_summary(): return [UiAssetCoverageSummaryItem(f,'html' if f.endswith('.html') else 'javascript' if f.endswith('.js') else 'css' if f.endswith('.css') else 'markdown/json',True,'本地静态只读材料，不包含敏感文件、运行日志、真实行情数据或账户数据。') for f in PACKAGE_FILES]
def build_risk_limitation_summary(): return [RiskLimitationSummaryItem('UI 收口不等于实盘授权','不提供交易、账户、通知和审批动作。','人工复核后进入 Stage76 路线重审。'),RiskLimitationSummaryItem('静态材料证据依赖上游阶段','缺失 Stage74 证据时只能 NEED_MORE_EVIDENCE。','补齐本地 Stage74 只读演示包。')]
def build_final_acceptance_conclusion_draft(): return FinalAcceptanceConclusionDraft()
def build_future_roadmap_recommendation(): return [FutureRoadmapRecommendationItem(),FutureRoadmapRecommendationItem('Stage76 safety','先审查 Stage1-75 成果、缺口、安全边界、数据质量和 UI 成熟度，不直接进入实盘。')]
def build_closure_safety_report(findings=None):
    findings=findings or []
    return ClosureSafetyReport(findings,sum(1 for f in findings if f.severity==LocalConsoleClosureSeverity.CRITICAL),[f'{f.severity.value} {f.marker} {f.path}' for f in findings if f.severity!=LocalConsoleClosureSeverity.CRITICAL])

def build_closure_index_html():
    nav=''.join(f'<a href="{r}">{r}</a>' for r in ALLOWED_ROUTES)
    panels=''.join(f'<section id="{pid}"><h2>{title}</h2></section>' for pid,title in [('closure-home-panel','UI Productization Closure Home Panel'),('stage-overview-panel','Stage Overview Panel'),('capability-matrix-panel','Capability Matrix Panel'),('safety-boundary-table-panel','Safety Boundary Table Panel'),('readonly-demo-entry-panel','Read-only Demo Entry Panel'),('route-coverage-summary-panel','Route Coverage Summary Panel'),('asset-coverage-summary-panel','Asset Coverage Summary Panel'),('risk-limitation-summary-panel','Risk and Limitation Summary Panel'),('final-acceptance-conclusion-draft-panel','Final Acceptance Conclusion Draft Panel'),('future-roadmap-recommendation-panel','Future Roadmap Recommendation Panel'),('closure-safety-report-panel','Closure Safety Report Panel'),('stage74-demo-evidence-panel','Stage74 Demo Evidence Panel')])
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Stage75 UI Productization Closure Layer</title><link rel="stylesheet" href="./style.css"></head><body><header><h1>QMT AI Trading 本地只读控制台</h1><p>Header / Project Title - Stage75 UI 产品化收口层</p></header><aside class="safety-banner">Safety Banner：{SAFETY_BANNER}</aside><nav>{nav}</nav><main id="app"><div class="toolbar"><input id="closureSearchInput" placeholder="只读搜索收口材料"><button id="searchClosureButton" type="button">Search Closure</button><button id="copyClosureSectionButton" type="button">Copy Closure Section</button><button id="openClosurePackageButton" type="button">Open Closure Package</button><button id="toggleClosureItemButton" type="button">Toggle Closure Item</button></div>{panels}<section id="loading-state">Loading State</section><section id="error-state">Error State</section><section id="empty-state">Empty State</section></main><footer>Footer：READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW 只表示 UI 产品化收口层材料可供人工复核，不是实盘授权。</footer><script src="./app.js"></script></body></html>'''

def build_closure_app_js():
    return f'''const ALLOWED_ROUTES={ALLOWED_ROUTES!r};
const FORBIDDEN_ROUTES={FORBIDDEN_ROUTES!r};
const state={{}};
async function loadClosureReport(){{ const r=await fetch('./ui_productization_closure_report.json'); state.report=await r.json(); return state.report; }}
async function loadStageOverview(){{ const r=await fetch('./stage_overview.json'); state.stages=await r.json(); return state.stages; }}
async function loadCapabilityMatrix(){{ const r=await fetch('./capability_matrix.json'); state.capabilities=await r.json(); return state.capabilities; }}
async function loadSafetyBoundaryTable(){{ const r=await fetch('./safety_boundary_table.json'); state.safetyTable=await r.json(); return state.safetyTable; }}
async function loadReadonlyDemoEntry(){{ const r=await fetch('./readonly_demo_entry.json'); state.demo=await r.json(); return state.demo; }}
async function loadRouteCoverageSummary(){{ const r=await fetch('./route_coverage_summary.json'); state.routes=await r.json(); return state.routes; }}
async function loadAssetCoverageSummary(){{ const r=await fetch('./asset_coverage_summary.json'); state.assets=await r.json(); return state.assets; }}
async function loadRiskLimitationSummary(){{ const r=await fetch('./risk_limitation_summary.json'); state.risks=await r.json(); return state.risks; }}
async function loadFinalAcceptanceConclusionDraft(){{ const r=await fetch('./final_acceptance_conclusion_draft.json'); state.conclusion=await r.json(); return state.conclusion; }}
async function loadFutureRoadmapRecommendation(){{ const r=await fetch('./future_roadmap_recommendation.json'); state.roadmap=await r.json(); return state.roadmap; }}
async function loadClosureSafetyReport(){{ const r=await fetch('./closure_safety_report.json'); state.closureSafety=await r.json(); return state.closureSafety; }}
function text(id,v){{ const n=document.getElementById(id); if(n) n.textContent=v; }}
function renderClosureHome(d){{ text('closure-home-panel','本地只读控制台；UI 产品化收口材料只是本地复核材料，不是审批授权。 '+JSON.stringify(d)); }}
function renderStageOverview(d){{ text('stage-overview-panel',JSON.stringify(d)); }}
function renderCapabilityMatrix(d){{ text('capability-matrix-panel','能力矩阵只描述 UI 能力，不是审批授权。 '+JSON.stringify(d)); }}
function renderSafetyBoundaryTable(d){{ text('safety-boundary-table-panel','不调用 xttrader；不下单；不查询真实账户；不发送真实通知。 '+JSON.stringify(d)); }}
function renderReadonlyDemoEntry(d){{ text('readonly-demo-entry-panel',JSON.stringify(d)); }}
function renderRouteCoverageSummary(d){{ text('route-coverage-summary-panel',JSON.stringify(d)); }}
function renderAssetCoverageSummary(d){{ text('asset-coverage-summary-panel',JSON.stringify(d)); }}
function renderRiskLimitationSummary(d){{ text('risk-limitation-summary-panel',JSON.stringify(d)); }}
function renderFinalAcceptanceConclusionDraft(d){{ text('final-acceptance-conclusion-draft-panel','最终验收结论草稿不是审批授权，不是交易授权。 '+JSON.stringify(d)); }}
function renderFutureRoadmapRecommendation(d){{ text('future-roadmap-recommendation-panel','Stage76 先做路线重审，不越级接实盘。 '+JSON.stringify(d)); }}
function renderClosureSafetyReport(d){{ text('closure-safety-report-panel',JSON.stringify(d)); }}
function searchClosureReadOnly(){{ return (document.getElementById('closureSearchInput')||{{value:''}}).value; }}
function copyClosureSectionReadOnly(){{ if(navigator.clipboard) navigator.clipboard.writeText('只读 UI 产品化收口材料，不是审批授权，不是交易授权。'); }}
function renderForbiddenRouteState(route){{ text('error-state','该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。 '+route); }}
function renderCurrentRoute(){{ let route=window.location.hash||'#/closure'; if(route==='#/'||route==='') route='#/closure'; if(FORBIDDEN_ROUTES.includes(route)){{ renderForbiddenRouteState(route); return; }} if(!ALLOWED_ROUTES.includes(route)){{ text('empty-state','Empty State'); return; }} text('loading-state','Loaded '+route); updateLastLoadedAt(); }}
function updateLastLoadedAt(){{ document.body.dataset.lastLoadedAt=new Date().toISOString(); }}
window.addEventListener('hashchange',renderCurrentRoute);
window.addEventListener('DOMContentLoaded',async()=>{{ try{{ await Promise.all([loadClosureReport(),loadStageOverview(),loadCapabilityMatrix(),loadSafetyBoundaryTable(),loadReadonlyDemoEntry(),loadRouteCoverageSummary(),loadAssetCoverageSummary(),loadRiskLimitationSummary(),loadFinalAcceptanceConclusionDraft(),loadFutureRoadmapRecommendation(),loadClosureSafetyReport()]); renderClosureHome(state.report); renderStageOverview(state.stages); renderCapabilityMatrix(state.capabilities); renderSafetyBoundaryTable(state.safetyTable); renderReadonlyDemoEntry(state.demo); renderRouteCoverageSummary(state.routes); renderAssetCoverageSummary(state.assets); renderRiskLimitationSummary(state.risks); renderFinalAcceptanceConclusionDraft(state.conclusion); renderFutureRoadmapRecommendation(state.roadmap); renderClosureSafetyReport(state.closureSafety); renderCurrentRoute(); }}catch(e){{ text('error-state',String(e)); }} }});
'''
def build_closure_style_css(): return 'body{font-family:system-ui;margin:0;background:#f8fafc;color:#111827}header,footer,.safety-banner,nav,section,.toolbar{margin:12px;padding:16px;border-radius:12px;background:white}.safety-banner{border:2px solid #f59e0b;background:#fffbeb}nav a{display:inline-block;margin:4px;color:#2563eb}button{border:1px solid #94a3b8;background:#e2e8f0;border-radius:8px;padding:8px}input{padding:8px;border:1px solid #94a3b8;border-radius:8px}'
