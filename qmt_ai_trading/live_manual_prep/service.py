from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .checklist import build_live_manual_prep_checklist, build_live_manual_signoff_placeholders, default_forbidden_items, default_residual_risks
from .evidence import aggregate_live_manual_prep_decision, collect_live_manual_prep_evidence
from .formatters import format_live_manual_prep_package_json, format_live_manual_prep_package_markdown
from .models import LiveManualPrepConfig, LiveManualPrepEvidence, LiveManualPrepPackage, SAFETY_NOTE
from .safety import build_default_live_manual_prep_config, validate_live_manual_prep_package_safety

def run_live_manual_prep_package(*, config: LiveManualPrepConfig|None=None, evidence: list[LiveManualPrepEvidence]|None=None, metadata: dict[str,Any]|None=None)->LiveManualPrepPackage:
    cfg=config or build_default_live_manual_prep_config(); ev=list(evidence or [])
    decision, blocked, warnings=aggregate_live_manual_prep_decision(ev,cfg)
    pkg=LiveManualPrepPackage(decision=decision, config=cfg, evidence=ev, blocked_reasons=blocked, warnings=warnings, metadata=metadata or {}, safety_note=SAFETY_NOTE)
    pkg.checklist=build_live_manual_prep_checklist(pkg); pkg.forbidden_items=default_forbidden_items(); pkg.residual_risks=default_residual_risks(); pkg.signoff_placeholders=build_live_manual_signoff_placeholders(pkg)
    pkg.success=(getattr(pkg.decision,"value",pkg.decision)!="BLOCKED"); pkg.message=f"Live manual approval prep decision={getattr(pkg.decision,'value',pkg.decision)}; preparation-only dry-run."
    return validate_live_manual_prep_package_safety(pkg)
def run_live_manual_prep_package_from_files(*, config: LiveManualPrepConfig|None=None, **paths: Any)->LiveManualPrepPackage:
    return run_live_manual_prep_package(config=config, evidence=collect_live_manual_prep_evidence(**paths), metadata={"source":"local_files"})
def save_live_manual_prep_package(package: LiveManualPrepPackage, output_path: str|Path):
    path=Path(output_path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_live_manual_prep_package_json(package) if path.suffix.lower()==".json" else format_live_manual_prep_package_markdown(package), encoding="utf-8"); return path
def load_live_manual_prep_package(path: str|Path)->LiveManualPrepPackage:
    data=json.loads(Path(path).read_text(encoding="utf-8")); return LiveManualPrepPackage(**{k:v for k,v in data.items() if k in LiveManualPrepPackage.__dataclass_fields__})
