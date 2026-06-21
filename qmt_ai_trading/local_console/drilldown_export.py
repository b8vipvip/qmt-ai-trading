from __future__ import annotations
import json, re
from .drilldown_models import ExportSnapshot, ExportManifest, to_plain
from .drilldown_safety import assert_export_path_is_safe, assert_export_payload_is_safe, assert_no_sensitive_export_sources

def sanitize_export_filename(name: str) -> str:
    name=re.sub(r'[^A-Za-z0-9_.-]+','_',name or 'snapshot').strip('._') or 'snapshot'
    assert_export_path_is_safe(name)
    return name

def sanitize_export_payload(payload):
    assert_export_payload_is_safe(payload)
    return payload

def validate_export_sources(sources):
    assert_no_sensitive_export_sources(sources); return list(sources)

def build_export_snapshot(report_id='stage70-overview', payload=None):
    payload=sanitize_export_payload(payload or {'summary':'本地只读复核摘要，不是交易授权。','note':'导出仅为本地 Markdown/JSON 复核快照，不是交易授权。','read_only':True,'dry_run_only':True,'no_trade_authorization':True})
    return ExportSnapshot(report_id=report_id,payload=payload)

def build_markdown_snapshot(snapshot: ExportSnapshot) -> str:
    return f"# Stage70 Export Snapshot\n\n- read_only={snapshot.read_only}\n- dry_run_only={snapshot.dry_run_only}\n- no_trade_authorization={snapshot.no_trade_authorization}\n- note: {snapshot.note}\n\n```json\n{json.dumps(to_plain(snapshot),ensure_ascii=False,indent=2)}\n```\n"

def build_json_snapshot(snapshot: ExportSnapshot) -> str:
    return json.dumps(to_plain(snapshot),ensure_ascii=False,indent=2)

def build_export_manifest(output_dir='local_console_drilldown_stage70', sources=None):
    sources=validate_export_sources(sources or ['local_console_drilldown_report.md','report_detail_index.md','drilldown_route_map.md'])
    return ExportManifest(output_dir=output_dir,sources=sources)
