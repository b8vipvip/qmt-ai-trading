from qmt_ai_trading.market_gateway import XtDataLiveReadOnlyConfig, XtDataLiveReadOnlyProvider

def test_default_fallback_is_safe():
    cfg = XtDataLiveReadOnlyConfig()
    assert cfg.enabled is False
    assert cfg.allow_import_xtdata is False
    provider = XtDataLiveReadOnlyProvider(cfg)
    status = provider.get_status()
    assert status['status'] == 'FALLBACK_TO_SANDBOX'
    assert status['real_market_data'] is False
    assert status['sandbox_fallback'] is True
    assert status['read_only'] is True
    assert status['no_xttrader'] is True
    assert status['no_order_submitted'] is True
    assert status['no_account_query'] is True

def test_snapshots_and_bars_fallback():
    p = XtDataLiveReadOnlyProvider()
    assert p.get_snapshot(['510300.SH'])['snapshots']
    assert p.get_bars('510300.SH','1d',3)['bars']


def test_enabled_params_use_real_xtdata_provider(monkeypatch):
    import sys, types
    fake_xtdata = types.SimpleNamespace(
        get_full_tick=lambda symbols: {symbols[0]: {'lastPrice': 3.14}},
        get_market_data=lambda *a, **k: {'close': [3.14]},
    )
    fake_pkg = types.SimpleNamespace(xtdata=fake_xtdata)
    monkeypatch.setitem(sys.modules, 'xtquant', fake_pkg)
    cfg = XtDataLiveReadOnlyConfig(
        enabled=True,
        allow_import_xtdata=True,
        allow_real_market_data=True,
        allow_connect_miniqmt=True,
        symbols=['510300.SH'],
        limit=20,
    )
    provider = XtDataLiveReadOnlyProvider(cfg)
    status = provider.get_status()
    assert status['real_market_data'] is True
    assert status['sandbox_fallback'] is False
    assert status['xtdata_imported'] is True
    assert status['mini_qmt_connected'] is True
    assert status['no_xttrader'] is True
    assert provider.get_snapshot(['510300.SH'])['real_market_data'] is True
    assert provider.get_bars('510300.SH', '1d', 20)['real_market_data'] is True



def _install_fake_pandas_numpy(monkeypatch):
    import sys, types, math

    class Timestamp:
        def __init__(self, value): self.value = value
        def isoformat(self): return self.value.replace(' ', 'T')

    class DataFrame:
        def __init__(self, data): self.data = data; self.columns = list(data.keys())
        def copy(self): return DataFrame({k: list(v) for k, v in self.data.items()})
        def reset_index(self):
            self.data = {'index': list(range(len(next(iter(self.data.values()), [])))), **self.data}
            self.columns = list(self.data.keys())
            return self
        def to_dict(self, orient='records'):
            assert orient == 'records'
            size = len(next(iter(self.data.values()), [])) if self.data else 0
            return [{k: v[i] for k, v in self.data.items()} for i in range(size)]

    class Series:
        def __init__(self, data): self.data = data
        def to_dict(self): return dict(self.data)

    class Generic:
        def __init__(self, value): self.value = value
        def item(self): return self.value

    class NdArray:
        def __init__(self, values): self.values = values
        def tolist(self): return list(self.values)

    fake_pd = types.SimpleNamespace(
        DataFrame=DataFrame,
        Series=Series,
        Timestamp=Timestamp,
        isna=lambda value: isinstance(value, float) and math.isnan(value),
    )
    fake_np = types.SimpleNamespace(
        generic=Generic,
        ndarray=NdArray,
        float64=lambda value: Generic(float(value)),
        int64=lambda value: Generic(int(value)),
        array=lambda values: NdArray(values),
        inf=float('inf'),
    )
    monkeypatch.setitem(sys.modules, 'pandas', fake_pd)
    monkeypatch.setitem(sys.modules, 'numpy', fake_np)
    return fake_pd, fake_np


def test_json_safe_converts_dataframe_series_numpy_timestamp(monkeypatch):
    import math
    from qmt_ai_trading.common.json_safe import json_safe
    pd, np = _install_fake_pandas_numpy(monkeypatch)

    ts = pd.Timestamp('2026-06-22 09:30:00')
    df = pd.DataFrame({'time': [ts], 'close': [np.float64(3.14)], 'bad': [float('nan')]})
    assert json_safe(df) == [{'index': 0, 'time': ts.isoformat(), 'close': 3.14, 'bad': None}]
    assert json_safe(pd.Series({'time': ts, 'n': np.int64(7)})) == {'time': ts.isoformat(), 'n': 7}
    assert json_safe(np.array([1, np.inf])) == [1, None]
    assert json_safe({'x': {1, 2}})['x'] in ([1, 2], [2, 1])


def test_real_xtdata_bars_dataframe_is_list_of_dicts(monkeypatch):
    import sys, types
    pd, _np = _install_fake_pandas_numpy(monkeypatch)

    fake_xtdata = types.SimpleNamespace(
        get_full_tick=lambda symbols: {symbols[0]: {'lastPrice': 3.14}},
        get_market_data_ex=lambda *a, **k: {'510300.SH': pd.DataFrame({
            'time': [pd.Timestamp('2026-06-22 09:30:00')],
            'open': [1.0], 'high': [2.0], 'low': [0.5], 'close': [1.5], 'volume': [100], 'amount': [200.0]
        })},
    )
    monkeypatch.setitem(sys.modules, 'xtquant', types.SimpleNamespace(xtdata=fake_xtdata))
    provider = XtDataLiveReadOnlyProvider(XtDataLiveReadOnlyConfig(
        enabled=True, allow_import_xtdata=True, allow_real_market_data=True, allow_connect_miniqmt=True, symbols=['510300.SH'], limit=20,
    ))
    res = provider.get_bars('510300.SH', '1d', 20)
    assert res['real_market_data'] is True
    assert isinstance(res['bars'], list)
    assert isinstance(res['bars'][0], dict)
    assert res['bars'][0]['time'] == '2026-06-22T09:30:00'
    assert res['bars'][0]['no_order_submitted'] is True
