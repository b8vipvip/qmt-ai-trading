# -*- coding: utf-8 -*-
import os, re, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN_FILES = ['qmt_generate_signal_rotation.py','qmt_daily_shadow_pipeline.py','qmt_plan_order_dryrun_v2.py','qmt_scan_etf_universe.py','qmt_compare_etf_pools.py']
ALLOWED_IMPORT_FILES = set(['qmt_gateway/data_client.py','qmt_gateway/trade_readonly_client.py'])
class ImportBoundaryTest(unittest.TestCase):
    def _read(self, rel):
        with open(os.path.join(ROOT, rel), encoding='utf-8') as h: return h.read()
    def test_strategy_and_ai_no_xtquant_imports(self):
        for folder in ['strategies','ai_tools']:
            base=os.path.join(ROOT,folder)
            if not os.path.isdir(base): continue
            for dirpath,_,files in os.walk(base):
                for fn in files:
                    if fn.endswith('.py'):
                        rel=os.path.relpath(os.path.join(dirpath,fn),ROOT).replace(os.sep,'/')
                        self.assertNotRegex(self._read(rel), r'from xtquant|import xtquant|XtQuantTrader|StockAccount', rel)
    def test_core_files_no_direct_xt_trader(self):
        for rel in FORBIDDEN_FILES:
            self.assertNotRegex(self._read(rel), r'from xtquant|import xtquant|XtQuantTrader|StockAccount', rel)
    def test_only_gateway_imports_xtquant(self):
        offenders=[]
        for dirpath,_,files in os.walk(ROOT):
            if '.git' in dirpath.split(os.sep): continue
            for fn in files:
                if fn.endswith('.py'):
                    rel=os.path.relpath(os.path.join(dirpath,fn),ROOT).replace(os.sep,'/')
                    if re.search(r'from xtquant|import xtquant|XtQuantTrader|StockAccount', self._read(rel)) and rel not in ALLOWED_IMPORT_FILES:
                        if rel.startswith('tests/') or rel in ['qmt_backtest_ma.py','qmt_generate_signal_ma.py','qmt_validate_ma.py','qmt_stable_ma.py','qmt_optimize_ma.py','qmt_test_kline.py','qmt_backtest_etf_rotation.py'] or rel.startswith('data_tools/'):
                            continue
                        offenders.append(rel)
        self.assertEqual([], offenders)
    def test_trade_calls_are_not_scattered(self):
        offenders=[]
        allowed=set(['qmt_gateway/trade_executor_disabled.py'])
        for dirpath,_,files in os.walk(ROOT):
            if '.git' in dirpath.split(os.sep): continue
            for fn in files:
                if fn.endswith('.py'):
                    rel=os.path.relpath(os.path.join(dirpath,fn),ROOT).replace(os.sep,'/')
                    if rel in allowed or rel.startswith('tests/'): continue
                    text=self._read(rel)
                    if re.search(r'\.(order_stock|cancel_order_stock)\s*\(', text): offenders.append(rel)
        self.assertEqual([], offenders)
if __name__ == '__main__': unittest.main()
