from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_signoff.models import LiveSignoffConfig, LiveSignoffReport, LiveSignoffDecision as D, LiveSignoffSeverity as Sev
from qmt_ai_trading.live_signoff.service import build_default_live_signoff_config, run_live_signoff
from qmt_ai_trading.live_signoff.formatters import format_live_signoff_report_markdown
from qmt_ai_trading.live_signoff.safety import classify_signoff_marker
ROOT=Path(__file__).resolve().parents[1]

def seed_gi(root): (root/'.gitignore').write_text('validation_logs/\nlive_signoff_stage46/\nlive_signoff/\nmarket_data_test_stage46/\n',encoding='utf-8')
def write_json(path, data): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data),encoding='utf-8')
def seed_stage45(root, decision='READY_FOR_RUNBOOK_REVIEW', critical=0):
    rb=root/'live_runbook_stage45'; rb.mkdir(exist_ok=True)
    write_json(rb/'live_runbook.json',{'decision':decision,'summary':{'critical':critical}})
    for n in ['live_runbook.md','manual_rehearsal.md','incident_playbook.md']: (rb/n).write_text('## Safety Note\n不是实盘授权',encoding='utf-8')
    for n in ['manual_rehearsal.json','incident_playbook.json']: write_json(rb/n,{'decision':decision,'summary':{'critical':0}})

def test_config_and_report_defaults(): assert LiveSignoffConfig() and LiveSignoffReport()
def test_missing_stage45_no_crash(tmp_path): seed_gi(tmp_path); assert run_live_signoff(build_default_live_signoff_config(repo_root=tmp_path)).decision in {D.NEED_MORE_EVIDENCE,D.NO_GO}
def test_stage45_need_more_evidence_not_no_go(tmp_path): seed_gi(tmp_path); seed_stage45(tmp_path,'NEED_MORE_EVIDENCE',0); assert run_live_signoff(build_default_live_signoff_config(repo_root=tmp_path)).decision == D.NEED_MORE_EVIDENCE
def test_stage45_no_go_or_critical_blocks(tmp_path): seed_gi(tmp_path); seed_stage45(tmp_path,'NO_GO',0); assert run_live_signoff(build_default_live_signoff_config(repo_root=tmp_path)).decision == D.NO_GO; seed_stage45(tmp_path,'READY_FOR_RUNBOOK_REVIEW',1); assert run_live_signoff(build_default_live_signoff_config(repo_root=tmp_path)).decision == D.NO_GO
def test_stage42_43_44_no_go_blocks(tmp_path):
    seed_gi(tmp_path); seed_stage45(tmp_path)
    for d,f in [('live_gray_review_stage42','live_gray_review.json'),('live_signature_freeze_stage43','live_signature_freeze.json'),('live_env_snapshot_stage44','live_env_snapshot.json')]:
        write_json(tmp_path/d/f,{'decision':'NO_GO','summary':{'critical':0}}); assert run_live_signoff(build_default_live_signoff_config(repo_root=tmp_path)).decision==D.NO_GO; (tmp_path/d/f).unlink()
def test_marker_classification():
    assert classify_signoff_marker('docs/stage46.md','xttrader','forbidden marker definitions') == Sev.WARN
    assert classify_signoff_marker('qmt_ai_trading/live_execute/order.py','place_order','query_stock_asset') == Sev.CRITICAL
def test_formatter_safety_note():
    md=format_live_signoff_report_markdown(LiveSignoffReport(decision=D.READY_FOR_SIGNOFF_REVIEW))
    assert '## Safety Note' in md and 'READY_FOR_SIGNOFF_REVIEW 只表示签字封版材料可供人工复核' in md and '不是实盘授权' in md
def test_cli_outputs(tmp_path):
    seed_gi(tmp_path); seed_stage45(tmp_path,'NEED_MORE_EVIDENCE',0); out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_live_signoff.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'live_signoff.md'),'--json-output',str(out/'live_signoff.json'),'--manual-output',str(out/'manual_signoff.md'),'--manual-json-output',str(out/'manual_signoff.json'),'--incident-output',str(out/'incident_rehearsal.md'),'--incident-json-output',str(out/'incident_rehearsal.json')]
    res=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); assert res.returncode==0, res.stderr+res.stdout
    for n in ['live_signoff.md','live_signoff.json','manual_signoff.md','manual_signoff.json','incident_rehearsal.md','incident_rehearsal.json']: assert (out/n).exists()
def test_daily_and_scheduled_and_register_signoff(tmp_path):
    cache=tmp_path/'cache'; subprocess.run([sys.executable,'scripts/warmup_etf_universe.py','--lookback-days','40','--frequency','1d','--provider','mock','--cache-root',str(cache)],cwd=ROOT,check=True)
    out=tmp_path/'signoff'
    r=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(cache),'--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-signoff','--live-signoff-output-dir',str(out)],cwd=ROOT,text=True,capture_output=True); assert r.returncode==0, r.stderr+ r.stdout; assert (out/'live_signoff.md').exists()
    out2=tmp_path/'signoff2'
    r=subprocess.run([sys.executable,'scripts/run_scheduled_daily_pipeline.py','--warmup-universe','--warmup-provider','mock','--universe-lookback-days','40','--warmup-frequency','1d','--cache-root',str(cache),'--data-source-mode','cached_real_first','--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-signoff','--live-signoff-output-dir',str(out2)],cwd=ROOT,text=True,capture_output=True); assert r.returncode==0, r.stderr+r.stdout; assert (out2/'live_signoff.md').exists()
    r=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-live-signoff','--live-signoff-output-dir','live_signoff','--time','15:30'],cwd=ROOT,text=True,capture_output=True); assert r.returncode==0; assert '--enable-live-signoff' in r.stdout and 'read_only=True' in r.stdout and 'dry_run_only=True' in r.stdout and 'no_task_registered=True' in r.stdout
def test_gitignore_sync_all_and_stage45_dedup():
    gi=(ROOT/'.gitignore').read_text(encoding='utf-8')
    for x in ['validation_logs/','live_signoff_stage46/','live_signoff/','market_data_test_stage46/']: assert x in gi
    assert subprocess.run(['git','ls-files','validation_logs'],cwd=ROOT,text=True,capture_output=True).stdout.strip()==''
    assert subprocess.run(['git','diff','--','scripts/sync_all.ps1'],cwd=ROOT,text=True,capture_output=True).stdout==''
    from qmt_ai_trading.live_runbook.formatters import format_manual_rehearsal_markdown
    from qmt_ai_trading.live_runbook.models import ManualRehearsalReport
    assert format_manual_rehearsal_markdown(ManualRehearsalReport()).count('READY_FOR_RUNBOOK_REVIEW') == 1
