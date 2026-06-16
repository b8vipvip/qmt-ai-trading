# -*- coding: utf-8 -*-
from __future__ import absolute_import
class DisabledTradeExecutor(object):
    def order_stock(self, *args, **kwargs):
        raise RuntimeError("真实下单执行器当前禁用：DisabledTradeExecutor")
    def cancel_order_stock(self, *args, **kwargs):
        raise RuntimeError("真实撤单执行器当前禁用：DisabledTradeExecutor")
