from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_runbook.models import LiveRunbookConfig, LiveRunbookReport, LiveRunbookDecision as D, LiveRunbookSeverity as Sev
from qmt_ai_trading.live_runbook.service import build_default_live_runbook_config, run_live_runbook
from qmt_ai_trading.live_runbook.formatters import format_live_runbook_report_markdown
from qmt_ai_trading.live_runbook.safety import classify_runbook_marker


def _write(path: Path, decision: str, critical: int = 0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'decision': decision, 'summary': {'critical': critical}}, ensure_ascii=False), encoding='utf-8')

def test_models_default_construct():
    assert LiveRunbookConfig().read_only is True
    assert LiveRunbookReport().decision == D.NEED_MORE_EVIDENCE

def test_missing_stage44_does_not_crash(tmp_path):
    r=run_live_runbook(build_default_live_runbook_config(repo_root=tmp_path))
    assert r.decision in {D.NEED_MORE_EVIDENCE, D.NO_GO}

def test_stage44_need_more_evidence_not_no_go(tmp_path):
    _write(tmp_path/'live_env_snapshot_stage44/live_env_snapshot.json','NEED_MORE_EVIDENCE',0)
    r=run_live_runbook(build_default_live_runbook_config(repo_root=tmp_path))
    assert r.decision == D.NEED_MORE_EVIDENCE

def test_stage44_no_go_or_critical_blocks(tmp_path):
    _write(tmp_path/'live_env_snapshot_stage44/live_env_snapshot.json','READY_FOR_ENV_SNAPSHOT',1)
    assert run_live_runbook(build_default_live_runbook_config(repo_root=tmp_path)).decision == D.NO_GO

def test_stage41_42_43_44_blocked_blocks(tmp_path):
    _write(tmp_path/'live_gray_ledger_stage41/live_gray_ledger.json','BLOCKED',0)
    _write(tmp_path/'live_gray_review_stage42/live_gray_review.json','READY_FOR_HUMAN_REVIEW',0)
    _write(tmp_path/'live_signature_freeze_stage43/live_signature_freeze.json','READY_FOR_SIGNATURE_FREEZE',0)
    _write(tmp_path/'live_env_snapshot_stage44/live_env_snapshot.json','READY_FOR_ENV_SNAPSHOT',0)
    assert run_live_runbook(build_default_live_runbook_config(repo_root=tmp_path)).decision == D.NO_GO

def test_marker_classification():
    assert classify_runbook_marker('docs/test.md','xttrader','marker definitions') == Sev.WARN
    assert classify_runbook_marker('qmt_ai_trading/live_executor.py','xttrader','place_order query_stock_asset') == Sev.CRITICAL

def test_formatter_safety_note():
    md=format_live_runbook_report_markdown(LiveRunbookReport(decision=D.READY_FOR_RUNBOOK_REVIEW))
    assert '## Safety Note' in md
    assert 'READY_FOR_RUNBOOK_REVIEW 只表示运行手册材料可供人工复核' in md
    assert '不是实盘授权' in md

def test_cli_generates_package(tmp_path):
    out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_live_runbook.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'live_runbook.md'),'--json-output',str(out/'live_runbook.json'),'--rehearsal-output',str(out/'manual_rehearsal.md'),'--rehearsal-json-output',str(out/'manual_rehearsal.json'),'--incident-output',str(out/'incident_playbook.md'),'--incident-json-output',str(out/'incident_playbook.json')]
    res=subprocess.run(cmd,cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True)
    assert res.returncode == 0, res.stderr
    for name in ['live_runbook.md','live_runbook.json','manual_rehearsal.md','manual_rehearsal.json','incident_playbook.md','incident_playbook.json']:
        assert (out/name).exists()

def test_gitignore_and_sync_all_unchanged():
    gi=Path('.gitignore').read_text(encoding='utf-8')
    for x in ['validation_logs/','live_runbook_stage45/','live_runbook/','market_data_test_stage45/']:
        assert x in gi
    status=subprocess.run(['git','status','--short','--','scripts/sync_all.ps1'],text=True,capture_output=True)
    assert status.stdout.strip()==''

def test_stage44_safety_note_deduped():
    from qmt_ai_trading.live_env_snapshot.formatters import format_live_env_snapshot_report_markdown
    from qmt_ai_trading.live_env_snapshot.models import LiveEnvSnapshotReport
    md=format_live_env_snapshot_report_markdown(LiveEnvSnapshotReport())
    assert md.count('本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。') == 1

def test_register_preview_contains_stage45():
    res=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-live-runbook','--live-runbook-output-dir','live_runbook','--time','15:30'],text=True,capture_output=True)
    assert res.returncode==0
    assert 'Stage45 Live Runbook' in res.stdout
    assert 'read_only=True' in res.stdout and 'dry_run_only=True' in res.stdout and 'no_task_registered=True' in res.stdout
