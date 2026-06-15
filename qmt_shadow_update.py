# -*- coding: utf-8 -*-
"""Update the virtual shadow ledger; never submits real orders."""
from __future__ import print_function
import json, os
from qmt_config import load_config
from shadow_trading.shadow_portfolio import update_shadow_portfolio
ROOT = os.path.dirname(os.path.abspath(__file__))
def _load(path):
    with open(path, "r", encoding="utf-8") as handle: return json.load(handle)
def main():
    cfg = load_config(); paths = cfg.get("paths", {}); shadow_dir = paths.get("shadow_dir", os.path.join(ROOT, "shadow"))
    result = update_shadow_portfolio(cfg, _load(paths.get("order_plan_file", os.path.join(ROOT,"signals","order_plan.json"))), _load(paths.get("target_signal_file", os.path.join(ROOT,"signals","target_signal.json"))), shadow_dir)
    print("[OK] shadow total_asset:", result["total_asset"]); return result
if __name__ == "__main__": main()
