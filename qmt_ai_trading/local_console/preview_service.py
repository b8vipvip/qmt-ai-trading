from __future__ import annotations
import json
from pathlib import Path
from .preview_models import *
from .preview_routes import build_allowed_preview_routes, FORBIDDEN_ROUTES
from .preview_reader import read_json
from .preview_safety import *
from .preview_formatters import format_preview_report_md, format_json_md
FILES={'/index.html':'index.html','/app.js':'app.js','/style.css':'style.css','/data_bundle.json':'data_bundle.json','/binding_manifest.json':'binding_manifest.json','/data_source_map.json':'data_source_map.json','/static_data_safety.json':'static_data_safety.json','/':'index.html'}
def build_default_local_console_preview_config(**kw): return LocalConsolePreviewConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def run_local_console_preview_review(config=None):
    cfg=config or LocalConsolePreviewConfig(); root=Path(cfg.repo_root); static=root/cfg.static_dir; warnings=[]; blocking=[]
    routes=build_allowed_preview_routes(); evidence=[]
    rr=read_json(static/'local_console_binding_report.json'); data=rr.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}
    crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0); dec=str(data.get('decision',''))
    evidence.append(LocalConsolePreviewEvidence('Stage66',rr['source'],LocalConsolePreviewStatus.PASS if rr['status']=='PASS' else LocalConsolePreviewStatus.UNAVAILABLE,dec,crit,rr['summary'],rr.get('encoding_warning',False),rr.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else []))
    warnings += rr.get('warnings',[])
    if not static.exists(): warnings.append('Stage66 package unavailable; preview review needs more evidence')
    if not assert_host_is_localhost(cfg.host) or not assert_no_public_bind(cfg.host): blocking.append(f'public bind forbidden: {cfg.host}')
    if dec=='NO_GO' or crit>0: blocking.append('Stage66 NO_GO or critical findings present')
    files=[]
    for route,name in FILES.items():
        p=static/name; txt=p.read_text(encoding='utf-8',errors='replace') if p.exists() else ''; enc='�' in txt or 'Ã' in txt
        files.append(PreviewStaticFile(name,p.exists(),p.stat().st_size if p.exists() else 0,route,'text/html' if name.endswith('.html') else 'application/json' if name.endswith('.json') else 'text/plain',enc,['上游报告存在编码异常，已隐藏乱码正文'] if enc else []))
        for h in scan_preview_assets_for_forbidden_markers(txt,name,generated=True,executable=name.endswith('.js')):
            (blocking if h['severity']=='CRITICAL' else warnings).append(f"{h['severity']} marker {h['marker']} in {name}")
    bad_methods=assert_no_forbidden_preview_methods(['POST','PUT','PATCH','DELETE'])
    responses=[PreviewResponseManifest(route=k,source_file=v) for k,v in FILES.items()]+[PreviewResponseManifest('/health',source_file='builtin'),PreviewResponseManifest('/preview-safety',source_file='builtin'),PreviewResponseManifest('/preview-manifest',source_file='builtin')]
    boundary=PreviewSafetyBoundary(host=cfg.host,public_bind=not assert_no_public_bind(cfg.host),critical_findings=blocking,warnings=warnings)
    decision=LocalConsolePreviewDecision.READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW
    if not static.exists(): decision=LocalConsolePreviewDecision.NEED_MORE_EVIDENCE
    if blocking: decision=LocalConsolePreviewDecision.NO_GO
    return PreviewServerReport(decision,cfg,evidence,routes,files,responses,boundary,warnings,blocking,{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking),'forbidden_methods':bad_methods})
def save_local_console_preview_report(r,output,json_output): _write(output,format_preview_report_md(r)); _write_json(json_output,r)
def load_local_console_preview_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_preview_route_map_report(r): return PreviewRouteMapReport(r.routes,FORBIDDEN_ROUTES)
def save_preview_route_map_report(r,output,json_output): _write(output,format_json_md('Stage67 Preview Route Map',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_static_file_index_report(r): return PreviewStaticFileIndexReport(r.static_files)
def save_static_file_index_report(r,output,json_output): _write(output,format_json_md('Stage67 Static File Index',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_response_manifest_report(r): return PreviewResponseManifestReport(r.response_manifest)
def save_response_manifest_report(r,output,json_output): _write(output,format_json_md('Stage67 Response Manifest',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_preview_safety_report(r): return PreviewSafetyReport(r.safety_boundary)
def save_preview_safety_report(r,output,json_output): _write(output,format_json_md('Stage67 Preview Safety Boundary',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_next_console_refresh_plan_report(config=None): return NextConsoleRefreshPlanReport()
def save_next_console_refresh_plan_report(r,output,json_output): _write(output,format_json_md('Stage68 Next Console Refresh Plan',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
