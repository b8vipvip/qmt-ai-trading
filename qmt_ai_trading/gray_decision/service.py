from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .checklist import build_gray_decision_checklist
from .evidence import aggregate_evidence_decision, collect_gray_decision_evidence
from .formatters import format_gray_decision_package_json, format_gray_decision_package_markdown
from .models import GrayDecisionConfig, GrayDecisionEvidence, GrayDecisionPackage, SAFETY_NOTE
from .safety import build_default_gray_decision_config, validate_gray_decision_package_safety

def run_gray_decision_package(*, config: GrayDecisionConfig|None=None, evidence: list[GrayDecisionEvidence]|None=None, metadata: dict[str,Any]|None=None)->GrayDecisionPackage:
    cfg=config or build_default_gray_decision_config()
    ev=list(evidence or [])
    decision, blocked, warnings=aggregate_evidence_decision(ev,cfg)
    pkg=GrayDecisionPackage(decision=decision, config=cfg, evidence=ev, blocked_reasons=blocked, warnings=warnings, metadata=metadata or {}, safety_note=SAFETY_NOTE)
    pkg.checklist=build_gray_decision_checklist(pkg); pkg.success=str(pkg.decision)!="BLOCKED"; pkg.message=f"Gray decision package decision={getattr(pkg.decision,'value',pkg.decision)}; manual-only dry-run."
    return validate_gray_decision_package_safety(pkg)
def run_gray_decision_package_from_files(*, config: GrayDecisionConfig|None=None, **paths: Any)->GrayDecisionPackage:
    return run_gray_decision_package(config=config, evidence=collect_gray_decision_evidence(**paths), metadata={"source":"local_files"})
def save_gray_decision_package(package: GrayDecisionPackage, output_path: str|Path):
    path=Path(output_path); path.parent.mkdir(parents=True, exist_ok=True)
    text=format_gray_decision_package_json(package) if path.suffix.lower()==".json" else format_gray_decision_package_markdown(package)
    path.write_text(text, encoding="utf-8"); return path
def load_gray_decision_package(path: str|Path)->GrayDecisionPackage:
    data=json.loads(Path(path).read_text(encoding="utf-8")); return GrayDecisionPackage(**{k:v for k,v in data.items() if k in GrayDecisionPackage.__dataclass_fields__})
