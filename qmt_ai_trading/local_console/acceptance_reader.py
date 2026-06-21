from __future__ import annotations
import json
from pathlib import Path

def read_json(path):
    p=Path(path)
    if not p.exists(): return {'status':'UNAVAILABLE','source':str(p),'data':{},'summary':'missing','warnings':[f'{p} unavailable']}
    try: return {'status':'PASS','source':str(p),'data':json.loads(p.read_text(encoding='utf-8')),'summary':'loaded','warnings':[]}
    except Exception as exc: return {'status':'UNAVAILABLE','source':str(p),'data':{},'summary':str(exc),'warnings':[str(exc)]}
