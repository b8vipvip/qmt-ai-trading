from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_env_snapshot.formatters import format_live_env_snapshot_report_markdown
from qmt_ai_trading.live_env_snapshot.models import LiveEnvSnapshotConfig, LiveEnvSnapshotDecision as D, LiveEnvSnapshotReport, LiveEnvSnapshotSeverity as Sev
from qmt_ai_trading.live_env_snapshot.safety import classify_env_snapshot_marker
from qmt_ai_trading.live_env_snapshot.service import build_default_live_env_snapshot_config, run_live_env_snapshot

ROOT=Path(__file__).resolve().parents[1]
def cfg(tmp_path): return build_default_live_env_snapshot_config(tmp_path, output_dir='out')
def write_json(path, data): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data), encoding='utf-8')
def seed_gitignore(root): (root/'.gitignore').write_text('validation_logs/\nmarket_data/\nreports/\nlogs/\nlive_env_snapshot_stage44/\nlive_env_snapshot/\nmarket_data_test_stage44/\n', encoding='utf-8')

def test_models_default_construct():
    assert LiveEnvSnapshotConfig().read_only is True
    assert LiveEnvSnapshotReport().decision == D.NEED_MORE_EVIDENCE

def test_missing_stage43_does_not_crash(tmp_path):
    seed_gitignore(tmp_path); r=run_live_env_snapshot(cfg(tmp_path)); assert r.decision in {D.NEED_MORE_EVIDENCE, D.NO_GO}

def test_stage43_need_more_evidence_not_no_go(tmp_path):
    seed_gitignore(tmp_path); write_json(tmp_path/'live_signature_freeze_stage43/live_signature_freeze.json', {'decision':'NEED_MORE_EVIDENCE','summary':{'critical':0}})
    r=run_live_env_snapshot(cfg(tmp_path)); assert r.decision == D.NEED_MORE_EVIDENCE

def test_stage43_no_go_or_critical_is_no_go(tmp_path):
    seed_gitignore(tmp_path); write_json(tmp_path/'live_signature_freeze_stage43/live_signature_freeze.json', {'decision':'NO_GO','summary':{'critical':0}})
    assert run_live_env_snapshot(cfg(tmp_path)).decision == D.NO_GO
    tmp2=tmp_path/'b'; tmp2.mkdir(); seed_gitignore(tmp2); write_json(tmp2/'live_signature_freeze_stage43/live_signature_freeze.json', {'decision':'READY_FOR_SIGNATURE','summary':{'critical':1}})
    assert run_live_env_snapshot(cfg(tmp2)).decision == D.NO_GO

def test_stage40_41_42_blocked_are_no_go(tmp_path):
    for rel,dec in [('redline_review_stage40/redline_review.json','BLOCKED'),('live_gray_ledger_stage41/live_gray_ledger.json','BLOCKED'),('live_gray_review_stage42/live_gray_review.json','NO_GO')]:
        root=tmp_path/rel.split('/')[0]; root.mkdir(parents=True, exist_ok=True); base=root.parent; seed_gitignore(base); write_json(base/rel, {'decision':dec,'summary':{'critical':0}})
        assert run_live_env_snapshot(cfg(base)).decision == D.NO_GO

def test_marker_classification_warn_and_critical():
    assert classify_env_snapshot_marker('docs/safety.md','xttrader') == Sev.WARN
    assert classify_env_snapshot_marker('tests/test_safety.py','place_order') == Sev.WARN
    assert classify_env_snapshot_marker('qmt_ai_trading/gateway/live.py','query_stock_asset') == Sev.CRITICAL


def test_stage43_generated_markdown_xttrader_text_is_warn_not_no_go(tmp_path):
    seed_gitignore(tmp_path)
    sig=tmp_path/'live_signature_freeze_stage43'
    sig.mkdir(parents=True)
    (sig/'live_signature_freeze.json').write_text(json.dumps({'decision':'NEED_MORE_EVIDENCE','summary':{'critical':0},'safety_note':'does not call xttrader; read-only; not trade authorization'}), encoding='utf-8')
    (sig/'live_signature_freeze.md').write_text('## Safety Note\nStage44 does not call xttrader. Human Checklist: 不调用 xttrader; dry-run only; not trade authorization. place_order query_stock_asset are forbidden examples.', encoding='utf-8')
    r=run_live_env_snapshot(cfg(tmp_path))
    assert r.decision == D.NEED_MORE_EVIDENCE
    assert r.summary['critical'] == 0
    assert any('xttrader' in w for w in r.warnings)


def test_stage43_generated_json_xttrader_text_is_warn_not_no_go(tmp_path):
    seed_gitignore(tmp_path)
    sig=tmp_path/'live_signature_freeze_stage43'
    sig.mkdir(parents=True)
    (sig/'live_signature_freeze.json').write_text(json.dumps({'decision':'NEED_MORE_EVIDENCE','summary':{'critical':0},'warnings':['Safety Note: does not call xttrader; read-only; dry-run only; not trade authorization; no place_order or query_stock_asset execution path']}), encoding='utf-8')
    r=run_live_env_snapshot(cfg(tmp_path))
    assert r.decision == D.NEED_MORE_EVIDENCE
    assert r.summary['critical'] == 0


def test_real_python_execution_marker_still_no_go(tmp_path):
    seed_gitignore(tmp_path)
    bad=tmp_path/'qmt_ai_trading/gateway/live.py'
    assert classify_env_snapshot_marker(bad, 'xttrader', 'import xttrader\nxttrader.connect()') == Sev.CRITICAL


def test_formatter_safety_note():
    md=format_live_env_snapshot_report_markdown(LiveEnvSnapshotReport(decision=D.READY_FOR_ENV_SNAPSHOT))
    assert '## Safety Note' in md and 'READY_FOR_ENV_SNAPSHOT 只表示环境快照材料可供人工复核' in md and '不是实盘授权' in md

def test_cli_generates_both_reports(tmp_path):
    seed_gitignore(tmp_path); out=tmp_path/'out'
    cmd=[sys.executable, str(ROOT/'scripts/run_live_env_snapshot.py'), '--repo-root', str(tmp_path), '--output-dir', str(out), '--output', str(out/'live_env_snapshot.md'), '--json-output', str(out/'live_env_snapshot.json'), '--snapshot-output', str(out/'readonly_environment_snapshot.md'), '--snapshot-json-output', str(out/'readonly_environment_snapshot.json')]
    res=subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    assert (out/'live_env_snapshot.md').exists() and (out/'live_env_snapshot.json').exists()
    assert (out/'readonly_environment_snapshot.md').exists() and (out/'readonly_environment_snapshot.json').exists()

def test_gitignore_rules_present():
    gi=(ROOT/'.gitignore').read_text(encoding='utf-8')
    for item in ['validation_logs/','market_data/','reports/','logs/','live_env_snapshot_stage44/','live_env_snapshot/','market_data_test_stage44/']:
        assert item in gi

def test_daily_scheduled_register_integration(tmp_path):
    out=tmp_path/'live_env_snapshot_stage44'
    daily=subprocess.run([sys.executable, str(ROOT/'scripts/run_daily_pipeline.py'), '--cache-root', str(tmp_path/'market_data'), '--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-env-snapshot','--live-env-snapshot-output-dir', str(out)], cwd=ROOT, text=True, capture_output=True)
    assert daily.returncode in (0,1) and (out/'live_env_snapshot.md').exists()
    out2=tmp_path/'scheduled_env_snapshot'
    sched=subprocess.run([sys.executable, str(ROOT/'scripts/run_scheduled_daily_pipeline.py'), '--cache-root', str(tmp_path/'market_data'), '--data-source-mode','cached_real_first','--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','2','--enable-live-env-snapshot','--live-env-snapshot-output-dir', str(out2)], cwd=ROOT, text=True, capture_output=True)
    assert sched.returncode in (0,1)
    reg=subprocess.run([sys.executable, str(ROOT/'scripts/register_daily_pipeline_task.py'), '--enable-live-env-snapshot', '--live-env-snapshot-output-dir','live_env_snapshot','--time','15:30'], cwd=ROOT, text=True, capture_output=True)
    assert reg.returncode == 0 and 'enable_live_env_snapshot=True' in reg.stdout and 'read_only=True' in reg.stdout and 'dry_run_only=True' in reg.stdout and 'no_task_registered=True' in reg.stdout

def test_no_validation_logs_tracked_and_sync_all_unmodified():
    tracked=subprocess.run(['git','ls-files','validation_logs'], cwd=ROOT, text=True, capture_output=True)
    assert tracked.stdout.strip() == ''
    status=subprocess.run(['git','status','--short','--','scripts/sync_all.ps1'], cwd=ROOT, text=True, capture_output=True)
    assert status.stdout.strip() == ''

def test_stage43_blank_warning_filtered():
    from qmt_ai_trading.live_signature_freeze.formatters import format_live_signature_freeze_report_markdown
    from qmt_ai_trading.live_signature_freeze.models import LiveSignatureFreezeReport
    md=format_live_signature_freeze_report_markdown(LiveSignatureFreezeReport(warnings=['']))
    assert '- \n' not in md
