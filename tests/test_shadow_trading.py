# -*- coding: utf-8 -*-
import csv, datetime, json, os, tempfile, unittest
from unittest import mock
from shadow_trading.shadow_portfolio import calculate_max_drawdown, update_shadow_portfolio
import qmt_daily_shadow_pipeline as pipeline
import qmt_collect_diagnostics as diagnostics
class ShadowTests(unittest.TestCase):
 def cfg(self): return {'shadow_trading':{'enabled':True,'initial_cash':100000,'slippage_rate':0,'commission_rate':0,'min_commission':0}}
 def plan(self, action='PLAN_BUY', price=10, volume=100): return {'action':action,'stock_code':'510300.SH','plan_price_ref':price,'plan_volume':volume}
 def test_buy_sell_no_action_and_duplicate(self):
  with tempfile.TemporaryDirectory() as d:
   now=datetime.datetime(2026,6,15,10); p=update_shadow_portfolio(self.cfg(),self.plan(),{},d,now); self.assertEqual(100,p['positions']['510300.SH']['volume']); self.assertEqual(1,len(p['trades']))
   p=update_shadow_portfolio(self.cfg(),self.plan(),{},d,now); self.assertEqual(1,len(p['trades']))
   p=update_shadow_portfolio(self.cfg(),self.plan('NO_ACTION',11,0),{},d,now); self.assertEqual(1,len(p['trades'])); self.assertEqual(100100,p['total_asset'])
   p=update_shadow_portfolio(self.cfg(),self.plan('PLAN_SELL',11,100),{},d,now); self.assertEqual(0,p['positions']['510300.SH']['volume']); self.assertEqual(2,len(p['trades']))
 def test_max_drawdown(self): self.assertAlmostEqual(.25,calculate_max_drawdown([100,120,90,110]))
 def test_ai_failure_does_not_undo_shadow_step(self):
  results=[mock.Mock(returncode=0,stdout='ok') for _ in range(6)]+[mock.Mock(returncode=1,stdout='ai failed'),mock.Mock(returncode=0,stdout='ok')]
  with tempfile.TemporaryDirectory() as d, mock.patch.object(pipeline,'ROOT',d), mock.patch.object(pipeline,'run_step',side_effect=results): self.assertTrue(pipeline.main())
 def test_diagnostic_shadow_status(self):
  with tempfile.TemporaryDirectory() as d, mock.patch.object(diagnostics,'ROOT',d):
   os.makedirs(os.path.join(d,'shadow'))
   with open(os.path.join(d,'shadow','portfolio.json'),'w',encoding='utf-8') as h: json.dump({'total_asset':1},h,ensure_ascii=False)
   with open(os.path.join(d,'shadow','equity_curve.csv'),'w',encoding='utf-8') as h: h.write('date,total_asset\n2026-06-15,1\n')
   self.assertTrue(diagnostics.collect_shadow()['started']); self.assertEqual('ETF 影子盘观察期',diagnostics.determine_stage({}, {'code_pull':'未知','unit_tests':'未知','safety_scan':'未知'}, {'dry_run_passed':True},{'pipeline_success':True},diagnostics.collect_shadow())[0])
 def test_modules_do_not_call_real_trading(self):
  for path in ['shadow_trading/shadow_portfolio.py','qmt_shadow_update.py','qmt_daily_shadow_pipeline.py','ai_tools/ai_daily_reviewer.py']:
   with open(path,'r',encoding='utf-8') as h: source=h.read()
   self.assertNotIn('order_'+'stock(',source); self.assertNotIn('cancel_order_'+'stock(',source)
if __name__=='__main__': unittest.main()
