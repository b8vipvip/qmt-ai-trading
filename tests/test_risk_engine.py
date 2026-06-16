# -*- coding: utf-8 -*-
import unittest
from risk.risk_engine import RiskEngine
from risk.risk_report import build_risk_report
CFG={'live_trading_enabled': False, 'max_single_order_value': 100000, 'risk_engine': {'enabled': True, 'max_total_position_pct': 0.5, 'max_symbol_position_pct': 0.2, 'max_trades_per_day': 2, 'force_manual_confirm': True}}
class RiskEngineTest(unittest.TestCase):
    def test_caps_full_position(self):
        r=RiskEngine(CFG).evaluate({'signal':'BUY_SIGNAL','raw_target_position_pct':1.0}, account={'total_asset':100000,'cash':100000})
        self.assertTrue(r['approved']); self.assertEqual(r['approved_target_position_pct'], 0.2)
    def test_caps_total_position(self):
        cfg=dict(CFG); cfg['risk_engine']=dict(CFG['risk_engine']); cfg['risk_engine']['max_symbol_position_pct']=0.8
        r=RiskEngine(cfg).evaluate({'signal':'BUY_SIGNAL','raw_target_position_pct':1.0}, account={'total_asset':100000,'cash':100000})
        self.assertEqual(r['approved_target_position_pct'], 0.5)
    def test_rejects_trade_frequency(self):
        r=RiskEngine(CFG).evaluate({'signal':'BUY_SIGNAL','raw_target_position_pct':0.1}, account={'total_asset':100000,'cash':100000}, context={'trades_today':2})
        self.assertFalse(r['approved']); self.assertTrue(r['risk_rejections'])
    def test_report_manual_and_live_gate(self):
        r=RiskEngine(CFG).evaluate({'signal':'BUY_SIGNAL','raw_target_position_pct':1.0}, account={'total_asset':100000,'cash':100000})
        report=build_risk_report(CFG, r, r['raw_signal'])
        self.assertTrue(report['manual_confirm_required']); self.assertFalse(report['live_trading_allowed'])
if __name__ == '__main__': unittest.main()
