from __future__ import annotations
import json, subprocess, sys
import pytest
from pathlib import Path
from qmt_ai_trading.live_consistency.models import *
from qmt_ai_trading.live_consistency.service import *
from qmt_ai_trading.live_consistency.formatters import format_live_consistency_report_markdown
from qmt_ai_trading.live_consistency.safety import classify_consistency_marker, scan_consistency_text_for_forbidden_markers

def _write(p:Path,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8')
def test_config_and_report_defaults(): assert LiveConsistencyConfig().read_only and LiveConsistencyReport().decision
def test_missing_stage48_no_crash(tmp_path):
    r=run_live_consistency(build_default_live_consistency_config(repo_root=tmp_path)); assert r.decision in {LiveConsistencyDecision.NEED_MORE_EVIDENCE,LiveConsistencyDecision.NO_GO}
def test_stage48_need_more_evidence_not_no_go(tmp_path):
    _write(tmp_path/'live_archive_stage48/live_archive.json',{'decision':'NEED_MORE_EVIDENCE','summary':{'critical':0}})
    r=run_live_consistency(build_default_live_consistency_config(repo_root=tmp_path)); assert r.decision==LiveConsistencyDecision.NEED_MORE_EVIDENCE
def test_stage48_no_go_or_critical_is_no_go(tmp_path):
    _write(tmp_path/'live_archive_stage48/live_archive.json',{'decision':'READY_FOR_ARCHIVE_REVIEW','summary':{'critical':1}})
    assert run_live_consistency(build_default_live_consistency_config(repo_root=tmp_path)).decision==LiveConsistencyDecision.NO_GO
@pytest.mark.parametrize('stage,path', [('NO_GO','live_runbook_stage45/live_runbook.json'),('NO_GO','live_signoff_stage46/live_signoff.json'),('NO_GO','live_final_review_stage47/live_final_review.json'),('NO_GO','live_archive_stage48/live_archive.json')])
def test_stage45_46_47_48_no_go_is_no_go(tmp_path,stage,path):
    _write(tmp_path/path,{'decision':stage,'summary':{'critical':0}}); assert run_live_consistency(build_default_live_consistency_config(repo_root=tmp_path)).decision==LiveConsistencyDecision.NO_GO
def test_marker_classification_warn_and_critical():
    assert classify_consistency_marker('xttrader','forbidden marker definition','docs/stage49.md')==LiveConsistencySeverity.WARN
    assert classify_consistency_marker('xttrader','actual executable live call','qmt_ai_trading/gateway/order.py')==LiveConsistencySeverity.CRITICAL
    assert scan_consistency_text_for_forbidden_markers('place_order query_stock_asset',context='actual executable live',path='executor.py')[0]['severity']=='CRITICAL'
def test_formatter_safety_note(tmp_path):
    md=format_live_consistency_report_markdown(run_live_consistency(build_default_live_consistency_config(repo_root=tmp_path)))
    assert '## Safety Note' in md and 'READY_FOR_CONSISTENCY_REVIEW' in md and '不是实盘授权' in md
def test_cli_generates_all_outputs(tmp_path):
    out=tmp_path/'out'; cmd=[sys.executable,'scripts/run_live_consistency.py','--repo-root',str(tmp_path),'--output-dir',str(out)]
    res=subprocess.run(cmd,cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True)
    assert res.returncode==0
    for n in ['live_consistency.md','live_consistency.json','material_consistency.md','material_consistency.json','human_recheck.md','human_recheck.json','next_gray_check_plan.md','next_gray_check_plan.json']: assert (out/n).exists()
def test_register_preview_contains_consistency():
    res=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-live-consistency','--live-consistency-output-dir','live_consistency','--time','15:30'],cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True)
    assert res.returncode==0 and 'Stage49 Live Consistency' in res.stdout and 'no_task_registered=True' in res.stdout
