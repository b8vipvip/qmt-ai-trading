from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.datahub.local_store import LocalBarStore
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.qmt_quality import QmtCacheQualityStatus, QmtDataQualityReport, build_qmt_quality_report, check_cache_roundtrip, check_qmt_bar_quality, format_qmt_quality_report_markdown
from qmt_ai_trading.datahub.qmt_realdata_plan import QmtRealDataPlan, build_default_qmt_realdata_plan, validate_qmt_realdata_plan


def bars():
    return [MarketBar("510300.SH", "2024-01-01", 1, 2, 1, 2, 100), MarketBar("510300.SH", "2024-01-02", 2, 3, 1, 2, 100)]


def test_report_instantiable():
    r = build_qmt_quality_report(symbol="510300.SH", frequency="1d", start_date="2024-01-01", end_date="2024-01-02", bars=bars(), cache_hit_after_save=True)
    assert isinstance(r, QmtDataQualityReport)


def test_quality_pass_normal_bars():
    checks, summary = check_qmt_bar_quality(bars())
    assert summary["bar_count"] == 2
    assert all(c.status == QmtCacheQualityStatus.PASS for c in checks)


def test_quality_detects_duplicate_datetime():
    checks, summary = check_qmt_bar_quality([bars()[0], bars()[0]])
    assert summary["duplicate_datetime_count"] == 1
    assert any(c.check_id == "duplicate_datetime" and c.status == QmtCacheQualityStatus.FAIL for c in checks)


def test_quality_detects_zero_volume():
    b = bars(); b[0].volume = 0
    checks, summary = check_qmt_bar_quality(b)
    assert summary["zero_volume_count"] == 1
    assert any(c.check_id == "zero_volume" and c.status == QmtCacheQualityStatus.WARN for c in checks)


def test_quality_detects_missing_ohlc():
    b = bars(); b[0].open = None
    checks, summary = check_qmt_bar_quality(b)
    assert summary["missing_ohlc_count"] == 1
    assert any(c.check_id == "missing_ohlc" and c.status == QmtCacheQualityStatus.FAIL for c in checks)


def test_quality_detects_unsorted_datetime():
    b = list(reversed(bars()))
    checks, summary = check_qmt_bar_quality(b)
    assert summary["sorted_by_datetime"] is False
    assert any(c.check_id == "datetime_sorted" and c.status == QmtCacheQualityStatus.FAIL for c in checks)


def test_cache_roundtrip(tmp_path):
    hit, loaded, msg = check_cache_roundtrip(LocalBarStore(tmp_path), symbol="510300.SH", frequency="1d", start_date="2024-01-01", end_date="2024-01-02", bars=bars())
    assert hit is True
    assert len(loaded) == 2
    assert "hit" in msg


def test_markdown_contains_symbol_and_decision():
    r = build_qmt_quality_report(symbol="510300.SH", frequency="1d", start_date="2024-01-01", end_date="2024-01-02", bars=bars(), cache_hit_after_save=True)
    md = format_qmt_quality_report_markdown(r)
    assert "510300.SH" in md
    assert "decision" in md


def test_plan_default_max_symbols():
    assert build_default_qmt_realdata_plan().max_symbols == 5


def test_plan_exceeds_max_symbols_warn_or_fail():
    plan = QmtRealDataPlan("x", [str(i) for i in range(6)], "2024-01-01", "2024-01-02", "1d", "qmt", "c", "r")
    checks = validate_qmt_realdata_plan(plan)
    assert any(c.check_id == "plan_max_symbols" and c.status in (QmtCacheQualityStatus.WARN, QmtCacheQualityStatus.FAIL) for c in checks)


def test_plan_exceeds_max_days_warn_or_fail():
    plan = QmtRealDataPlan("x", ["510300.SH"], "2024-01-01", "2024-05-01", "1d", "qmt", "c", "r")
    checks = validate_qmt_realdata_plan(plan)
    assert any(c.check_id == "plan_max_days" and c.status in (QmtCacheQualityStatus.WARN, QmtCacheQualityStatus.FAIL) for c in checks)


def test_smoke_script_no_xtquant_runs_unavailable_or_skipped(tmp_path):
    out = subprocess.run([sys.executable, "scripts/qmt_realdata_smoke_test.py", "--symbol", "510300.SH", "--start", "2024-01-01", "--end", "2024-01-10", "--frequency", "1d", "--cache-root", str(tmp_path / "cache"), "--report-dir", str(tmp_path / "reports"), "--write-json"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    assert out.returncode == 0
    assert "UNAVAILABLE" in out.stdout or "SKIPPED" in out.stdout or "AVAILABLE" in out.stdout


def test_cache_quality_script_empty_cache_runs(tmp_path):
    out = subprocess.run([sys.executable, "scripts/check_qmt_cache_quality.py", "--symbols", "510300.SH,510500.SH", "--start", "2024-01-01", "--end", "2024-01-10", "--frequency", "1d", "--cache-root", str(tmp_path / "cache"), "--report-dir", str(tmp_path / "reports"), "--write-json", "--min-bars", "1"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    assert out.returncode == 0
    assert "510300.SH" in out.stdout


def test_scripts_do_not_import_xttrader():
    for path in [Path("scripts/qmt_realdata_smoke_test.py"), Path("scripts/check_qmt_cache_quality.py"), Path("qmt_ai_trading/datahub/qmt_quality.py")]:
        text = path.read_text(encoding="utf-8")
        assert "import xtquant.xttrader" not in text
        assert "from xtquant import xttrader" not in text


def test_roadmap_contains_stage24_and_stage25():
    text = Path("docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段二十四" in text and "QMT 实机数据联调与真实缓存质量验证" in text
    assert "阶段二十五" in text and "Daily Pipeline 真实缓存数据默认化" in text


def test_sync_all_ps1_not_modified_exists():
    assert Path("scripts/sync_all.ps1").exists()
