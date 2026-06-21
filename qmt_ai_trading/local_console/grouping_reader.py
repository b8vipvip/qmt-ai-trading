from __future__ import annotations
import json
from pathlib import Path

def read_json(path):
    p=Path(path)
    if not p.exists(): return {'status':'MISSING','source':str(p),'summary':'missing','warnings':[f'{p} unavailable'],'data':{}}
    try:
        return {'status':'PASS','source':str(p),'summary':'loaded','warnings':[],'data':json.loads(p.read_text(encoding='utf-8'))}
    except Exception as exc:
        return {'status':'ERROR','source':str(p),'summary':str(exc),'warnings':[str(exc)],'data':{}}
