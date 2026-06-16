# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .data_client import QmtDataClient
from .trade_readonly_client import QmtTradeReadonlyClient
from .trade_executor_disabled import DisabledTradeExecutor
from .safety import validate_config_safe
class QmtGateway(object):
    def __init__(self, cfg):
        validate_config_safe(cfg or {})
        self.cfg = cfg or {}
        self.data = QmtDataClient()
        self.trade_readonly = QmtTradeReadonlyClient(self.cfg)
        self.executor = DisabledTradeExecutor()
