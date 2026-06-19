from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_final_archive.models import *
from qmt_ai_trading.live_final_archive.service import *
from qmt_ai_trading.live_final_archive.formatters import format_live_final_archive_report_markdown
from qmt_ai_trading.live_final_archive.safety import classify_final_archive_marker, scan_final_archive_text_for_forbidden_markers
ROOT=Path(__file__).resolve().parents[1]
def _write(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8')
def _seed(root, s49='READY_FOR_CONSISTENCY_REVIEW', critical=0):
    _write(root/'live_consistency_stage49/live_consistency.json',{'decision':s49,'summary':{'critical':critical}})
    (root/'live_consistency_stage49/live_consistency.md').write_text('Stage49 ready',encoding='utf-8')
    for n in ['material_consistency','human_recheck','next_gray_check_plan']:
        _write(root/f'live_consistency_stage49/{n}.json',{'decision':s49,'summary':{'critical':0}}); (root/f'live_consistency_stage49/{n}.md').write_text(n,encoding='utf-8')
    _write(root/'live_archive_stage48/live_archive.json',{'decision':'READY_FOR_ARCHIVE_REVIEW','summary':{'critical':0}})
    _write(root/'live_final_review_stage47/live_final_review.json',{'decision':'READY_FOR_FINAL_REVIEW','summary':{'critical':0}})
    _write(root/'live_signoff_stage46/live_signoff.json',{'decision':'READY_FOR_LIVE_SIGNOFF','summary':{'critical':0}})
    (root/'.gitignore').write_text('validation_logs/\nlive_final_archive_stage50/\nlive_final_archive/\nmarket_data_test_stage50/\n',encoding='utf-8')
    (root/'validation_logs').mkdir(exist_ok=True)
def test_config_and_report_defaults(): assert LiveFinalArchiveConfig().read_only and LiveFinalArchiveReport().decision==LiveFinalArchiveDecision.NEED_MORE_EVIDENCE
def test_missing_stage49_no_crash(tmp_path): assert run_live_final_archive(build_default_live_final_archive_config(repo_root=tmp_path)).decision in {LiveFinalArchiveDecision.NEED_MORE_EVIDENCE,LiveFinalArchiveDecision.NO_GO}
def test_ready_stage49_all_evidence_ready(tmp_path): _seed(tmp_path); assert run_live_final_archive(build_default_live_final_archive_config(repo_root=tmp_path)).decision==LiveFinalArchiveDecision.READY_FOR_FINAL_ARCHIVE_REVIEW
def test_stage49_need_more_evidence_not_no_go(tmp_path): _seed(tmp_path,'NEED_MORE_EVIDENCE'); assert run_live_final_archive(build_default_live_final_archive_config(repo_root=tmp_path)).decision==LiveFinalArchiveDecision.NEED_MORE_EVIDENCE
def test_stage49_no_go_or_critical_no_go(tmp_path): _seed(tmp_path,'NO_GO'); assert run_live_final_archive(build_default_live_final_archive_config(repo_root=tmp_path)).decision==LiveFinalArchiveDecision.NO_GO; tmp=tmp_path/'b'; _seed(tmp,'READY_FOR_CONSISTENCY_REVIEW',1); assert run_live_final_archive(build_default_live_final_archive_config(repo_root=tmp)).decision==LiveFinalArchiveDecision.NO_GO
def test_stage46_47_48_no_go_forces_no_go(tmp_path):
    for rel in ['live_signoff_stage46/live_signoff.json','live_final_review_stage47/live_final_review.json','live_archive_stage48/live_archive.json']:
        root=tmp_path/rel.split('/')[0]; _seed(root); _write(root/rel,{'decision':'NO_GO','summary':{'critical':0}}); assert run_live_final_archive(build_default_live_final_archive_config(repo_root=root)).decision==LiveFinalArchiveDecision.NO_GO
def test_safety_marker_classification():
    assert classify_final_archive_marker('xttrader',path='docs/stage50-final-archive-material-seal.md').value=='WARN'
    assert scan_final_archive_text_for_forbidden_markers('actual executable xttrader place_order query_stock_asset',context='actual executable live',path='gateway/order.py')[0]['severity']=='CRITICAL'
def test_formatter_safety_note(tmp_path): _seed(tmp_path); md=format_live_final_archive_report_markdown(run_live_final_archive(build_default_live_final_archive_config(repo_root=tmp_path))); assert '## Safety Note' in md and 'READY_FOR_FINAL_ARCHIVE_REVIEW' in md and '不是实盘授权' in md
def test_cli_generates_all_outputs(tmp_path):
    _seed(tmp_path); out=tmp_path/'out'; cmd=[sys.executable,'scripts/run_live_final_archive.py','--repo-root',str(tmp_path),'--output-dir',str(out)]
    res=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); assert res.returncode==0, res.stderr+res.stdout
    for n in ['live_final_archive.md','live_final_archive.json','material_seal.md','material_seal.json','human_closure.md','human_closure.json','next_readonly_check_plan.md','next_readonly_check_plan.json']: assert (out/n).exists()
def test_register_preview_contains_stage50():
    res=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-live-final-archive','--live-final-archive-output-dir','live_final_archive','--time','15:30'],cwd=ROOT,text=True,capture_output=True)
    assert res.returncode==0 and 'Stage50 Live Final Archive' in res.stdout and 'no_task_registered=True' in res.stdout
def test_gitignore_validation_logs_and_sync_all_unmodified():
    gi=(ROOT/'.gitignore').read_text(encoding='utf-8')
    for x in ['validation_logs/','live_final_archive_stage50/','live_final_archive/','market_data_test_stage50/']: assert x in gi
    assert subprocess.run(['git','ls-files','validation_logs'],cwd=ROOT,text=True,capture_output=True).stdout.strip()==''
    assert subprocess.run(['git','diff','--','scripts/sync_all.ps1'],cwd=ROOT,text=True,capture_output=True).stdout==''
def test_stage49_safety_note_deduplicated(tmp_path):
    from qmt_ai_trading.live_consistency.service import build_default_live_consistency_config, run_live_consistency
    from qmt_ai_trading.live_consistency.formatters import format_live_consistency_report_markdown
    md=format_live_consistency_report_markdown(run_live_consistency(build_default_live_consistency_config(repo_root=tmp_path)))
    assert md.count('READY_FOR_CONSISTENCY_REVIEW 只表示补证后只读复核与一致性材料可供人工复核')==1
