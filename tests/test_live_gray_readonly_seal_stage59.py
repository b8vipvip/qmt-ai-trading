import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_gray_readonly_seal.models import *
from qmt_ai_trading.live_gray_readonly_seal.service import *
from qmt_ai_trading.live_gray_readonly_seal.safety import scan_live_gray_readonly_seal_text_for_forbidden_markers

def write_json(p, decision, critical=0):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({'decision':decision,'summary':{'critical':critical}},ensure_ascii=False),encoding='utf-8')
def make_root(tmp_path, s58='READY_FOR_FINAL_APPROVAL_REVIEW', crit=0):
    (tmp_path/'docs').mkdir(parents=True, exist_ok=True); (tmp_path/'docs/qmt-ai-trading-project-roadmap.md').write_text('完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）\nStage61：API Gateway 基础层\nStage75：本地控制台封版 / 可选桌面化\nUI 不直接访问 QMT\nUI 不能绕过 Risk Gate\nUI 不能绕过 Human Approval\nUI 不能自动 approve',encoding='utf-8')
    write_json(tmp_path/'live_gray_final_approval_stage58/live_gray_final_approval.json',s58,crit)
    for n in ['capital_position_approval.json','risk_human_approval_review.json','rollback_circuit_approval.json','final_signoff_checklist.json','next_readonly_seal_plan.json']: write_json(tmp_path/'live_gray_final_approval_stage58'/n,'OK')
    (tmp_path/'live_gray_final_approval_stage58/live_gray_final_approval.md').write_text('不调用 xttrader',encoding='utf-8')
    write_json(tmp_path/'live_gray_candidate_stage57/live_gray_candidate.json','READY_FOR_GRAY_CANDIDATE_REVIEW')
    write_json(tmp_path/'real_cache_quality_stage56/real_cache_quality.json','READY_FOR_REAL_CACHE_QUALITY_REVIEW')
    write_json(tmp_path/'qmt_dryrun_calibration_stage55/qmt_dryrun_calibration.json','READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW')
    return tmp_path
def test_defaults():
    assert LiveGrayReadonlySealConfig(); assert LiveGrayReadonlySealReport()
def test_missing_stage58_no_crash(tmp_path):
    (tmp_path/'docs').mkdir(parents=True, exist_ok=True); (tmp_path/'docs/qmt-ai-trading-project-roadmap.md').write_text('',encoding='utf-8')
    r=run_live_gray_readonly_seal(build_default_live_gray_readonly_seal_config(repo_root=tmp_path))
    assert r.decision in (LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE, LiveGrayReadonlySealDecision.NO_GO)
def test_stage58_decisions(tmp_path):
    r=run_live_gray_readonly_seal(build_default_live_gray_readonly_seal_config(repo_root=make_root(tmp_path)))
    assert r.decision==LiveGrayReadonlySealDecision.READY_FOR_READONLY_SEAL_REVIEW
    r=run_live_gray_readonly_seal(build_default_live_gray_readonly_seal_config(repo_root=make_root(tmp_path/'b','NEED_MORE_EVIDENCE')))
    assert r.decision==LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE
    r=run_live_gray_readonly_seal(build_default_live_gray_readonly_seal_config(repo_root=make_root(tmp_path/'c','NO_GO')))
    assert r.decision==LiveGrayReadonlySealDecision.NO_GO
    r=run_live_gray_readonly_seal(build_default_live_gray_readonly_seal_config(repo_root=make_root(tmp_path/'d','READY_FOR_FINAL_APPROVAL_REVIEW',1)))
    assert r.decision==LiveGrayReadonlySealDecision.NO_GO
def test_reports_manifest_safety_and_formatter(tmp_path):
    r=run_live_gray_readonly_seal(build_default_live_gray_readonly_seal_config(repo_root=make_root(tmp_path)))
    assert len(r.material_lock_items)>=8 and len(r.checklist_items)>=12 and len(r.signoff_items)>=7 and len(r.next_plan_items)>=11
    assert all(hasattr(i,'relative_path') and hasattr(i,'sha256') for i in r.manifest_items)
    md=__import__('qmt_ai_trading.live_gray_readonly_seal.formatters',fromlist=['format_live_gray_readonly_seal_report_markdown']).format_live_gray_readonly_seal_report_markdown(r)
    assert '## Safety Note' in md and '不是实盘授权' in md and 'READY_FOR_READONLY_SEAL_REVIEW' in md
    assert any(x['severity']=='CRITICAL' for x in scan_live_gray_readonly_seal_text_for_forbidden_markers('xttrader XtQuantTrader place_order query_stock_asset','actual executable'))
    assert all(x['severity']=='WARN' for x in scan_live_gray_readonly_seal_text_for_forbidden_markers('不调用 xttrader','live_gray_final_approval_stage58/live_gray_final_approval.md'))
def test_cli_generates_outputs(tmp_path):
    make_root(tmp_path); out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_live_gray_readonly_seal.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'live_gray_readonly_seal.md'),'--json-output',str(out/'live_gray_readonly_seal.json'),'--lock-output',str(out/'material_lock.md'),'--lock-json-output',str(out/'material_lock.json'),'--checklist-output',str(out/'pre_run_checklist.md'),'--checklist-json-output',str(out/'pre_run_checklist.json'),'--manifest-output',str(out/'readonly_seal_manifest.md'),'--manifest-json-output',str(out/'readonly_seal_manifest.json'),'--signoff-output',str(out/'final_signoff_recheck.md'),'--signoff-json-output',str(out/'final_signoff_recheck.json'),'--plan-output',str(out/'next_pre_gray_review_plan.md'),'--plan-json-output',str(out/'next_pre_gray_review_plan.json')]
    assert subprocess.run(cmd,cwd=Path(__file__).parents[1]).returncode==0
    for n in ['live_gray_readonly_seal.md','live_gray_readonly_seal.json','material_lock.md','material_lock.json','pre_run_checklist.md','pre_run_checklist.json','readonly_seal_manifest.md','readonly_seal_manifest.json','final_signoff_recheck.md','final_signoff_recheck.json','next_pre_gray_review_plan.md','next_pre_gray_review_plan.json']: assert (out/n).exists()
def test_stage59_static_guards():
    assert not list(Path('scripts').glob('validate_stage58.ps1.bak_stage58fix_*'))
    assert 'powershell -NoProfile -Command \\' not in Path('scripts/validate_stage59.ps1').read_text(encoding='utf-8')
    assert 'scripts/sync_all.ps1' not in subprocess.check_output(['git','diff','--name-only']).decode().splitlines()
