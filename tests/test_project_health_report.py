# -*- coding: utf-8 -*-
import unittest
from qmt_generate_project_health_report import build_project_health, main
class ProjectHealthReportTest(unittest.TestCase):
    def test_build_and_generate(self):
        r=build_project_health(); self.assertIn('live_gate', r); self.assertFalse(r['live_gate']['live_trading_allowed']); main()
if __name__ == '__main__': unittest.main()
