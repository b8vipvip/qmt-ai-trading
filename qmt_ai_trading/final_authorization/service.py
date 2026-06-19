from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .checklist import build_final_authorization_checklist, build_final_authorization_signoff_placeholders, default_final_forbidden_items, default_final_residual_risks, default_future_stage_requirements
from .evidence import aggregate_final_authorization_decision, collect_final_authorization_evidence
from .formatters import format_final_authorization_package_json, format_final_authorization_package_markdown
from .models import FinalAuthorizationConfig, FinalAuthorizationEvidence, FinalAuthorizationPackage, SAFETY_NOTE
from .safety import build_default_final_authorization_config, validate_final_authorization_package_safety

def run_final_authorization_package(*, config: FinalAuthorizationConfig|None=None, evidence: list[FinalAuthorizationEvidence]|None=None, metadata: dict[str,Any]|None=None)->FinalAuthorizationPackage:
    cfg=config or build_default_final_authorization_config(); ev=list(evidence or [])
    decision, blocked, warnings=aggregate_final_authorization_decision(ev,cfg)
    pkg=FinalAuthorizationPackage(decision=decision, config=cfg, evidence=ev, blocked_reasons=blocked, warnings=warnings, metadata=metadata or {}, safety_note=SAFETY_NOTE)
    pkg.checklist=build_final_authorization_checklist(pkg); pkg.forbidden_items=default_final_forbidden_items(); pkg.residual_risks=default_final_residual_risks(); pkg.future_stage_requirements=default_future_stage_requirements(); pkg.signoff_placeholders=build_final_authorization_signoff_placeholders(pkg)
    pkg.success=(getattr(pkg.decision,"value",pkg.decision)!="BLOCKED"); pkg.message=f"Final authorization package decision={getattr(pkg.decision,'value',pkg.decision)}; review-only dry-run."
    return validate_final_authorization_package_safety(pkg)
def run_final_authorization_package_from_files(*, config: FinalAuthorizationConfig|None=None, **paths: Any)->FinalAuthorizationPackage:
    return run_final_authorization_package(config=config, evidence=collect_final_authorization_evidence(**paths), metadata={"source":"local_files"})
def save_final_authorization_package(package: FinalAuthorizationPackage, output_path: str|Path):
    path=Path(output_path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_final_authorization_package_json(package) if path.suffix.lower()==".json" else format_final_authorization_package_markdown(package), encoding="utf-8"); return path
def load_final_authorization_package(path: str|Path)->FinalAuthorizationPackage:
    data=json.loads(Path(path).read_text(encoding="utf-8")); return FinalAuthorizationPackage(**{k:v for k,v in data.items() if k in FinalAuthorizationPackage.__dataclass_fields__})
