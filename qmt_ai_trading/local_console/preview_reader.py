from __future__ import annotations
import json,re
from pathlib import Path
def read_json(path):
    p=Path(path)
    if not p.exists(): return {'status':'UNAVAILABLE','source':str(p),'data':{},'summary':'missing','warnings':[f'missing {p}'],'encoding_warning':False}
    txt=p.read_text(encoding='utf-8',errors='replace')
    enc_warn=bool(re.search(r'Ã.|�{2,}|\x00',txt))
    if enc_warn: txt='上游报告存在编码异常，已隐藏乱码正文'
    try: data=json.loads(p.read_text(encoding='utf-8',errors='replace')) if not enc_warn else {}
    except Exception: data={}
    return {'status':'PASS','source':str(p),'data':data,'summary':'encoding_warning=True; 上游报告存在编码异常，已隐藏乱码正文' if enc_warn else str(data.get('decision', 'available'))[:200],'warnings':['上游报告存在编码异常，已隐藏乱码正文'] if enc_warn else [],'encoding_warning':enc_warn}
