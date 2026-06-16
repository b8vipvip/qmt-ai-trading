# -*- coding: utf-8 -*-
import unittest
from risk.risk_report import build_risk_report, write_risk_report
class RiskReportTest(unittest.TestCase):
    def test_build_and_write(self):
        r=build_risk_report({'live_trading_enabled':False}, {'risk_rejections':['x'], 'approved_target_position_pct':0.2}, {'raw_target_position_pct':1.0})
        self.assertTrue(r['exists_100pct_raw_signal']); self.assertFalse(r['live_trading_allowed']); write_risk_report(r, 'reports')
if __name__ == '__main__': unittest.main()
