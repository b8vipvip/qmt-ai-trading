from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
from qmt_ai_trading.redline_review.models import RedlineReviewConfig, RedlineReviewReport, SAFETY_NOTE
from qmt_ai_trading.redline_review.safety import classify_marker, build_default_redline_review_config
from qmt_ai_trading.redline_review.scanner import scan_file_for_redline_markers, scan_sensitive_files, scan_scheduler_preview_text, scan_dashboard_for_order_entry
from qmt_ai_trading.redline_review.service import run_redline_review, save_redline_review_report
from qmt_ai_trading.redline_review.formatters import format_redline_review_report_markdown
from qmt_ai_trading.dashboard.collector import collect_redline_review_section
from qmt_ai_trading.dashboard.models import DashboardConfig, DashboardStatus

def test_models_and_safety_markers():
    RedlineReviewConfig(); RedlineReviewReport()
    for m in ['--live-enabled','--execute-live','--real-send','xttrader','submit_order','place_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','requests.post','smtp','sendMessage','webhook','bypass Risk Gate','bypass Human Approval']:
        f=classify_marker(m,'qmt_ai_trading/app.py',m); assert f.marker==m

def test_allowed_contexts_record_not_critical():
    f=classify_marker('xttrader','docs/x.md','禁止 xttrader and review-only')
    assert str(f.status).endswith('WARN') and f.marker
    f2=classify_marker('--live-enabled','tests/x.py','assert "--live-enabled"')
    assert str(f2.status).endswith('WARN')

def test_scanner_boundaries(tmp_path):
    assert scan_file_for_redline_markers(tmp_path/'missing.py', RedlineReviewConfig())
    (tmp_path/'.env').write_text('NOT_READ=1')
    assert str(scan_sensitive_files(tmp_path, RedlineReviewConfig())[0].status).endswith('FAIL')
    assert str(scan_scheduler_preview_text('py x.py --execute-live', RedlineReviewConfig())[0].status).endswith('FAIL')
    assert str(scan_dashboard_for_order_entry('<button>submit order</button>', RedlineReviewConfig())[0].status).endswith('FAIL')

def test_service_cli_formatter_and_dashboard(tmp_path):
    cfg=build_default_redline_review_config(tmp_path, include_paths=[])
    r=run_redline_review(config=cfg)
    md=tmp_path/'a.redline_review.md'; js=tmp_path/'a.redline_review.json'
    save_redline_review_report(r,md); save_redline_review_report(r,js)
    assert SAFETY_NOTE in format_redline_review_report_markdown(r)
    cp=subprocess.run([sys.executable, str(ROOT/'scripts/run_redline_review.py'), '--repo-root', str(tmp_path), '--output', str(tmp_path/'out.md'), '--json-output', str(tmp_path/'out.json')], cwd=ROOT, text=True, capture_output=True)
    assert cp.returncode==0, cp.stderr
    sec=collect_redline_review_section(DashboardConfig(include_redline_review=True, redline_review_dir=str(tmp_path)))
    assert sec.status != DashboardStatus.EMPTY

def test_pipeline_scheduler_register_and_docs(tmp_path):
    cp=subprocess.run([sys.executable, str(ROOT/'scripts/run_daily_pipeline.py'), '--data-source-mode','mock','--enable-redline-review','--redline-review-output-dir', str(tmp_path/'rr')], cwd=ROOT, text=True, capture_output=True, timeout=120)
    assert cp.returncode==0, cp.stderr
    cp2=subprocess.run([sys.executable, str(ROOT/'scripts/run_scheduled_daily_pipeline.py'), '--data-source-mode','mock','--enable-redline-review','--redline-review-output-dir', str(tmp_path/'rr2')], cwd=ROOT, text=True, capture_output=True, timeout=120)
    assert cp2.returncode==0, cp2.stderr
    cp3=subprocess.run([sys.executable, str(ROOT/'scripts/register_daily_pipeline_task.py'), '--enable-redline-review', '--redline-review-output-dir','redline_review'], cwd=ROOT, text=True, capture_output=True)
    assert cp3.returncode==0
    out=cp3.stdout
    assert '--enable-redline-review' in out and '--redline-review-output-dir redline_review' in out
    assert '--execute-live' not in out and '--real-send' not in out and '--live-enabled' not in out
    gi=(ROOT/'.gitignore').read_text(encoding='utf-8')
    assert 'redline_review/' in gi or 'redline_review_stage40/' in gi
    roadmap=(ROOT/'docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '阶段四十' in roadmap and '实盘开关隔离与最终红线复核' in roadmap
    assert '阶段四十一' in roadmap and '极小资金灰度实盘前只读确认台账' in roadmap
