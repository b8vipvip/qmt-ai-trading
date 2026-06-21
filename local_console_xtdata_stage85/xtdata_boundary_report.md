# xtdata_boundary_report

```json
{
  "created_at": "2026-01-01T00:00:00+00:00#Stage85-cb25e6cbe432",
  "dry_run": true,
  "enabled": false,
  "mini_qmt_connected": false,
  "no_order_submitted": true,
  "no_qmt_trader_api": true,
  "output_dir": "local_console_xtdata_stage85",
  "read_only": true,
  "real_market_data": false,
  "report_path": "local_console_xtdata_stage85/xtdata_boundary_report.md",
  "safety_status": "PASS",
  "sandbox_fallback": true,
  "stage": "Stage85",
  "status": "SUCCESS",
  "task_id": "xtdata_boundary_dry_run",
  "warnings": [
    "Stage85 performs configuration-only dry-run probes."
  ],
  "workflow": [
    "Stage84 Sandbox Market Gateway",
    "XtData Adapter Config",
    "Import Guard",
    "Capability Probe Dry-run",
    "Safety Gate",
    "XtData Boundary Report",
    "Frontend xtdata Boundary Checklist"
  ],
  "xtdata_imported": false
}
```
