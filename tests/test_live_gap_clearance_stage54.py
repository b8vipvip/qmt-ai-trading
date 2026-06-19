import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_gap_clearance.models import *
from qmt_ai_trading.live_gap_clearance.service import *
from qmt_ai_trading.live_gap_clearance.formatters import format_live_gap_clearance_report_markdown
from qmt_ai_trading.live_gap_clearance.safety import scan_gap_clearance_text_for_forbidden_markers


def write_json(p: Path, decision, critical=0):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({'decision': decision, 'summary': {'critical': critical}}, ensure_ascii=False), encoding='utf-8')

def seed(root: Path, stage53='READY_FOR_ARCHIVE_VERIFICATION_REVIEW', crit=0):
    write_json(root/'live_archive_verification_stage53/live_archive_verification.json', stage53, crit)
    for n in ['locked_material_review.json','human_closure_recheck.json','next_readonly_check_plan.json']:
        write_json(root/'live_archive_verification_stage53'/n, 'READY_FOR_ARCHIVE_VERIFICATION_REVIEW', 0)
    write_json(root/'live_lock_consistency_stage52/live_lock_consistency.json', 'READY_FOR_LOCK_CONSISTENCY_REVIEW', 0)
    write_json(root/'live_archive_lock_stage51/live_archive_lock.json', 'READY_FOR_ARCHIVE_LOCK_REVIEW', 0)
    write_json(root/'live_final_archive_stage50/live_final_archive.json', 'READY_FOR_FINAL_ARCHIVE_REVIEW', 0)
    (root/'docs').mkdir(exist_ok=True)
    (root/'docs/qmt-ai-trading-project-roadmap.md').write_text('完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）\nStage61：API Gateway 基础层\nStage75：本地控制台封版 / 可选桌面化\nUI 不直接访问 QMT\nUI 不能绕过 Risk Gate\nUI 不能绕过 Human Approval\nUI 不能自动 approve', encoding='utf-8')
    (root/'.gitignore').write_text('validation_logs/\nlive_gap_clearance_stage54/\nlive_gap_clearance/\nmarket_data_test_stage54/\n', encoding='utf-8')

def test_config_and_report_defaults():
    assert LiveGapClearanceConfig().read_only is True
    assert LiveGapClearanceReport().decision == LiveGapClearanceDecision.NEED_MORE_EVIDENCE

def test_missing_stage53_does_not_crash(tmp_path):
    r=run_live_gap_clearance(build_default_live_gap_clearance_config(repo_root=tmp_path))
    assert r.decision in {LiveGapClearanceDecision.NEED_MORE_EVIDENCE, LiveGapClearanceDecision.NO_GO}

def test_stage53_ready_maps_to_gap_review(tmp_path):
    seed(tmp_path)
    r=run_live_gap_clearance(build_default_live_gap_clearance_config(repo_root=tmp_path))
    assert r.decision == LiveGapClearanceDecision.READY_FOR_GAP_CLEARANCE_REVIEW

def test_stage53_need_more_evidence_stays_need_more(tmp_path):
    seed(tmp_path, 'NEED_MORE_EVIDENCE')
    assert run_live_gap_clearance(build_default_live_gap_clearance_config(repo_root=tmp_path)).decision == LiveGapClearanceDecision.NEED_MORE_EVIDENCE

def test_no_go_or_critical_blocks(tmp_path):
    seed(tmp_path, 'NO_GO')
    assert run_live_gap_clearance(build_default_live_gap_clearance_config(repo_root=tmp_path)).decision == LiveGapClearanceDecision.NO_GO
    seed(tmp_path, 'READY_FOR_ARCHIVE_VERIFICATION_REVIEW', 1)
    assert run_live_gap_clearance(build_default_live_gap_clearance_config(repo_root=tmp_path)).decision == LiveGapClearanceDecision.NO_GO

def test_stage50_51_52_no_go_blocks(tmp_path):
    seed(tmp_path)
    for path in ['live_final_archive_stage50/live_final_archive.json','live_archive_lock_stage51/live_archive_lock.json','live_lock_consistency_stage52/live_lock_consistency.json']:
        write_json(tmp_path/path, 'NO_GO', 0)
        assert run_live_gap_clearance(build_default_live_gap_clearance_config(repo_root=tmp_path)).decision == LiveGapClearanceDecision.NO_GO
        seed(tmp_path)

def test_forbidden_marker_classification():
    assert scan_gap_clearance_text_for_forbidden_markers('xttrader place_order query_stock_asset', 'docs/tests/safety marker definitions')[0]['severity']=='WARN'
    assert scan_gap_clearance_text_for_forbidden_markers('xttrader place_order query_stock_asset', 'actual executable live order code')[0]['severity']=='CRITICAL'

def test_formatter_safety_note():
    md=format_live_gap_clearance_report_markdown(LiveGapClearanceReport(decision=LiveGapClearanceDecision.READY_FOR_GAP_CLEARANCE_REVIEW))
    assert '## Safety Note' in md and 'READY_FOR_GAP_CLEARANCE_REVIEW 只表示' in md and '不是实盘授权' in md

def test_cli_generates_all_reports(tmp_path):
    seed(tmp_path)
    out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_live_gap_clearance.py','--repo-root',str(tmp_path),'--output-dir',str(out)]
    assert subprocess.run(cmd,cwd=Path.cwd(),capture_output=True,text=True).returncode==0
    for name in ['live_gap_clearance.md','live_gap_clearance.json','evidence_remediation.md','evidence_remediation.json','human_closure_recheck.md','human_closure_recheck.json','next_readonly_check_plan.md','next_readonly_check_plan.json']:
        assert (out/name).exists()

def test_repo_static_requirements():
    assert not list(Path('scripts').glob('validate_stage53.ps1.bak_*'))
    assert Path('scripts/sync_all.ps1').exists()
    gi=Path('.gitignore').read_text(encoding='utf-8')
    assert 'validation_logs/' in gi and 'live_gap_clearance_stage54/' in gi and 'market_data_test_stage54/' in gi
    txt=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    for key in ['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']:
        assert key in txt
    fmt=Path('qmt_ai_trading/live_archive_verification/formatters.py').read_text(encoding='utf-8')
    assert fmt.count('READY_FOR_ARCHIVE_VERIFICATION_REVIEW 只表示') <= 1
