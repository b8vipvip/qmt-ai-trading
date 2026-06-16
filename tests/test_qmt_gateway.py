# -*- coding: utf-8 -*-
import unittest
from qmt_gateway.data_client import QmtDataClient
from qmt_gateway.trade_readonly_client import QmtTradeReadonlyClient
from qmt_gateway.trade_executor_disabled import DisabledTradeExecutor
from qmt_gateway.safety import redact_account_id

class QmtGatewayTest(unittest.TestCase):
    def test_import_clients(self):
        self.assertIsNotNone(QmtDataClient)
        self.assertIsNotNone(QmtTradeReadonlyClient)
    def test_disabled_executor_rejects(self):
        ex = DisabledTradeExecutor()
        with self.assertRaises(RuntimeError): ex.order_stock()
        with self.assertRaises(RuntimeError): ex.cancel_order_stock()
    def test_redact_account(self):
        self.assertEqual(redact_account_id('88123416'), '88***16')
        self.assertNotIn('1234', redact_account_id('88123416'))
if __name__ == '__main__': unittest.main()
