from __future__ import annotations
from .detail_models import *

def filter_reports_by_stage(reports, stage): return [r for r in reports if r.stage.lower()==str(stage).lower()]
def filter_reports_by_status(reports, status): return [r for r in reports if r.status.value==str(status) or r.status==status]
def filter_reports_by_severity(reports, severity): return [r for r in reports if r.severity.value==str(severity) or r.severity==severity]
def collect_warnings(reports):
    out=[]
    for r in reports:
        for w in r.warnings or ([] if r.status!=LocalConsoleDetailStatus.WARN else [r.summary]): out.append(ConsoleWarningItem(r.stage,str(w),LocalConsoleDetailSeverity.WARN,r.path))
    return out
def collect_blocking_reasons(reports):
    out=[]
    for r in reports:
        for b in r.blocking_reasons or ([] if r.critical_count<=0 and r.decision!='NO_GO' else [r.summary]): out.append(ConsoleBlockingReasonItem(r.stage,str(b),LocalConsoleDetailSeverity.CRITICAL,r.path))
    return out
def collect_manifest_items(reports): return [ConsoleManifestDetailItem(r.stage,r.path,r.status,r.summary,{'decision':r.decision,'critical_count':r.critical_count}) for r in reports]
def collect_validation_summary(validation_detail): return validation_detail.summary
def build_filter_index(reports, validation_detail=None, routes=None):
    return {'stage':sorted({r.stage for r in reports}), 'status':sorted({r.status.value for r in reports}), 'severity':sorted({r.severity.value for r in reports}), 'warnings':len(collect_warnings(reports)), 'blocking-reasons':len(collect_blocking_reasons(reports)), 'manifest':len(reports), 'validation_log': bool(validation_detail and validation_detail.summary), 'routes': routes or []}
