# -*- coding: utf-8 -*-
from __future__ import absolute_import

class QmtDataClient(object):
    def __init__(self):
        self._xtdata = None
    def _client(self):
        if self._xtdata is None:
            try:
                from xtquant import xtdata
                self._xtdata = xtdata
            except Exception as exc:
                raise RuntimeError("QMT行情模块不可用，请在Windows MiniQMT Python环境运行: %s" % exc)
        return self._xtdata
    def _call(self, name, *args, **kwargs):
        try:
            return getattr(self._client(), name)(*args, **kwargs)
        except Exception as exc:
            raise RuntimeError("QMT行情读取失败[%s]: %s" % (name, exc))
    def safe_call(self, name, *args, **kwargs):
        try:
            return self._call(name, *args, **kwargs)
        except RuntimeError:
            return None
    def get_stock_list_in_sector(self, sector_name):
        return self._call("get_stock_list_in_sector", sector_name)
    def get_instrument_detail(self, stock_code):
        return self._call("get_instrument_detail", stock_code)
    def download_history_data(self, stock_code, period, start_time, end_time):
        return self._call("download_history_data", stock_code, period, start_time, end_time)
    def get_market_data(self, field_list, stock_list, period, start_time, end_time, count=-1, dividend_type="front", fill_data=False):
        return self._call("get_market_data", field_list=field_list, stock_list=stock_list, period=period, start_time=start_time, end_time=end_time, count=count, dividend_type=dividend_type, fill_data=fill_data)
