from __future__ import annotations

import importlib.util
from pathlib import Path

from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.qmt_diagnostics import build_qmt_data_quality_report, calibrate_qmt_bar_fields, format_qmt_data_quality_report, format_qmt_runtime_info, inspect_qmt_raw_schema, inspect_qmt_runtime
from qmt_ai_trading.datahub.qmt_field_mapping import map_qmt_record_fields, resolve_qmt_field
from qmt_ai_trading.datahub.qmt_provider import normalize_qmt_raw_records, qmt_record_to_bar


class FakeXtData:
    __file__ = "/fake/xtdata.py"

    def __init__(self) -> None:
        self.connected = False

    def connect(self):
        self.connected = True
        return True

    def get_market_data_ex(self):
        return None


def test_inspect_qmt_runtime_without_xtdata_does_not_crash():
    info = inspect_qmt_runtime(xtdata_module=None)
    assert isinstance(info.xtdata_available, bool)


def test_inspect_qmt_runtime_fake_available():
    info = inspect_qmt_runtime(xtdata_module=FakeXtData())
    assert info.xtdata_available is True
    assert info.xtdata_module_path == "/fake/xtdata.py"


def test_inspect_qmt_runtime_try_connect_calls_fake():
    fake = FakeXtData()
    info = inspect_qmt_runtime(try_connect=True, xtdata_module=fake)
    assert fake.connected is True
    assert info.connect_success is True


def test_inspect_qmt_raw_schema_dict_and_list():
    assert inspect_qmt_raw_schema({"datetime": "2024-01-01", "open": 1, "high": 2, "low": 1, "close": 2}).raw_columns
    assert inspect_qmt_raw_schema([{"datetime": "2024-01-01", "open": 1, "high": 2, "low": 1, "close": 2}]).raw_columns


def test_calibrate_qmt_bar_fields_ohlcv():
    c = calibrate_qmt_bar_fields({"datetime": ["2024-01-01"], "open": [1], "high": [2], "low": [1], "close": [2], "volume": [100]})
    assert not c.missing_required_fields
    assert c.mapped_fields["volume"] == "volume"


def test_qmt_field_mapping_aliases():
    r = {"openPrice": 1, "highPrice": 2, "lowPrice": 0.5, "closePrice": 1.5}
    assert resolve_qmt_field(r, "open") == 1
    assert map_qmt_record_fields(r)["high"] == 2


def test_normalize_qmt_raw_records_fake_records():
    bars = normalize_qmt_raw_records([{"date": "2024-01-01", "openPrice": 1, "highPrice": 2, "lowPrice": 1, "closePrice": 2, "vol": 100}], "510300.SH", "1d")
    assert len(bars) == 1
    assert bars[0].open == 1.0


def test_qmt_record_to_bar_returns_bar():
    bar = qmt_record_to_bar({"datetime": "2024-01-01", "open": 1, "high": 2, "low": 1, "close": 2}, "510300.SH", "1d")
    assert isinstance(bar, MarketBar)


def test_quality_report_row_count_first_last():
    bars = [MarketBar("S", "2024-01-01", 1, 2, 1, 2), MarketBar("S", "2024-01-02", 1, 2, 1, 2)]
    r = build_qmt_data_quality_report(bars, "S", "1d", "2024-01-01", "2024-01-02")
    assert r.row_count == 2
    assert r.first_datetime == "2024-01-01"
    assert r.last_datetime == "2024-01-02"


def test_quality_report_duplicate_datetime():
    bars = [MarketBar("S", "2024-01-01", 1, 2, 1, 2), MarketBar("S", "2024-01-01", 1, 2, 1, 2)]
    assert build_qmt_data_quality_report(bars, "S", "1d", "", "").duplicate_datetime_count == 1


def test_format_qmt_runtime_info_string():
    assert "QMT Runtime Info" in format_qmt_runtime_info(inspect_qmt_runtime(xtdata_module=FakeXtData()))


def test_format_qmt_data_quality_report_string():
    report = build_qmt_data_quality_report([], "S", "1d", "", "")
    assert "QMT Data Quality Report" in format_qmt_data_quality_report(report)


def _import_script(path: str):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_check_qmt_data_provider_imports_main():
    assert callable(_import_script("scripts/check_qmt_data_provider.py").main)


def test_qmt_fetch_sample_calibrate_imports_main():
    assert callable(_import_script("scripts/qmt_fetch_sample_calibrate.py").main)


def test_sync_all_ps1_not_modified_marker_exists():
    assert Path("scripts/sync_all.ps1").exists()
