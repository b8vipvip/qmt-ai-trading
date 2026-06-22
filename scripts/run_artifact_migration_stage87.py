from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.common.artifact_migration import run_artifact_migration_stage87
p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_artifact_migration_stage87')
a=p.parse_args(); print(json.dumps(run_artifact_migration_stage87(a.repo_root,a.output_dir),ensure_ascii=False,indent=2,sort_keys=True))
