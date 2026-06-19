import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.live_gray_review.formatters import format_live_gray_review_report_markdown
from qmt_ai_trading.live_gray_review.models import LiveGrayReviewConfig, LiveGrayReviewDecision, LiveGrayReviewReport, LiveGrayReviewSeverity
from qmt_ai_trading.live_gray_review.safety import classify_review_marker, scan_review_text_for_forbidden_markers
from qmt_ai_trading.live_gray_review.service import build_default_live_gray_review_config, run_live_gray_review


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

def test_config_and_report_defaults():
    assert LiveGrayReviewConfig().output_dir == 'live_gray_review_stage42'
    assert LiveGrayReviewReport().decision == LiveGrayReviewDecision.NEED_MORE_EVIDENCE

def test_missing_stage41_ledger_no_crash(tmp_path):
    report=run_live_gray_review(build_default_live_gray_review_config(tmp_path))
    assert report.decision in {LiveGrayReviewDecision.NEED_MORE_EVIDENCE, LiveGrayReviewDecision.NO_GO}

def test_stage41_need_more_evidence_not_no_go(tmp_path):
    write_json(tmp_path/'live_gray_ledger_stage41/live_gray_ledger.json', {'decision':'NEED_MORE_EVIDENCE','summary':{'critical':0}})
    write_json(tmp_path/'redline_review_stage40/redline_review.json', {'decision':'READY_FOR_REDLINE_REVIEW','summary':{'critical':0}})
    (tmp_path/'final_authorization_stage40').mkdir()
    report=run_live_gray_review(build_default_live_gray_review_config(tmp_path))
    assert report.decision == LiveGrayReviewDecision.NEED_MORE_EVIDENCE

def test_stage41_blocked_or_critical_no_go(tmp_path):
    write_json(tmp_path/'live_gray_ledger_stage41/live_gray_ledger.json', {'decision':'BLOCKED','summary':{'critical':0}})
    report=run_live_gray_review(build_default_live_gray_review_config(tmp_path))
    assert report.decision == LiveGrayReviewDecision.NO_GO
    write_json(tmp_path/'live_gray_ledger_stage41/live_gray_ledger.json', {'decision':'NEED_MORE_EVIDENCE','summary':{'critical':1}})
    report=run_live_gray_review(build_default_live_gray_review_config(tmp_path))
    assert report.decision == LiveGrayReviewDecision.NO_GO

def test_stage40_blocked_or_critical_no_go(tmp_path):
    write_json(tmp_path/'redline_review_stage40/redline_review.json', {'decision':'BLOCKED','summary':{'critical':0}})
    assert run_live_gray_review(build_default_live_gray_review_config(tmp_path)).decision == LiveGrayReviewDecision.NO_GO
    write_json(tmp_path/'redline_review_stage40/redline_review.json', {'decision':'READY_FOR_REDLINE_REVIEW','summary':{'critical':2}})
    assert run_live_gray_review(build_default_live_gray_review_config(tmp_path)).decision == LiveGrayReviewDecision.NO_GO

def test_forbidden_marker_classification_contexts():
    _, sev, _, _ = classify_review_marker('xttrader', 'docs/stage42.md', '禁止 xttrader')
    assert sev == LiveGrayReviewSeverity.WARN
    _, sev, _, _ = classify_review_marker('place_order', 'tests/test_live_gray_review_stage42.py', 'marker place_order')
    assert sev == LiveGrayReviewSeverity.WARN
    for marker in ['xttrader','place_order','query_stock_asset']:
        _, sev, _, _ = classify_review_marker(marker, 'scripts/live_runner.py', f'{marker}()')
        assert sev == LiveGrayReviewSeverity.CRITICAL

def test_formatter_safety_note_and_authorization_semantics():
    text=format_live_gray_review_report_markdown(LiveGrayReviewReport(decision=LiveGrayReviewDecision.READY_FOR_HUMAN_REVIEW))
    assert '## Safety Note' in text
    assert 'READY_FOR_HUMAN_REVIEW 只表示材料可供人工复核' in text
    assert '不是实盘授权' in text

def test_cli_generates_review_and_rehearsal(tmp_path):
    script=Path(__file__).resolve().parents[1]/'scripts/run_live_gray_review.py'
    out=tmp_path/'out'
    res=subprocess.run([sys.executable, str(script), '--repo-root', str(tmp_path), '--output-dir', str(out)], text=True, capture_output=True)
    assert res.returncode == 0
    assert (out/'live_gray_review.md').exists()
    assert (out/'live_gray_review.json').exists()
    assert (out/'readonly_rehearsal.md').exists()
    assert (out/'readonly_rehearsal.json').exists()

def test_daily_and_scheduled_and_register_live_gray_review(tmp_path):
    root=Path(__file__).resolve().parents[1]
    cache=tmp_path/'cache'; out=tmp_path/'review'
    subprocess.run([sys.executable, str(root/'scripts/warmup_etf_universe.py'), '--lookback-days','40','--frequency','1d','--provider','mock','--cache-root', str(cache)], check=True)
    base=['--cache-root', str(cache), '--research-start','2026-05-09','--research-end','2026-06-18','--research-frequency','1d','--min-bars','20','--cached-strategy-top-n','1','--enable-live-gray-review','--live-gray-review-output-dir', str(out)]
    assert subprocess.run([sys.executable, str(root/'scripts/run_daily_pipeline.py'), *base]).returncode == 0
    assert (out/'live_gray_review.md').exists()
    assert subprocess.run([sys.executable, str(root/'scripts/run_scheduled_daily_pipeline.py'), '--warmup-universe','--warmup-provider','mock','--universe-lookback-days','40','--warmup-frequency','1d', *base]).returncode == 0
    res=subprocess.run([sys.executable, str(root/'scripts/register_daily_pipeline_task.py'), *base, '--time','15:30'], text=True, capture_output=True)
    assert res.returncode == 0
    assert 'enable_live_gray_review=True' in res.stdout
    assert 'read_only=True' in res.stdout and 'dry_run_only=True' in res.stdout and 'no_task_registered=True' in res.stdout

def test_validation_logs_ignored_and_sync_all_not_modified():
    gi=Path('.gitignore').read_text(encoding='utf-8')
    assert 'validation_logs/' in gi
    assert Path('scripts/sync_all.ps1').exists()
