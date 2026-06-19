from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_archive_verification.models import *
from qmt_ai_trading.live_archive_verification.service import build_default_live_archive_verification_config, run_live_archive_verification
from qmt_ai_trading.live_archive_verification.formatters import format_live_archive_verification_report_markdown
from qmt_ai_trading.live_archive_verification.safety import classify_archive_verification_marker, scan_archive_verification_text_for_forbidden_markers

ROADMAP_TEXT='''完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）
Stage61：API Gateway 基础层
Stage75：本地控制台封版 / 可选桌面化
UI 不直接访问 QMT
UI 不能绕过 Risk Gate
UI 不能绕过 Human Approval
UI 不能自动 approve
'''

def _write(root: Path, rel: str, decision: str, critical: int = 0):
    p=root/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({'decision':decision,'summary':{'critical':critical}}, ensure_ascii=False), encoding='utf-8')

def _base(root: Path, stage52='READY_FOR_LOCK_CONSISTENCY_REVIEW', crit=0):
    (root/'docs').mkdir(); (root/'docs/qmt-ai-trading-project-roadmap.md').write_text(ROADMAP_TEXT, encoding='utf-8')
    (root/'.gitignore').write_text('validation_logs/\nlive_archive_verification_stage53/\nlive_archive_verification/\nmarket_data_test_stage53/\n', encoding='utf-8')
    _write(root,'live_lock_consistency_stage52/live_lock_consistency.json',stage52,crit)
    _write(root,'live_archive_lock_stage51/live_archive_lock.json','READY_FOR_LOCK_REVIEW',0)
    _write(root,'live_final_archive_stage50/live_final_archive.json','READY_FOR_FINAL_ARCHIVE_REVIEW',0)
    _write(root,'live_consistency_stage49/live_consistency.json','READY_FOR_CONSISTENCY_REVIEW',0)

def test_config_and_report_default_constructible():
    assert LiveArchiveVerificationConfig().read_only is True
    assert LiveArchiveVerificationReport().decision == LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE

def test_missing_stage52_does_not_crash(tmp_path):
    (tmp_path/'docs').mkdir(); (tmp_path/'docs/qmt-ai-trading-project-roadmap.md').write_text(ROADMAP_TEXT, encoding='utf-8')
    r=run_live_archive_verification(build_default_live_archive_verification_config(repo_root=tmp_path))
    assert r.decision in {LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE, LiveArchiveVerificationDecision.NO_GO}

def test_stage52_ready_maps_to_archive_review(tmp_path):
    _base(tmp_path)
    r=run_live_archive_verification(build_default_live_archive_verification_config(repo_root=tmp_path))
    assert r.decision == LiveArchiveVerificationDecision.READY_FOR_ARCHIVE_VERIFICATION_REVIEW

def test_stage52_need_more_evidence_stays_need_more_evidence(tmp_path):
    _base(tmp_path, 'NEED_MORE_EVIDENCE', 0)
    r=run_live_archive_verification(build_default_live_archive_verification_config(repo_root=tmp_path))
    assert r.decision == LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE

def test_stage52_no_go_or_critical_is_no_go(tmp_path):
    _base(tmp_path, 'NO_GO', 0)
    assert run_live_archive_verification(build_default_live_archive_verification_config(repo_root=tmp_path)).decision == LiveArchiveVerificationDecision.NO_GO
    tmp2=tmp_path/'x'; tmp2.mkdir(); _base(tmp2, 'READY_FOR_LOCK_CONSISTENCY_REVIEW', 1)
    assert run_live_archive_verification(build_default_live_archive_verification_config(repo_root=tmp2)).decision == LiveArchiveVerificationDecision.NO_GO

def test_stage49_50_51_no_go_is_no_go(tmp_path):
    for rel in ['live_consistency_stage49/live_consistency.json','live_final_archive_stage50/live_final_archive.json','live_archive_lock_stage51/live_archive_lock.json']:
        root=tmp_path/rel.split('/')[0]; root.mkdir(parents=True, exist_ok=True); _base(root)
        _write(root, rel, 'NO_GO', 0)
        assert run_live_archive_verification(build_default_live_archive_verification_config(repo_root=root)).decision == LiveArchiveVerificationDecision.NO_GO

def test_marker_classification_warn_and_critical():
    assert classify_archive_verification_marker('xttrader','docs/safety marker definitions') == 'WARN'
    hits=scan_archive_verification_text_for_forbidden_markers('xttrader place_order query_stock_asset','src/live_executor.py')
    assert {h['severity'] for h in hits} == {'CRITICAL'}

def test_formatter_safety_note_and_not_authorization(tmp_path):
    _base(tmp_path)
    md=format_live_archive_verification_report_markdown(run_live_archive_verification(build_default_live_archive_verification_config(repo_root=tmp_path)))
    assert '## Safety Note' in md
    assert 'READY_FOR_ARCHIVE_VERIFICATION_REVIEW 只表示' in md
    assert '不是实盘授权' in md

def test_cli_generates_all_outputs(tmp_path):
    _base(tmp_path)
    out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_live_archive_verification.py','--repo-root',str(tmp_path),'--output-dir',str(out)]
    res=subprocess.run(cmd,cwd=Path.cwd(),text=True,capture_output=True)
    assert res.returncode == 0, res.stderr+res.stdout
    for name in ['live_archive_verification.md','live_archive_verification.json','locked_material_review.md','locked_material_review.json','human_closure_recheck.md','human_closure_recheck.json','next_readonly_check_plan.md','next_readonly_check_plan.json']:
        assert (out/name).exists()

def test_roadmap_contains_ui_plan_and_safety_redlines():
    text=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    for token in ['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve','UI 不直接访问 QMT']:
        assert token in text

def test_gitignore_and_sync_all_untouched_markers():
    gi=Path('.gitignore').read_text(encoding='utf-8')
    for token in ['validation_logs/','live_archive_verification_stage53/','live_archive_verification/','market_data_test_stage53/']:
        assert token in gi
    assert Path('scripts/sync_all.ps1').exists()
