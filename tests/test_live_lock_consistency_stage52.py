from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_lock_consistency.models import *
from qmt_ai_trading.live_lock_consistency.service import *
from qmt_ai_trading.live_lock_consistency.formatters import format_live_lock_consistency_report_markdown
from qmt_ai_trading.live_lock_consistency.safety import classify_lock_consistency_marker, scan_lock_consistency_text_for_forbidden_markers
ROOT=Path(__file__).resolve().parents[1]
def _write(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8')
def _seed(root, s51='READY_FOR_LOCK_REVIEW', critical=0):
    for n in ['live_archive_lock','archive_lock','human_closure_recheck','next_readonly_check_plan']:
        _write(root/f'live_archive_lock_stage51/{n}.json',{'decision':s51,'summary':{'critical':critical if n=='live_archive_lock' else 0}}); (root/f'live_archive_lock_stage51/{n}.md').write_text(n,encoding='utf-8')
    _write(root/'live_final_archive_stage50/live_final_archive.json',{'decision':'READY_FOR_FINAL_ARCHIVE_REVIEW','summary':{'critical':0}})
    _write(root/'live_consistency_stage49/live_consistency.json',{'decision':'READY_FOR_CONSISTENCY_REVIEW','summary':{'critical':0}})
    _write(root/'live_archive_stage48/live_archive.json',{'decision':'READY_FOR_ARCHIVE_REVIEW','summary':{'critical':0}})
    (root/'.gitignore').write_text('validation_logs/\nlive_lock_consistency_stage52/\nlive_lock_consistency/\nmarket_data_test_stage52/\n',encoding='utf-8'); (root/'validation_logs').mkdir(exist_ok=True)
def test_config_and_report_defaults(): assert LiveLockConsistencyConfig().read_only and LiveLockConsistencyReport().decision==LiveLockConsistencyDecision.NEED_MORE_EVIDENCE
def test_missing_stage51_no_crash(tmp_path): assert run_live_lock_consistency(build_default_live_lock_consistency_config(repo_root=tmp_path)).decision in {LiveLockConsistencyDecision.NEED_MORE_EVIDENCE,LiveLockConsistencyDecision.NO_GO}
def test_ready_stage51_all_evidence_ready(tmp_path): _seed(tmp_path); assert run_live_lock_consistency(build_default_live_lock_consistency_config(repo_root=tmp_path)).decision==LiveLockConsistencyDecision.READY_FOR_LOCK_CONSISTENCY_REVIEW
def test_stage51_need_more_evidence_not_no_go(tmp_path): _seed(tmp_path,'NEED_MORE_EVIDENCE'); assert run_live_lock_consistency(build_default_live_lock_consistency_config(repo_root=tmp_path)).decision==LiveLockConsistencyDecision.NEED_MORE_EVIDENCE
def test_stage51_no_go_or_critical_no_go(tmp_path): _seed(tmp_path,'NO_GO'); assert run_live_lock_consistency(build_default_live_lock_consistency_config(repo_root=tmp_path)).decision==LiveLockConsistencyDecision.NO_GO; tmp=tmp_path/'b'; _seed(tmp,'READY_FOR_LOCK_REVIEW',1); assert run_live_lock_consistency(build_default_live_lock_consistency_config(repo_root=tmp)).decision==LiveLockConsistencyDecision.NO_GO
def test_stage48_49_50_51_no_go_forces_no_go(tmp_path):
    for rel in ['live_archive_stage48/live_archive.json','live_consistency_stage49/live_consistency.json','live_final_archive_stage50/live_final_archive.json','live_archive_lock_stage51/live_archive_lock.json']:
        root=tmp_path/rel.split('/')[0]; _seed(root); _write(root/rel,{'decision':'NO_GO','summary':{'critical':0}}); assert run_live_lock_consistency(build_default_live_lock_consistency_config(repo_root=root)).decision==LiveLockConsistencyDecision.NO_GO
def test_safety_marker_classification():
    assert classify_lock_consistency_marker('xttrader',context='docs/stage52-final-readonly-lock-archive-consistency.md')=='WARN'
    assert scan_lock_consistency_text_for_forbidden_markers('actual executable xttrader place_order query_stock_asset',context='actual executable live')[0]['severity']=='CRITICAL'
def test_formatter_safety_note(tmp_path): _seed(tmp_path); md=format_live_lock_consistency_report_markdown(run_live_lock_consistency(build_default_live_lock_consistency_config(repo_root=tmp_path))); assert '## Safety Note' in md and 'READY_FOR_LOCK_CONSISTENCY_REVIEW' in md and '不是实盘授权' in md
def test_cli_generates_all_outputs(tmp_path):
    _seed(tmp_path); out=tmp_path/'out'; res=subprocess.run([sys.executable,'scripts/run_live_lock_consistency.py','--repo-root',str(tmp_path),'--output-dir',str(out)],cwd=ROOT,text=True,capture_output=True); assert res.returncode==0, res.stderr+res.stdout
    for n in ['live_lock_consistency.md','live_lock_consistency.json','archive_consistency.md','archive_consistency.json','human_closure_recheck.md','human_closure_recheck.json','next_readonly_check_plan.md','next_readonly_check_plan.json']: assert (out/n).exists()
def test_daily_and_scheduled_and_register_stage52(tmp_path):
    out=tmp_path/'daily_lock_consistency'; cmd=[sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'cache'),'--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-lock-consistency','--live-lock-consistency-output-dir',str(out)]
    res=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); assert res.returncode in {0,1}; assert (out/'archive_consistency.md').exists()
    out2=tmp_path/'scheduled_lock_consistency'; cmd=[sys.executable,'scripts/run_scheduled_daily_pipeline.py','--cache-root',str(tmp_path/'cache'),'--data-source-mode','cached_real_first','--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-lock-consistency','--live-lock-consistency-output-dir',str(out2)]
    res=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); assert res.returncode in {0,1}; assert (out2/'archive_consistency.md').exists()
    res=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-live-lock-consistency','--live-lock-consistency-output-dir','live_lock_consistency','--time','15:30'],cwd=ROOT,text=True,capture_output=True)
    assert res.returncode==0 and 'Stage52 Live Lock Consistency' in res.stdout and 'no_task_registered=True' in res.stdout and '--enable-live-lock-consistency' in res.stdout
def test_gitignore_validation_logs_and_sync_all_unmodified_and_stage51_dedup():
    gi=(ROOT/'.gitignore').read_text(encoding='utf-8')
    for x in ['validation_logs/','live_lock_consistency_stage52/','live_lock_consistency/','market_data_test_stage52/']: assert x in gi
    assert subprocess.run(['git','ls-files','validation_logs'],cwd=ROOT,text=True,capture_output=True).stdout.strip()==''
    assert subprocess.run(['git','diff','--','scripts/sync_all.ps1'],cwd=ROOT,text=True,capture_output=True).stdout==''
    from qmt_ai_trading.live_archive_lock.service import build_default_live_archive_lock_config, run_live_archive_lock
    from qmt_ai_trading.live_archive_lock.formatters import format_live_archive_lock_report_markdown
    md=format_live_archive_lock_report_markdown(run_live_archive_lock(build_default_live_archive_lock_config(repo_root=ROOT)))
    assert md.count('READY_FOR_LOCK_REVIEW 只表示最终只读封版复核与材料归档锁定材料可供人工复核')==1
