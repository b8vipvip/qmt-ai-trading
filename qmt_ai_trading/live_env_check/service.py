from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .checks import *
from .formatters import format_live_env_check_report_json, format_live_env_check_report_markdown
from .models import LiveEnvCheckConfig, LiveEnvCheckDecision, LiveEnvCheckReport, LiveEnvCheckStatus
from .safety import build_default_live_env_check_config, sanitize_live_env_check_metadata, validate_live_env_check_report_safety

def run_live_env_check(*, repo_root='.', config: LiveEnvCheckConfig | None=None, scheduler_preview_text=None, dashboard_text=None, notification_dry_run_text=None, data_quality_text=None, agent_text=None, live_manual_prep_text=None, gray_decision_text=None, pipeline_text=None, final_acceptance_text=None, metadata=None) -> LiveEnvCheckReport:
    cfg=config or build_default_live_env_check_config(metadata=metadata or {})
    root=Path(repo_root)
    checks=[check_project_files(root), check_gitignore_runtime_patterns(root), check_sync_script_protected(root), check_no_sensitive_files(root), check_capital_config(cfg), check_allowed_symbols(cfg)]
    if scheduler_preview_text is not None: checks.append(check_scheduler_preview_text(scheduler_preview_text)); checks.append(check_live_flags_absent(scheduler_preview_text))
    else: checks.append(LiveEnvCheckItem("scheduler_preview_missing", S.SCHEDULER, St.WARN, "Scheduler preview evidence missing", "No scheduler preview text/file was provided.", remediation="Provide register task dry-run preview."))
    checks += [check_dashboard_read_only(text=dashboard_text), check_notification_dry_run(text=notification_dry_run_text), check_data_quality_read_only(text=data_quality_text), check_agent_read_only(text=agent_text), check_live_manual_prep_evidence(text=live_manual_prep_text), check_risk_approval_paper_chain(text="\n".join(x for x in [gray_decision_text, pipeline_text, final_acceptance_text] if x))]
    decision, blockers, warnings = aggregate_live_env_checks(checks, cfg)
    report=LiveEnvCheckReport(decision=decision, config=cfg, checks=checks, blocked_reasons=blockers, warnings=warnings, success=decision==LiveEnvCheckDecision.READY_FOR_ENV_REVIEW, metadata=sanitize_live_env_check_metadata(metadata or {}))
    report.summary=f"Live environment read-only check completed with {len(checks)} checks."
    report.message="READY_FOR_ENV_REVIEW only means materials may be sent to manual environment review; it does not authorize live trading."
    return validate_live_env_check_report_safety(report)

def _read_optional(path):
    if not path: return None
    p=Path(path)
    if not p.exists(): return None
    if any(x in p.name.lower() for x in ('.env','token','key','password','secret')): return None
    return p.read_text(encoding='utf-8', errors='replace')

def run_live_env_check_from_files(*, repo_root='.', config=None, scheduler_preview_file=None, dashboard_path=None, notification_dry_run_report=None, data_quality_report=None, agent_memo=None, live_manual_prep_package=None, gray_decision_package=None, pipeline_report=None, final_acceptance_report=None, metadata=None):
    return run_live_env_check(repo_root=repo_root, config=config, scheduler_preview_text=_read_optional(scheduler_preview_file), dashboard_text=_read_optional(dashboard_path), notification_dry_run_text=_read_optional(notification_dry_run_report), data_quality_text=_read_optional(data_quality_report), agent_text=_read_optional(agent_memo), live_manual_prep_text=_read_optional(live_manual_prep_package), gray_decision_text=_read_optional(gray_decision_package), pipeline_text=_read_optional(pipeline_report), final_acceptance_text=_read_optional(final_acceptance_report), metadata=metadata)

def save_live_env_check_report(report, output_path):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
    text=format_live_env_check_report_json(report) if p.suffix.lower()=='.json' else format_live_env_check_report_markdown(report)
    p.write_text(text, encoding='utf-8')

def load_live_env_check_report(path):
    from .models import LiveEnvCheckItem
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    cfg=LiveEnvCheckConfig(**data.get('config',{})); checks=[LiveEnvCheckItem(**c) for c in data.get('checks',[])]
    return LiveEnvCheckReport(report_id=data.get('report_id',''), created_at=data.get('created_at',''), decision=data.get('decision', LiveEnvCheckDecision.NEED_MORE_EVIDENCE), config=cfg, checks=checks, blocked_reasons=data.get('blocked_reasons',[]), warnings=data.get('warnings',[]), summary=data.get('summary',''), safety_note=data.get('safety_note',''), success=data.get('success',False), message=data.get('message',''), metadata=data.get('metadata',{}))
