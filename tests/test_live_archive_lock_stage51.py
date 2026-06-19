from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_archive_lock.models import *
from qmt_ai_trading.live_archive_lock.service import *
from qmt_ai_trading.live_archive_lock.formatters import format_live_archive_lock_report_markdown
from qmt_ai_trading.live_archive_lock.safety import classify_archive_lock_marker, scan_archive_lock_text_for_forbidden_markers
ROOT=Path(__file__).resolve().parents[1]
def _write(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8')
def _seed(root, s50='READY_FOR_FINAL_ARCHIVE_REVIEW', critical=0):
    _write(root/'live_final_archive_stage50/live_final_archive.json',{'decision':s50,'summary':{'critical':critical}}); (root/'live_final_archive_stage50/live_final_archive.md').write_text('Stage50 ready',encoding='utf-8')
    for n in ['material_seal','human_closure','next_readonly_check_plan']:
        _write(root/f'live_final_archive_stage50/{n}.json',{'decision':s50,'summary':{'critical':0}}); (root/f'live_final_archive_stage50/{n}.md').write_text(n,encoding='utf-8')
    _write(root/'live_consistency_stage49/live_consistency.json',{'decision':'READY_FOR_CONSISTENCY_REVIEW','summary':{'critical':0}})
    _write(root/'live_archive_stage48/live_archive.json',{'decision':'READY_FOR_ARCHIVE_REVIEW','summary':{'critical':0}})
    _write(root/'live_final_review_stage47/live_final_review.json',{'decision':'READY_FOR_FINAL_REVIEW','summary':{'critical':0}})
    (root/'.gitignore').write_text('validation_logs/\nlive_archive_lock_stage51/\nlive_archive_lock/\nmarket_data_test_stage51/\n',encoding='utf-8'); (root/'validation_logs').mkdir(exist_ok=True)
def test_config_and_report_defaults(): assert LiveArchiveLockConfig().read_only and LiveArchiveLockReport().decision==LiveArchiveLockDecision.NEED_MORE_EVIDENCE
def test_missing_stage50_no_crash(tmp_path): assert run_live_archive_lock(build_default_live_archive_lock_config(repo_root=tmp_path)).decision in {LiveArchiveLockDecision.NEED_MORE_EVIDENCE,LiveArchiveLockDecision.NO_GO}
def test_ready_stage50_all_evidence_ready(tmp_path): _seed(tmp_path); assert run_live_archive_lock(build_default_live_archive_lock_config(repo_root=tmp_path)).decision==LiveArchiveLockDecision.READY_FOR_LOCK_REVIEW
def test_stage50_need_more_evidence_not_no_go(tmp_path): _seed(tmp_path,'NEED_MORE_EVIDENCE'); assert run_live_archive_lock(build_default_live_archive_lock_config(repo_root=tmp_path)).decision==LiveArchiveLockDecision.NEED_MORE_EVIDENCE
def test_stage50_no_go_or_critical_no_go(tmp_path): _seed(tmp_path,'NO_GO'); assert run_live_archive_lock(build_default_live_archive_lock_config(repo_root=tmp_path)).decision==LiveArchiveLockDecision.NO_GO; tmp=tmp_path/'b'; _seed(tmp,'READY_FOR_FINAL_ARCHIVE_REVIEW',1); assert run_live_archive_lock(build_default_live_archive_lock_config(repo_root=tmp)).decision==LiveArchiveLockDecision.NO_GO
def test_stage47_48_49_50_no_go_forces_no_go(tmp_path):
    for rel in ['live_final_review_stage47/live_final_review.json','live_archive_stage48/live_archive.json','live_consistency_stage49/live_consistency.json','live_final_archive_stage50/live_final_archive.json']:
        root=tmp_path/rel.split('/')[0]; _seed(root); _write(root/rel,{'decision':'NO_GO','summary':{'critical':0}}); assert run_live_archive_lock(build_default_live_archive_lock_config(repo_root=root)).decision==LiveArchiveLockDecision.NO_GO
def test_safety_marker_classification():
    assert classify_archive_lock_marker('xttrader',path='docs/stage51-final-readonly-seal-archive-lock.md').value=='WARN'
    assert scan_archive_lock_text_for_forbidden_markers('actual executable xttrader place_order query_stock_asset',context='actual executable live',path='gateway/order.py')[0]['severity']=='CRITICAL'
def test_formatter_safety_note(tmp_path): _seed(tmp_path); md=format_live_archive_lock_report_markdown(run_live_archive_lock(build_default_live_archive_lock_config(repo_root=tmp_path))); assert '## Safety Note' in md and 'READY_FOR_LOCK_REVIEW' in md and '不是实盘授权' in md
def test_cli_generates_all_outputs(tmp_path):
    _seed(tmp_path); out=tmp_path/'out'; res=subprocess.run([sys.executable,'scripts/run_live_archive_lock.py','--repo-root',str(tmp_path),'--output-dir',str(out)],cwd=ROOT,text=True,capture_output=True); assert res.returncode==0, res.stderr+res.stdout
    for n in ['live_archive_lock.md','live_archive_lock.json','archive_lock.md','archive_lock.json','human_closure_recheck.md','human_closure_recheck.json','next_readonly_check_plan.md','next_readonly_check_plan.json']: assert (out/n).exists()
def test_daily_and_scheduled_and_register_stage51(tmp_path):
    # Use existing repository evidence without mutating repository .gitignore.
    out=tmp_path/'daily_lock'; cmd=[sys.executable,'scripts/run_daily_pipeline.py','--cache-root',str(tmp_path/'cache'),'--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-archive-lock','--live-archive-lock-output-dir',str(out)]
    res=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); assert res.returncode in {0,1}; assert (out/'archive_lock.md').exists()
    out2=tmp_path/'scheduled_lock'; cmd=[sys.executable,'scripts/run_scheduled_daily_pipeline.py','--cache-root',str(tmp_path/'cache'),'--data-source-mode','cached_real_first','--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-archive-lock','--live-archive-lock-output-dir',str(out2)]
    res=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); assert res.returncode in {0,1}; assert (out2/'archive_lock.md').exists()
    res=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-live-archive-lock','--live-archive-lock-output-dir','live_archive_lock','--time','15:30'],cwd=ROOT,text=True,capture_output=True)
    assert res.returncode==0 and 'Stage51 Live Archive Lock' in res.stdout and 'no_task_registered=True' in res.stdout and '--enable-live-archive-lock' in res.stdout
def test_gitignore_validation_logs_and_sync_all_unmodified_and_stage50_dedup():
    gi=(ROOT/'.gitignore').read_text(encoding='utf-8')
    for x in ['validation_logs/','live_archive_lock_stage51/','live_archive_lock/','market_data_test_stage51/']: assert x in gi
    assert subprocess.run(['git','ls-files','validation_logs'],cwd=ROOT,text=True,capture_output=True).stdout.strip()==''
    assert subprocess.run(['git','diff','--','scripts/sync_all.ps1'],cwd=ROOT,text=True,capture_output=True).stdout==''
    from qmt_ai_trading.live_final_archive.service import build_default_live_final_archive_config, run_live_final_archive
    from qmt_ai_trading.live_final_archive.formatters import format_live_final_archive_report_markdown
    md=format_live_final_archive_report_markdown(run_live_final_archive(build_default_live_final_archive_config(repo_root=ROOT)))
    assert md.count('READY_FOR_FINAL_ARCHIVE_REVIEW 只表示最终归档复核与材料一致性封版材料可供人工复核')==1
