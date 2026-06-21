#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.review_models import LocalConsoleReviewDecision
from qmt_ai_trading.local_console.review_service import *

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='local_console_review_stage71')
    p.add_argument('--drilldown-dir',default='local_console_drilldown_stage70'); p.add_argument('--grouping-dir',default='local_console_grouping_stage69'); p.add_argument('--refresh-dir',default='local_console_refresh_stage68'); p.add_argument('--preview-dir',default='local_console_preview_stage67'); p.add_argument('--binding-dir',default='local_console_binding_stage66')
    for a,d in [('output','local_console_review_workbench_report.md'),('json-output','local_console_review_workbench_report.json'),('manifest-output','review_manifest.md'),('manifest-json-output','review_manifest.json'),('checklist-output','review_checklist.md'),('checklist-json-output','review_checklist.json'),('notes-output','review_notes_template.md'),('notes-json-output','review_notes_template.json'),('confirmation-output','local_confirmation_checklist.md'),('confirmation-json-output','local_confirmation_checklist.json'),('package-output','review_package_index.md'),('package-json-output','review_package_index.json'),('safety-output','review_safety_report.md'),('safety-json-output','review_safety_report.json'),('plan-output','next_ui_acceptance_summary_plan.md'),('plan-json-output','next_ui_acceptance_summary_plan.json')]: p.add_argument('--'+a, default=None)
    args=p.parse_args(argv); out=Path(args.repo_root)/args.output_dir
    def val(name,default): return getattr(args,name.replace('-','_')) or str(out/default)
    cfg=build_default_local_console_review_config(repo_root=args.repo_root,output_dir=args.output_dir,drilldown_dir=args.drilldown_dir,grouping_dir=args.grouping_dir,refresh_dir=args.refresh_dir,preview_dir=args.preview_dir,binding_dir=args.binding_dir)
    r=run_local_console_review_workbench_review(cfg)
    save_local_console_review_workbench_report(r,val('output','local_console_review_workbench_report.md'),val('json-output','local_console_review_workbench_report.json'))
    save_review_manifest_report(build_review_manifest_report(r),val('manifest-output','review_manifest.md'),val('manifest-json-output','review_manifest.json'))
    save_review_checklist_report(build_review_checklist_report(r),val('checklist-output','review_checklist.md'),val('checklist-json-output','review_checklist.json'))
    save_review_notes_template_report(build_review_notes_template_report(r),val('notes-output','review_notes_template.md'),val('notes-json-output','review_notes_template.json'))
    save_local_confirmation_checklist_report(build_local_confirmation_checklist_report(r),val('confirmation-output','local_confirmation_checklist.md'),val('confirmation-json-output','local_confirmation_checklist.json'))
    save_review_package_index_report(build_review_package_index_report(r),val('package-output','review_package_index.md'),val('package-json-output','review_package_index.json'))
    save_review_safety_report(build_review_safety_report_from_report(r),val('safety-output','review_safety_report.md'),val('safety-json-output','review_safety_report.json'))
    save_next_ui_acceptance_summary_plan_report(build_next_ui_acceptance_summary_plan_report(cfg),val('plan-output','next_ui_acceptance_summary_plan.md'),val('plan-json-output','next_ui_acceptance_summary_plan.json'))
    print(f'Stage71 Local Console Review Workbench decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if r.decision==LocalConsoleReviewDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
