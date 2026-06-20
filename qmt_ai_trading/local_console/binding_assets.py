from __future__ import annotations
from .binding_models import *
SAFETY_BANNER='本地只读控制台｜不是实盘授权｜不下单｜不调用 xttrader｜不查询真实账户｜不发送真实通知'
ROUTES=['/','#/dashboard','#/reports','#/reports/detail','#/filters','#/manifest','#/validation','#/scheduler','#/safety','#/api','#/next']
def build_bound_index_html(bundle=None):
    secs=[('dashboard-overview-section','Dashboard Overview Section'),('stage-status-section','Stage Status Cards Section'),('validation-summary-section','Latest Validation Card Section'),('warning-blocking-section','Warning / Blocking Stats Section'),('manifest-section','Manifest / Hash Section'),('scheduler-preview-section','Scheduler Preview Section'),('safety-boundary-section','Safety Boundary Section'),('api-capability-section','API Capability Section'),('detail-filter-section','Detail / Filter Section'),('report-list-section','Report List Section')]
    body='\n'.join(f'<section id="{i}"><h2>{t}</h2><div class="card" data-bind="{i}">Loading local static data...</div></section>' for i,t in secs)
    nav=''.join(f'<a href="{r}">{r}</a>' for r in ROUTES if r!='/')
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>QMT AI Trading Stage66 Local Console Binding</title><link rel="stylesheet" href="./style.css"></head><body><header><h1>QMT AI Trading 本地只读控制台</h1><p>{SAFETY_BANNER}</p></header><aside class="safety-banner" id="safety-banner">Safety Banner：{SAFETY_BANNER}</aside><nav>{nav}</nav><main>{body}</main><footer>READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW 不是实盘授权；本页面不提供下单按钮、审批按钮、账户查询入口或真实通知入口。</footer><script src="./app.js"></script></body></html>'
def build_bound_app_js():
    return """const READ_ONLY = true;
const SAFE_SOURCES = ['./data_bundle.json', './binding_manifest.json', './data_source_map.json'];
const SECTION_KEYS = {
  'dashboard-overview-section': 'dashboard',
  'stage-status-section': 'stage_status',
  'validation-summary-section': 'latest_validation',
  'warning-blocking-section': 'warnings',
  'manifest-section': 'manifest',
  'scheduler-preview-section': 'scheduler_preview',
  'safety-boundary-section': 'safety_boundary',
  'api-capability-section': 'api_capability',
  'detail-filter-section': 'detail_filters',
  'report-list-section': 'report_list'
};
function renderValue(value) { return `<pre>${JSON.stringify(value ?? { warning: 'missing data placeholder', read_only: READ_ONLY }, null, 2)}</pre>`; }
async function loadStaticBindingData() {
  const results = {};
  for (const source of SAFE_SOURCES) {
    try { results[source] = await fetch(source).then((response) => response.json()); }
    catch (error) { results[source] = { warning: String(error), read_only: READ_ONLY }; }
  }
  const bundle = results['./data_bundle.json'] || {};
  for (const [sectionId, key] of Object.entries(SECTION_KEYS)) {
    const node = document.querySelector(`[data-bind="${sectionId}"]`);
    if (node) node.innerHTML = renderValue(bundle[key]);
  }
  document.body.dataset.readOnly = String(READ_ONLY);
  return results;
}
window.addEventListener('DOMContentLoaded', () => { loadStaticBindingData(); });
"""
def build_bound_style_css(): return """body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f6f7fb;color:#182033}header,.safety-banner,nav,main,footer{padding:16px 24px}.safety-banner{background:#fff3cd;border:1px solid #ffe08a;color:#664d03;font-weight:700}nav{display:flex;gap:12px;flex-wrap:wrap;background:#102033}nav a{color:#fff;text-decoration:none}.card,section{background:#fff;border:1px solid #d9e1ef;border-radius:12px;margin:14px 0;padding:16px;box-shadow:0 1px 3px #0001}pre{white-space:pre-wrap;overflow:auto}h1,h2{margin:0 0 8px}footer{font-size:13px;color:#4b5563}\n"""
def build_data_source_map(): return {'local_console_dashboard_stage64/dashboard_card_index.json':'#dashboard-overview-section','local_console_dashboard_stage64/stage_status_cards.json':'#stage-status-section','local_console_dashboard_stage64/warning_blocking_stats.json':'#warning-blocking-section','local_console_dashboard_stage64/manifest_hash_status.json':'#manifest-section','local_console_dashboard_stage64/scheduler_preview_status.json':'#scheduler-preview-section','local_console_dashboard_stage64/safety_boundary_status.json':'#safety-boundary-section','local_console_stage62/report_list.json':'#report-list-section','local_console_detail_stage63/filter_index.json':'#detail-filter-section','api_gateway_stage61/api_gateway_report.json':'#api-capability-section','validation_logs/latest':'#validation-summary-section'}
def build_missing_data_placeholders(sources): return [LocalConsoleMissingDataPlaceholder(s.source_path,s.target_section_id) for s in sources if s.status in {LocalConsoleBindingStatus.UNAVAILABLE, LocalConsoleBindingStatus.WARN}]
def build_binding_manifest(sources): return LocalConsoleBindingManifest(sources=sources)
def build_data_bundle(*a, **k): from .binding_reader import build_data_bundle as b; return b(*a, **k)
def build_bound_asset_index(): return [{'name':'index.html','path':'index.html','read_only':True},{'name':'app.js','path':'app.js','read_only':True},{'name':'style.css','path':'style.css','read_only':True},{'name':'data_bundle.json','path':'data_bundle.json','read_only':True},{'name':'binding_manifest.json','path':'binding_manifest.json','read_only':True},{'name':'data_source_map.json','path':'data_source_map.json','read_only':True}]
def build_static_data_safety(): return StaticDataSafetyReport()
