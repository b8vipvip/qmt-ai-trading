from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.planning.stage76_models import Stage76RoadmapReviewDecision
from qmt_ai_trading.planning.stage76_service import Stage76RoadmapReviewConfig, run_stage76_roadmap_review, save_all_reports

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage76 read-only roadmap review materials.')
    for a,d in [('repo-root','.'),('output-dir','stage76_roadmap_review'),('closure-dir','local_console_closure_stage75'),('demo-dir','local_console_demo_stage74'),('help-dir','local_console_help_stage73'),('acceptance-dir','local_console_acceptance_stage72'),('review-dir','local_console_review_stage71')]: p.add_argument('--'+a, default=d)
    for a in ['output','json-output','completed-output','completed-json-output','ui-output','ui-json-output','architecture-output','architecture-json-output','safety-output','safety-json-output','data-output','data-json-output','trading-output','trading-json-output','ui-maturity-output','ui-maturity-json-output','blockers-output','blockers-json-output','next-output','next-json-output','stage77-output','stage77-json-output']:
        p.add_argument('--'+a, default=None)
    ns=p.parse_args(argv); root=Path(ns.repo_root); out=root/ns.output_dir; out.mkdir(parents=True,exist_ok=True)
    defaults={'output':out/'stage76_roadmap_review_report.md','json_output':out/'stage76_roadmap_review_report.json','completed_output':out/'completed_stage_summary.md','completed_json_output':out/'completed_stage_summary.json','ui_output':out/'ui_productization_recap.md','ui_json_output':out/'ui_productization_recap.json','architecture_output':out/'architecture_alignment_review.md','architecture_json_output':out/'architecture_alignment_review.json','safety_output':out/'safety_boundary_review.md','safety_json_output':out/'safety_boundary_review.json','data_output':out/'data_quality_gap_review.md','data_json_output':out/'data_quality_gap_review.json','trading_output':out/'trading_readiness_gap_review.md','trading_json_output':out/'trading_readiness_gap_review.json','ui_maturity_output':out/'ui_maturity_review.md','ui_maturity_json_output':out/'ui_maturity_review.json','blockers_output':out/'live_readiness_blockers.md','blockers_json_output':out/'live_readiness_blockers.json','next_output':out/'next_roadmap_plan.md','next_json_output':out/'next_roadmap_plan.json','stage77_output':out/'stage77_plan.md','stage77_json_output':out/'stage77_plan.json'}
    paths={k:str(Path(getattr(ns,k)) if getattr(ns,k) else v) for k,v in defaults.items()}
    cfg=Stage76RoadmapReviewConfig(ns.repo_root,ns.output_dir,ns.closure_dir,ns.demo_dir,ns.help_dir,ns.acceptance_dir,ns.review_dir)
    r=run_stage76_roadmap_review(cfg); save_all_reports(r,paths); print(r.decision.value)
    return 1 if r.decision==Stage76RoadmapReviewDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
