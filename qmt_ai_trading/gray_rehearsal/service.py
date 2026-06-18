from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping
from .checklist import build_gray_rehearsal_checklist
from .formatters import format_gray_rehearsal_report_json, format_gray_rehearsal_report_markdown
from .models import GrayRehearsalConfig, GrayRehearsalDecision, GrayRehearsalReport
from .safety import build_default_gray_rehearsal_config, sanitize_gray_rehearsal_metadata, validate_gray_rehearsal_report_safety
from .scenarios import RUNNERS, build_default_rehearsal_scenarios

def _read_optional(path: str | Path | None) -> str:
    if not path: return ""
    p=Path(path)
    if not p.exists() or not p.is_file(): return ""
    return p.read_text(encoding="utf-8", errors="replace")[:20000]

def run_gray_rehearsal(*, config: GrayRehearsalConfig | None=None, context: Mapping[str, Any] | None=None, metadata: Mapping[str, Any] | None=None) -> GrayRehearsalReport:
    cfg=config or build_default_gray_rehearsal_config(metadata=metadata or {})
    ctx=dict(context or {})
    scenarios=[]
    for typ in build_default_rehearsal_scenarios(cfg):
        scenarios.append(RUNNERS[typ](ctx,cfg))
    has_fail=any(str(s.decision)=="GrayRehearsalDecision.FAIL" or getattr(s.decision,"value",s.decision)=="FAIL" for s in scenarios)
    has_warn=any(getattr(s.decision,"value",s.decision) in {"WARN","BLOCKED"} or s.warnings or s.blocked_reasons for s in scenarios)
    decision=GrayRehearsalDecision.FAIL if has_fail else (GrayRehearsalDecision.WARN if has_warn else GrayRehearsalDecision.PASS)
    report=GrayRehearsalReport(decision=decision, config=cfg, scenarios=scenarios, summary="Stage 35 small-capital gray rehearsal completed in dry-run/local-file mode.", success=not has_fail, metadata=sanitize_gray_rehearsal_metadata(metadata or {}))
    report.checklist=build_gray_rehearsal_checklist(report)
    validate_gray_rehearsal_report_safety(report)
    return report

def run_gray_rehearsal_from_files(*, pipeline_report=None, monitoring_report=None, data_quality_report=None, agent_memo=None, live_gray_report=None, notification_dry_run_report=None, dashboard_path=None, config: GrayRehearsalConfig | None=None, metadata: Mapping[str,Any] | None=None) -> GrayRehearsalReport:
    ctx={"pipeline_report":_read_optional(pipeline_report),"monitoring_report":_read_optional(monitoring_report),"data_quality_report":_read_optional(data_quality_report),"agent_memo":_read_optional(agent_memo),"live_gray_report":_read_optional(live_gray_report),"notification_dry_run_report":_read_optional(notification_dry_run_report),"dashboard_path":str(dashboard_path or "") if dashboard_path and Path(dashboard_path).exists() else ""}
    return run_gray_rehearsal(config=config, context=ctx, metadata=metadata)

def save_gray_rehearsal_report(report: GrayRehearsalReport, output_path: str | Path):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
    text=format_gray_rehearsal_report_json(report) if p.suffix.lower()==".json" else format_gray_rehearsal_report_markdown(report)
    p.write_text(text, encoding="utf-8"); return p

def load_gray_rehearsal_report(path: str | Path) -> GrayRehearsalReport:
    from .models import GrayRehearsalConfig, GrayRehearsalScenarioResult, GrayRehearsalStep
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    cfg=GrayRehearsalConfig(**data.get("config",{}))
    scenarios=[]
    for s in data.get("scenarios",[]):
        steps=[GrayRehearsalStep(**x) for x in s.get("steps",[])]
        s={k:v for k,v in s.items() if k!="steps"}; scenarios.append(GrayRehearsalScenarioResult(steps=steps, **s))
    return GrayRehearsalReport(config=cfg, scenarios=scenarios, **{k:v for k,v in data.items() if k not in {"config","scenarios"}})
