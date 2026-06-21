from __future__ import annotations
import json
from pathlib import Path

def write_json(path: Path, data: dict | list):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def write_md(path: Path, title: str, data: dict):
    lines = [
        f'# {title}',
        '',
        'dry_run=true',
        'not_live_trading=true',
        'research_only=true',
        'no_order_submitted=true',
        'no_qmt_trader_api=true',
        'requires_risk_gate=true',
        'requires_human_approval=true',
        '',
    ]
    if data.get('warnings'):
        lines += ['## Warnings', *[f'- {w}' for w in data['warnings']], '']
    lines += ['## Summary', data.get('summary', 'Stage81 Agent 投研报告，仅供研究复核，不能作为实盘依据。')]
    path.write_text('\n'.join(lines), encoding='utf-8')
