from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_archive.models import LiveArchiveConfig, LiveArchiveReport, LiveArchiveDecision as D, LiveArchiveSeverity as Sev
from qmt_ai_trading.live_archive.service import build_default_live_archive_config, run_live_archive
from qmt_ai_trading.live_archive.formatters import format_live_archive_report_markdown
from qmt_ai_trading.live_archive.safety import classify_archive_marker
ROOT=Path(__file__).resolve().parents[1]
def wj(path,data): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data),encoding='utf-8')
def seed_gi(root): root.mkdir(parents=True,exist_ok=True); (root/'.gitignore').write_text('validation_logs/\nlive_archive_stage48/\nlive_archive/\nmarket_data_test_stage48/\nmarket_data/\nreports/\nlogs/\n',encoding='utf-8')
def seed(root, decision='READY_FOR_FINAL_REVIEW', critical=0, stage='all'):
    seed_gi(root)
    vals=[('live_env_snapshot_stage44','live_env_snapshot.json','READY_FOR_ENV_SNAPSHOT_REVIEW'),('live_runbook_stage45','live_runbook.json','READY_FOR_RUNBOOK_REVIEW'),('live_signoff_stage46','live_signoff.json','READY_FOR_SIGNOFF_REVIEW'),('live_final_review_stage47','live_final_review.json',decision)]
    for d,f,ok in vals: wj(root/d/f, {'decision':decision if d=='live_final_review_stage47' else ok, 'summary':{'critical':critical if (stage in {'all',d} or d=='live_final_review_stage47') else 0}})
    fr=root/'live_final_review_stage47'
    for n in ['live_final_review.md','signature_verification.md','evidence_gap_report.md','next_readonly_plan.md']: (fr/n).write_text('不是实盘授权',encoding='utf-8')
    for n in ['signature_verification.json','evidence_gap_report.json','next_readonly_plan.json']: wj(fr/n,{'decision':decision,'summary':{'critical':0}})
def test_defaults(): assert LiveArchiveConfig() and LiveArchiveReport()
def test_missing_stage47_no_crash(tmp_path): seed_gi(tmp_path); assert run_live_archive(build_default_live_archive_config(repo_root=tmp_path)).decision in {D.NEED_MORE_EVIDENCE,D.NO_GO}
def test_stage47_need_more_evidence_not_no_go(tmp_path): seed(tmp_path, decision='NEED_MORE_EVIDENCE', critical=0); assert run_live_archive(build_default_live_archive_config(repo_root=tmp_path)).decision==D.NEED_MORE_EVIDENCE
def test_stage47_no_go_or_critical_blocks(tmp_path): seed(tmp_path, decision='NO_GO'); assert run_live_archive(build_default_live_archive_config(repo_root=tmp_path)).decision==D.NO_GO; seed(tmp_path, decision='READY_FOR_FINAL_REVIEW', critical=1); assert run_live_archive(build_default_live_archive_config(repo_root=tmp_path)).decision==D.NO_GO
def test_stage44_45_46_47_no_go_or_critical_blocks(tmp_path):
    for d,f in [('live_env_snapshot_stage44','live_env_snapshot.json'),('live_runbook_stage45','live_runbook.json'),('live_signoff_stage46','live_signoff.json'),('live_final_review_stage47','live_final_review.json')]:
        root=tmp_path/d; seed(root); wj(root/d/f,{'decision':'NO_GO','summary':{'critical':0}}); assert run_live_archive(build_default_live_archive_config(repo_root=root)).decision==D.NO_GO
        root=tmp_path/(d+'crit'); seed(root); wj(root/d/f,{'decision':'READY','summary':{'critical':1}}); assert run_live_archive(build_default_live_archive_config(repo_root=root)).decision==D.NO_GO
def test_marker_classification(): assert classify_archive_marker('docs/stage48.md','xttrader','forbidden marker definitions')==Sev.WARN; assert classify_archive_marker('qmt_ai_trading/live_execute/order.py','place_order','query_stock_asset')==Sev.CRITICAL
def test_formatter_safety_note():
    md=format_live_archive_report_markdown(LiveArchiveReport(decision=D.READY_FOR_ARCHIVE_REVIEW))
    assert '## Safety Note' in md and 'READY_FOR_ARCHIVE_REVIEW 只表示最终只读归档材料可供人工复核' in md and '不是实盘授权' in md
def test_cli_outputs(tmp_path):
    seed(tmp_path, decision='NEED_MORE_EVIDENCE'); out=tmp_path/'out'; cmd=[sys.executable,'scripts/run_live_archive.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'live_archive.md'),'--json-output',str(out/'live_archive.json'),'--remediation-output',str(out/'evidence_remediation_plan.md'),'--remediation-json-output',str(out/'evidence_remediation_plan.json'),'--human-output',str(out/'human_verification_summary.md'),'--human-json-output',str(out/'human_verification_summary.json'),'--plan-output',str(out/'next_readonly_check_plan.md'),'--plan-json-output',str(out/'next_readonly_check_plan.json')]
    r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); assert r.returncode==0, r.stderr+r.stdout
    for n in ['live_archive.md','live_archive.json','evidence_remediation_plan.md','evidence_remediation_plan.json','human_verification_summary.md','human_verification_summary.json','next_readonly_check_plan.md','next_readonly_check_plan.json']: assert (out/n).exists()
def test_daily_scheduled_register(tmp_path):
    cache=tmp_path/'cache'; subprocess.run([sys.executable,'scripts/warmup_etf_universe.py','--lookback-days','40','--frequency','1d','--provider','mock','--cache-root',str(cache)],cwd=ROOT,check=True)
    out=tmp_path/'ar'; r=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(cache),'--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-archive','--live-archive-output-dir',str(out)],cwd=ROOT,text=True,capture_output=True); assert r.returncode==0, r.stderr+r.stdout; assert (out/'live_archive.md').exists()
    out2=tmp_path/'ar2'; r=subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--warmup-universe','--warmup-provider','mock','--universe-lookback-days','40','--warmup-frequency','1d','--cache-root',str(cache),'--data-source-mode','cached_real_first','--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-archive','--live-archive-output-dir',str(out2)],cwd=ROOT,text=True,capture_output=True); assert r.returncode==0, r.stderr+r.stdout; assert (out2/'live_archive.md').exists()
    r=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-live-archive','--live-archive-output-dir','live_archive','--time','15:30'],cwd=ROOT,text=True,capture_output=True); assert r.returncode==0; assert '--enable-live-archive' in r.stdout and 'read_only=True' in r.stdout and 'dry_run_only=True' in r.stdout and 'no_task_registered=True' in r.stdout
def test_gitignore_sync_all_stage47_readability():
    gi=(ROOT/'.gitignore').read_text(encoding='utf-8')
    for x in ['validation_logs/','live_archive_stage48/','live_archive/','market_data_test_stage48/']: assert x in gi
    assert subprocess.run(['git','ls-files','validation_logs'],cwd=ROOT,text=True,capture_output=True).stdout.strip()==''
    assert subprocess.run(['git','diff','--','scripts/sync_all.ps1'],cwd=ROOT,text=True,capture_output=True).stdout==''
    from qmt_ai_trading.live_final_review.service import run_live_final_review
    r=run_live_final_review(); summaries={i.summary for i in r.go_no_go_summary}; assert len(summaries)>1
