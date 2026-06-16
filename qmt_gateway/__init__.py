# -*- coding: utf-8 -*-
"""Read-only QMT gateway package."""
from __future__ import absolute_import

from .gateway import QmtGateway
from .trade_executor_disabled import DisabledTradeExecutor

__all__ = ["QmtGateway", "DisabledTradeExecutor"]
