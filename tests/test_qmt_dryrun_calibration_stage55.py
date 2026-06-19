from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.qmt_dryrun_calibration.models import *
from qmt_ai_trading.qmt_dryrun_calibration.service import *
from qmt_ai_trading.qmt_dryrun_calibration.safety import scan_qmt_dryrun_calibration_text_for_forbidden_markers

def test_config_and_report_default_construct():
    assert QmtDryrunCalibrationConfig().read_only is True
    assert QmtDryrunCalibrationReport().decision == QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE

def test_missing_stage54_does_not_crash(tmp_path):
    r=run_qmt_dryrun_calibration(build_default_qmt_dryrun_calibration_config(repo_root=tmp_path, cache_root='cache'))
    assert r.decision in {QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE, QmtDryrunCalibrationDecision.NO_GO}

def test_stage54_ready_can_review_or_need_more(tmp_path):
    (tmp_path/'live_gap_clearance_stage54').mkdir()
    (tmp_path/'docs').mkdir()
    (tmp_path/'docs/qmt-ai-trading-project-roadmap.md').write_text('完整工程阶段计划与前端 UI 产品化路线（Stage 1-75） Stage61：API Gateway 基础层 Stage75：本地控制台封版 / 可选桌面化 UI 不直接访问 QMT UI 不能绕过 Risk Gate UI 不能绕过 Human Approval UI 不能自动 approve',encoding='utf-8')
    (tmp_path/'live_gap_clearance_stage54/live_gap_clearance.json').write_text(json.dumps({'decision':'READY_FOR_GAP_CLEARANCE_REVIEW','summary':{'critical':0}},ensure_ascii=False),encoding='utf-8')
    r=run_qmt_dryrun_calibration(build_default_qmt_dryrun_calibration_config(repo_root=tmp_path, cache_root='cache'))
    assert r.decision in {QmtDryrunCalibrationDecision.READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW, QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE}

def test_stage54_no_go_blocks(tmp_path):
    (tmp_path/'live_gap_clearance_stage54').mkdir(); (tmp_path/'docs').mkdir()
    (tmp_path/'docs/qmt-ai-trading-project-roadmap.md').write_text('完整工程阶段计划与前端 UI 产品化路线（Stage 1-75） Stage61：API Gateway 基础层 Stage75：本地控制台封版 / 可选桌面化 UI 不直接访问 QMT UI 不能绕过 Risk Gate UI 不能绕过 Human Approval UI 不能自动 approve',encoding='utf-8')
    (tmp_path/'live_gap_clearance_stage54/live_gap_clearance.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical':1}},ensure_ascii=False),encoding='utf-8')
    assert run_qmt_dryrun_calibration(build_default_qmt_dryrun_calibration_config(repo_root=tmp_path, cache_root='cache')).decision == QmtDryrunCalibrationDecision.NO_GO

def test_safety_classification_generated_warn_and_executable_critical():
    assert all(str(f.severity).endswith('WARN') or getattr(f.severity,'value','')=='WARN' for f in scan_qmt_dryrun_calibration_text_for_forbidden_markers('xttrader place_order query_stock_asset','docs/tests/safety marker definitions'))
    assert any(getattr(f.severity,'value','')=='CRITICAL' for f in scan_qmt_dryrun_calibration_text_for_forbidden_markers('xttrader XtQuantTrader place_order query_stock_asset','actual executable'))
    assert not scan_qmt_dryrun_calibration_text_for_forbidden_markers('xtquant.xtdata get_market_data','actual executable')

def test_formatters_and_cli_outputs(tmp_path):
    out=tmp_path/'out'; cache=tmp_path/'cache'
    cmd=[sys.executable,'scripts/run_qmt_dryrun_calibration.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--cache-root',str(cache),'--output',str(out/'qmt_dryrun_calibration.md'),'--json-output',str(out/'qmt_dryrun_calibration.json'),'--xtdata-output',str(out/'xtdata_capability.md'),'--xtdata-json-output',str(out/'xtdata_capability.json'),'--whitelist-output',str(out/'etf_whitelist_calibration.md'),'--whitelist-json-output',str(out/'etf_whitelist_calibration.json'),'--plan-output',str(out/'next_real_cache_quality_plan.md'),'--plan-json-output',str(out/'next_real_cache_quality_plan.json')]
    res=subprocess.run(cmd,cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True)
    assert res.returncode in (0,1)
    for name in ['qmt_dryrun_calibration.md','qmt_dryrun_calibration.json','xtdata_capability.md','xtdata_capability.json','etf_whitelist_calibration.md','etf_whitelist_calibration.json','next_real_cache_quality_plan.md','next_real_cache_quality_plan.json']:
        assert (out/name).exists()
    text=(out/'qmt_dryrun_calibration.md').read_text(encoding='utf-8')
    assert '## Safety Note' in text and '不是实盘授权' in text and 'READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW' in text

def test_roadmap_ui_plan_and_no_stage54_backups():
    root=Path(__file__).resolve().parents[1]
    txt=(root/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    for needle in ['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']:
        assert needle in txt
    assert not list((root/'qmt_ai_trading/live_gap_clearance').glob('*.bak_stage54fix_*'))
    assert not list((root/'scripts').glob('validate_stage54.ps1.bak_stage54fix_*'))
    assert 'sync_all.ps1' not in subprocess.run(['git','diff','--name-only'],cwd=root,text=True,capture_output=True).stdout
