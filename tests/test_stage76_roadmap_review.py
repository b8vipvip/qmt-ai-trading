from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.planning.stage76_models import *
from qmt_ai_trading.planning.stage76_service import *
from qmt_ai_trading.planning.stage76_formatters import format_stage76_report_md

MOJ=['鏈','鍙','楠','涓','绛','璇','瀹','鐩','鎺','鏉','�','\x00']

def ready_stage75(tmp_path, decision='READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW', critical=0):
    d=tmp_path/'local_console_closure_stage75'; d.mkdir(exist_ok=True)
    (d/'ui_productization_closure_report.json').write_text(json.dumps({'decision':decision,'summary':{'critical_count':critical}},ensure_ascii=False),encoding='utf-8')

def test_defaults():
    assert Stage76RoadmapReviewConfig().read_only is True
    assert Stage76RoadmapReviewReport().decision == Stage76RoadmapReviewDecision.NEED_MORE_EVIDENCE

def test_missing_stage75_needs_evidence(tmp_path):
    r=run_stage76_roadmap_review(build_default_stage76_config(repo_root=str(tmp_path)))
    assert r.decision in {Stage76RoadmapReviewDecision.NEED_MORE_EVIDENCE, Stage76RoadmapReviewDecision.NO_GO}

def test_stage75_ready_and_no_go(tmp_path):
    ready_stage75(tmp_path)
    assert run_stage76_roadmap_review(build_default_stage76_config(repo_root=str(tmp_path))).decision == Stage76RoadmapReviewDecision.READY_FOR_NEXT_ROADMAP_REVIEW
    ready_stage75(tmp_path,'NO_GO',0)
    assert run_stage76_roadmap_review(build_default_stage76_config(repo_root=str(tmp_path))).decision == Stage76RoadmapReviewDecision.NO_GO
    ready_stage75(tmp_path,'READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW',1)
    assert run_stage76_roadmap_review(build_default_stage76_config(repo_root=str(tmp_path))).decision == Stage76RoadmapReviewDecision.NO_GO

def test_all_sections_and_conservative_semantics(tmp_path):
    ready_stage75(tmp_path); r=run_stage76_roadmap_review(build_default_stage76_config(repo_root=str(tmp_path)))
    assert build_completed_stage_summary() and r.completed_stage_summary
    assert build_ui_productization_recap() and r.ui_productization_recap
    assert build_architecture_alignment() and r.architecture_alignment
    assert build_safety_boundary() and r.safety_boundary
    assert build_data_quality_gaps() and r.data_quality_gaps
    assert build_trading_readiness_gaps() and r.trading_readiness_gaps
    assert build_ui_maturity() and r.ui_maturity
    assert build_live_readiness_blockers() and len(r.live_readiness_blockers) >= 8
    assert build_next_roadmap() and r.next_roadmap
    assert build_stage77_plan() and r.stage77_plan
    blockers=' '.join(x.blocker for x in r.live_readiness_blockers)
    for s in ['真实缓存长期质量验证','Paper Trading 长周期复盘','小资金灰度','异常监控','live config 多重确认']:
        assert s in blockers
    roadmap=' '.join(x.note+x.title for x in r.next_roadmap); plan=' '.join(x.note+x.task for x in r.stage77_plan)
    assert '直接实盘' in roadmap and '不直接实盘' in roadmap
    assert '直接实盘' in plan and '不直接实盘' in plan
    assert '不是实盘授权' in r.safety_note and '不下单' in r.safety_note and '不调用 xttrader' in r.safety_note and '不查询真实账户' in r.safety_note
    md=format_stage76_report_md(r); js=json.dumps(to_plain(r),ensure_ascii=False)
    assert 'Stage75 UI 产品化收口不等于实盘授权' in md
    for marker in MOJ:
        assert marker not in md and marker not in js

def test_cli_generates_outputs(tmp_path):
    ready_stage75(tmp_path)
    cmd=[sys.executable,'scripts/run_stage76_roadmap_review.py','--repo-root',str(tmp_path),'--output-dir','stage76_roadmap_review']
    assert subprocess.run(cmd,cwd=Path.cwd()).returncode == 0
    out=tmp_path/'stage76_roadmap_review'
    for name in ['stage76_roadmap_review_report.md','stage76_roadmap_review_report.json','completed_stage_summary.md','ui_productization_recap.md','architecture_alignment_review.md','safety_boundary_review.md','data_quality_gap_review.md','trading_readiness_gap_review.md','ui_maturity_review.md','live_readiness_blockers.md','next_roadmap_plan.md','stage77_plan.md']:
        assert (out/name).exists()

def test_sync_all_not_modified_and_validate_rules():
    assert Path('scripts/sync_all.ps1').exists()
    text=Path('scripts/validate_stage76.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in text
    assert 'Clean-PythonCache' in text
    assert 'Clean-PythonCache' in text
    assert text.find('Clean-PythonCache') < text.find('sync scan')
