from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.agents_research import run_agent_research
p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_agent_stage81'); p.add_argument('--mock-agent',action='store_true',default=True); p.add_argument('--real-ai-call',action='store_true',default=False); p.add_argument('--max-agents',type=int,default=7); p.add_argument('--input-source',default='stage80')
a=p.parse_args(); res=run_agent_research(a.repo_root,a.output_dir,a.mock_agent,a.real_ai_call,a.max_agents,a.input_source,True); print(json.dumps(res,ensure_ascii=False,indent=2))
