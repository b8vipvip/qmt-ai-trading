from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_signature_freeze.formatters import format_live_signature_freeze_report_markdown
from qmt_ai_trading.live_signature_freeze.models import LiveSignatureFreezeConfig, LiveSignatureFreezeDecision as D, LiveSignatureFreezeReport, LiveSignatureFreezeSeverity as Sev
from qmt_ai_trading.live_signature_freeze.safety import classify_signature_freeze_marker
from qmt_ai_trading.live_signature_freeze.service import build_default_live_signature_freeze_config, run_live_signature_freeze

ROOT=Path(__file__).resolve().parents[1]

def write_json(p: Path, data: dict): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
def cfg(tmp_path): return build_default_live_signature_freeze_config(tmp_path, output_dir='out')

def test_config_and_report_default_constructible():
    assert LiveSignatureFreezeConfig().output_dir
    assert LiveSignatureFreezeReport().decision == D.NEED_MORE_EVIDENCE

def test_missing_stage42_does_not_crash(tmp_path):
    r=run_live_signature_freeze(cfg(tmp_path))
    assert r.decision in {D.NEED_MORE_EVIDENCE, D.NO_GO}

def test_stage42_need_more_evidence_without_critical_is_not_no_go(tmp_path):
    write_json(tmp_path/'live_gray_review_stage42/live_gray_review.json', {'decision':'NEED_MORE_EVIDENCE','summary':{'critical':0}})
    r=run_live_signature_freeze(cfg(tmp_path))
    assert r.decision == D.NEED_MORE_EVIDENCE

def test_stage42_no_go_or_critical_blocks(tmp_path):
    write_json(tmp_path/'live_gray_review_stage42/live_gray_review.json', {'decision':'NO_GO','summary':{'critical':0}})
    assert run_live_signature_freeze(cfg(tmp_path)).decision == D.NO_GO
    tmp2=tmp_path/'b'; write_json(tmp2/'live_gray_review_stage42/live_gray_review.json', {'decision':'READY_FOR_HUMAN_REVIEW','summary':{'critical':1}})
    assert run_live_signature_freeze(cfg(tmp2)).decision == D.NO_GO

def test_stage40_blocked_or_critical_blocks(tmp_path):
    write_json(tmp_path/'redline_review_stage40/redline_review.json', {'decision':'BLOCKED','summary':{'critical':0}})
    assert run_live_signature_freeze(cfg(tmp_path)).decision == D.NO_GO
    tmp2=tmp_path/'b'; write_json(tmp2/'redline_review_stage40/redline_review.json', {'decision':'READY','summary':{'critical':2}})
    assert run_live_signature_freeze(cfg(tmp2)).decision == D.NO_GO

def test_safety_marker_context_classification():
    assert classify_signature_freeze_marker('xttrader','docs/x.md','禁止 xttrader')[1] == Sev.WARN
    assert classify_signature_freeze_marker('place_order','tests/test_x.py','FORBIDDEN_MARKERS place_order')[1] == Sev.WARN
    assert classify_signature_freeze_marker('xttrader','qmt_ai_trading/live_exec.py','xttrader.connect()')[1] == Sev.CRITICAL
    assert classify_signature_freeze_marker('place_order','qmt_ai_trading/live_exec.py','place_order()')[1] == Sev.CRITICAL
    assert classify_signature_freeze_marker('query_stock_asset','qmt_ai_trading/live_exec.py','query_stock_asset()')[1] == Sev.CRITICAL

def test_formatter_safety_note_and_ready_not_authorization():
    md=format_live_signature_freeze_report_markdown(LiveSignatureFreezeReport(decision=D.READY_FOR_SIGNATURE))
    assert '## Safety Note' in md
    assert 'READY_FOR_SIGNATURE 只表示材料可供人工签字复核' in md
    assert '不是实盘授权' in md

def test_cli_generates_signature_and_config_freeze(tmp_path):
    out=tmp_path/'out'
    cmd=[sys.executable, str(ROOT/'scripts/run_live_signature_freeze.py'), '--repo-root', str(tmp_path), '--output-dir', str(out), '--output', str(out/'live_signature_freeze.md'), '--json-output', str(out/'live_signature_freeze.json'), '--config-freeze-output', str(out/'config_freeze.md'), '--config-freeze-json-output', str(out/'config_freeze.json')]
    res=subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    assert res.returncode == 0, res.stderr+res.stdout
    assert (out/'live_signature_freeze.md').exists() and (out/'live_signature_freeze.json').exists()
    assert (out/'config_freeze.md').exists() and (out/'config_freeze.json').exists()

def test_daily_scheduled_and_register_stage43_options(tmp_path):
    out=tmp_path/'sig'
    daily=subprocess.run([sys.executable, str(ROOT/'scripts/run_daily_pipeline.py'), '--cache-root', str(tmp_path/'cache'), '--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-signature-freeze','--live-signature-freeze-output-dir', str(out)], cwd=ROOT, text=True, capture_output=True)
    assert daily.returncode == 0, daily.stderr+daily.stdout
    assert (out/'live_signature_freeze.md').exists() and (out/'config_freeze.md').exists()
    out2=tmp_path/'sig2'
    sched=subprocess.run([sys.executable, str(ROOT/'scripts/run_scheduled_daily_pipeline.py'), '--cache-root', str(tmp_path/'cache2'), '--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-signature-freeze','--live-signature-freeze-output-dir', str(out2)], cwd=ROOT, text=True, capture_output=True)
    assert sched.returncode == 0, sched.stderr+sched.stdout
    assert (out2/'live_signature_freeze.md').exists() and (out2/'config_freeze.md').exists()
    reg=subprocess.run([sys.executable, str(ROOT/'scripts/register_daily_pipeline_task.py'), '--enable-live-signature-freeze', '--live-signature-freeze-output-dir', 'live_signature_freeze', '--time','15:30'], cwd=ROOT, text=True, capture_output=True)
    assert reg.returncode == 0, reg.stderr+reg.stdout
    assert 'enable_live_signature_freeze=True' in reg.stdout and 'read_only=True' in reg.stdout and 'dry_run_only=True' in reg.stdout and 'no_task_registered=True' in reg.stdout

def test_gitignore_and_sync_all_not_modified():
    gi=(ROOT/'.gitignore').read_text(encoding='utf-8')
    assert 'validation_logs/' in gi and 'live_signature_freeze_stage43/' in gi and 'market_data_test_stage43/' in gi
    diff=subprocess.run(['git','diff','--','scripts/sync_all.ps1'], cwd=ROOT, text=True, capture_output=True)
    assert diff.stdout == ''
