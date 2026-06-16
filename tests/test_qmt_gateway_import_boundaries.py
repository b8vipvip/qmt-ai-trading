# -*- coding: utf-8 -*-
import os, re, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN_FILES = ['qmt_generate_signal_rotation.py','qmt_daily_shadow_pipeline.py','qmt_plan_order_dryrun_v2.py','qmt_scan_etf_universe.py','qmt_compare_etf_pools.py']
LEGACY_UNSAFE_SCRIPTS = ['qmt_plan_order_dryrun.py','qmt_plan_order_dryrun_test_buy.py','qmt_query_readonly.py']
ALLOWED_IMPORT_FILES = set(['qmt_gateway/data_client.py','qmt_gateway/trade_readonly_client.py'])
XTQUANT_PATTERN = r'from xtquant|import xtquant|XtQuantTrader|StockAccount'
LEGACY_CLEANUP_MARKERS = [
    'Move-LegacyUnsafeScripts',
    'legacy_unsafe_scripts',
    'git ls-files --error-unmatch',
    '已隔离旧版 QMT 直连脚本',
]
class ImportBoundaryTest(unittest.TestCase):
    def _read(self, rel):
        with open(os.path.join(ROOT, rel), encoding='utf-8-sig') as h: return h.read()
    def _find_xtquant_offenders(self, root):
        offenders=[]
        for dirpath,_,files in os.walk(root):
            if '.git' in dirpath.split(os.sep): continue
            for fn in files:
                if fn.endswith('.py'):
                    path=os.path.join(dirpath,fn)
                    rel=os.path.relpath(path,root).replace(os.sep,'/')
                    with open(path, encoding='utf-8-sig') as h:
                        text=h.read()
                    if re.search(XTQUANT_PATTERN, text) and rel not in ALLOWED_IMPORT_FILES:
                        if rel.startswith('tests/') or rel in ['qmt_backtest_ma.py','qmt_generate_signal_ma.py','qmt_validate_ma.py','qmt_stable_ma.py','qmt_optimize_ma.py','qmt_test_kline.py','qmt_backtest_etf_rotation.py'] or rel.startswith('data_tools/'):
                            continue
                        offenders.append(rel)
        return offenders
    def test_strategy_and_ai_no_xtquant_imports(self):
        for folder in ['strategies','ai_tools']:
            base=os.path.join(ROOT,folder)
            if not os.path.isdir(base): continue
            for dirpath,_,files in os.walk(base):
                for fn in files:
                    if fn.endswith('.py'):
                        rel=os.path.relpath(os.path.join(dirpath,fn),ROOT).replace(os.sep,'/')
                        self.assertNotRegex(self._read(rel), XTQUANT_PATTERN, rel)
    def test_core_files_no_direct_xt_trader(self):
        for rel in FORBIDDEN_FILES:
            self.assertNotRegex(self._read(rel), XTQUANT_PATTERN, rel)
    def test_legacy_unsafe_script_list_is_explicit(self):
        self.assertEqual(['qmt_plan_order_dryrun.py','qmt_plan_order_dryrun_test_buy.py','qmt_query_readonly.py'], LEGACY_UNSAFE_SCRIPTS)
    def test_update_script_quarantines_legacy_scripts_before_tests(self):
        text = self._read('update_qmt_project.ps1')
        for script in LEGACY_UNSAFE_SCRIPTS:
            self.assertIn(script, text)
        for marker in LEGACY_CLEANUP_MARKERS:
            self.assertIn(marker, text)
        self.assertLess(text.index('Move-LegacyUnsafeScripts $backupRoot'), text.index('Invoke-Checked "unit_tests"'))
    def test_legacy_scripts_are_not_import_boundary_allowlisted(self):
        self.assertTrue(set(LEGACY_UNSAFE_SCRIPTS).isdisjoint(ALLOWED_IMPORT_FILES))
    def test_import_boundary_detects_root_direct_xtquant_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, 'unsafe_root_script.py'), 'w', encoding='utf-8') as h:
                h.write('from xtquant.xttrader import XtQuantTrader\n')
            self.assertEqual(['unsafe_root_script.py'], self._find_xtquant_offenders(tmp))
    def test_qmt_plan_order_dryrun_v2_uses_gateway_not_direct_trader(self):
        text = self._read('qmt_plan_order_dryrun_v2.py')
        self.assertIn('from qmt_gateway.gateway import QmtGateway', text)
        self.assertNotRegex(text, r'from xtquant|import xtquant|XtQuantTrader|StockAccount')
    def test_only_gateway_imports_xtquant(self):
        self.assertEqual([], self._find_xtquant_offenders(ROOT))
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
