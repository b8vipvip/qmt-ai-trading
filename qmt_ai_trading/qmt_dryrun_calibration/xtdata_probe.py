from __future__ import annotations
import importlib
READONLY_FUNCTIONS=["get_market_data","get_market_data_ex","download_history_data","download_history_data2","get_trading_dates","get_stock_list_in_sector"]
def probe_xtquant_import():
    try: importlib.import_module("xtquant"); return True,"xtquant import available"
    except Exception as e: return False,f"xtquant unavailable: {type(e).__name__}: {e}"
def probe_xtdata_import():
    try: return True, importlib.import_module("xtquant.xtdata"), "xtquant.xtdata import available"
    except Exception as e: return False, None, f"xtdata unavailable: {type(e).__name__}: {e}"
def probe_xtdata_functions(xtdata=None):
    if xtdata is None:
        ok,xtdata,msg=probe_xtdata_import()
        if not ok: return {name:(False,msg) for name in READONLY_FUNCTIONS}
    return {name:(hasattr(xtdata,name), "present" if hasattr(xtdata,name) else "missing") for name in READONLY_FUNCTIONS}
def probe_xtdata_smoke_readonly(provider="mock", max_symbols=5, max_days=90):
    max_symbols=min(int(max_symbols),5); max_days=min(int(max_days),90)
    if provider=="mock": return True,{"provider":"mock","rows":1,"max_symbols":max_symbols,"max_days":max_days},"mock readonly smoke passed"
    ok,xtdata,msg=probe_xtdata_import()
    if not ok: return False,{"provider":provider},msg
    if hasattr(xtdata,"get_trading_dates"):
        try:
            res=xtdata.get_trading_dates("SH", "20260101", "20260110")
            return True,{"provider":provider,"sample_type":type(res).__name__},"xtdata readonly trading dates smoke passed"
        except Exception as e: return False,{"provider":provider},f"xtdata smoke unavailable: {type(e).__name__}: {e}"
    return False,{"provider":provider},"xtdata smoke skipped: no readonly function available"
