# -*- coding: utf-8 -*-
import unittest
from qmt_generate_project_health_report import build_strategy_validation
class StrategyValidationReportTest(unittest.TestCase):
    def test_build(self):
        r=build_strategy_validation(); self.assertEqual(r['strategy_name'], 'ETF Rotation'); self.assertFalse(r['allow_small_capital_live'])
if __name__ == '__main__': unittest.main()
