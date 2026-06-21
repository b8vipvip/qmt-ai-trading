from __future__ import annotations
import json
from pathlib import Path

def read_text(path: Path) -> str:
    try: return path.read_text(encoding='utf-8')
    except FileNotFoundError: return ''
    except UnicodeDecodeError: return path.read_text(encoding='utf-8', errors='replace')

def read_json(path: Path) -> dict:
    if not path.exists(): return {'status':'UNAVAILABLE','source':str(path),'data':{},'summary':'missing'}
    try: return {'status':'PASS','source':str(path),'data':json.loads(path.read_text(encoding='utf-8')),'summary':'loaded'}
    except Exception as exc: return {'status':'UNAVAILABLE','source':str(path),'data':{},'summary':f'failed: {exc}'}
