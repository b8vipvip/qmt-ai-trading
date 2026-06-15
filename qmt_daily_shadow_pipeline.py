# -*- coding: utf-8 -*-
"""One-click, virtual-only daily pipeline."""
from __future__ import print_function
import datetime, os, subprocess, sys
ROOT=os.path.dirname(os.path.abspath(__file__))
STEPS=[("data_tools.market_regime",False),("data_tools.etf_rotation_selector",False),("qmt_generate_signal_rotation.py",False),("qmt_plan_order_dryrun_v2.py",False),("qmt_execute_manual_guard.py",False),("qmt_shadow_update.py",False),("ai_tools.ai_daily_reviewer",True),("qmt_collect_diagnostics.py",False)]
def run_step(name, optional=False):
    cmd=[sys.executable,"-m",name] if "." in name and not name.endswith(".py") else [sys.executable,os.path.join(ROOT,name)]
    return subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
def main():
    logs=os.path.join(ROOT,"logs"); os.makedirs(logs,exist_ok=True); path=os.path.join(logs,"daily_shadow_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".log")
    shadow_done=False
    with open(path,"w",encoding="utf-8") as log:
        log.write("Virtual-only pipeline; no real trading.\n")
        for name,optional in STEPS:
            result=run_step(name,optional); log.write("\n=== "+name+" ===\n"+result.stdout)
            if name=="qmt_shadow_update.py" and result.returncode==0: shadow_done=True
            if result.returncode and not optional: break
            if result.returncode and optional: log.write("\n[WARNING] AI review failed; shadow ledger remains recorded.\n")
    return shadow_done
if __name__=="__main__": main()
