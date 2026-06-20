from __future__ import annotations
import json
from pathlib import Path
from .dashboard_models import *
SENSITIVE=['.env','token','key','secret','credential']
def _blocked(path):
    s=str(path).replace('\\','/').lower(); n=Path(path).name.lower()
    return any(x in n for x in SENSITIVE) or '/market_data/' in s or s.endswith(('.db','.sqlite','.duckdb'))
def strip_bom(text: str)->str: return text.lstrip('\ufeff')
def clean_nul_text(text: str)->str: return text.replace('\x00','')
def clean_replacement_chars(text: str)->str: return text.lstrip('\ufffd').replace('��','')
def _score(txt): return txt.count('\ufffd')+txt.count('\x00')*2
def _decode_bytes(data: bytes):
    best=(data.decode('utf-8',errors='replace'),'utf-8-replace')
    for enc in ('utf-8-sig','utf-8','utf-16','utf-16le','utf-16be'):
        try:
            cand=data.decode(enc)
            if _score(cand) < _score(best[0]): best=(cand,enc)
            if _score(cand)==0: return clean_nul_text(strip_bom(cand)),enc
        except UnicodeError: pass
    txt,enc=best
    return clean_nul_text(strip_bom(txt)),enc
def decode_text_file_auto(path, max_bytes: int|None=None):
    p=Path(path); data=p.read_bytes(); data=data if max_bytes is None else data[:max_bytes]
    txt,enc=_decode_bytes(data)
    if txt.startswith('\ufffd') or txt.startswith('��') or '\ufffd' in txt:
        for enc2 in ('utf-16','utf-16le','utf-16be','utf-8-sig','utf-8'):
            try:
                cand=clean_nul_text(strip_bom(data.decode(enc2)))
                if _score(cand) < _score(txt): txt,enc=cand,enc2
            except UnicodeError: pass
    return clean_nul_text(strip_bom(txt)),enc
def read_json_evidence(stage,path):
    p=Path(path)
    if _blocked(p): return LocalConsoleDashboardEvidence(stage=stage,path=str(p),status=LocalConsoleDashboardStatus.FAIL,severity=LocalConsoleDashboardSeverity.CRITICAL,summary='BLOCKED sensitive/runtime path',critical_count=1)
    if not p.exists(): return LocalConsoleDashboardEvidence(stage=stage,path=str(p),summary='UNAVAILABLE missing json report')
    try:
        txt,_=decode_text_file_auto(p,512000); data=json.loads(txt); summary=data.get('summary',{}) if isinstance(data,dict) else {}
        crit=int(summary.get('critical_count', data.get('critical_count',0) if isinstance(data,dict) else 0) or 0)
        warns=list(data.get('warnings',[]) if isinstance(data,dict) else [])
        blocks=list(data.get('blocking_reasons',[]) if isinstance(data,dict) else [])
        return LocalConsoleDashboardEvidence(stage=stage,title=stage,path=str(p),status=LocalConsoleDashboardStatus.PASS,severity=LocalConsoleDashboardSeverity.INFO,summary=str(summary or data.get('decision','json report readable')),decision=str(data.get('decision','')),critical_count=crit,warning_count=len(warns),blocking_reason_count=len(blocks),warnings=warns,blocking_reasons=blocks,metadata={'data':data})
    except Exception as e:
        return LocalConsoleDashboardEvidence(stage=stage,path=str(p),status=LocalConsoleDashboardStatus.WARN,summary=f'WARN json read failed: {e}')
def read_latest_validation_detail(log_dir):
    d=Path(log_dir)
    if not d.exists(): return {'path':str(d),'status':'UNAVAILABLE','encoding':'','summary':'UNAVAILABLE validation_logs missing','warnings':['validation_logs missing'],'contains_nul':False,'contains_replacement_char':False}
    files=sorted(d.glob('stage*_validation_*.log'), key=lambda p:(p.stat().st_mtime, p.name), reverse=True)[:1]
    if not files: return {'path':str(d),'status':'UNAVAILABLE','encoding':'','summary':'UNAVAILABLE no validation log found','warnings':['no validation log found'],'contains_nul':False,'contains_replacement_char':False}
    p=files[0]
    try:
        raw=p.read_bytes(); sample=raw[:6000]+(b'\n...TRUNCATED...\n'+raw[-6000:] if len(raw)>12000 else b'')
        txt,enc=_decode_bytes(sample); txt=clean_nul_text(strip_bom(txt)); warns=[]
        if '\ufffd' in txt or '��' in txt: warns.append('replacement char detected after fallback decode')
        txt=clean_replacement_chars(txt)
        return {'path':str(p),'status':'PASS','encoding':enc,'head':txt[:3000],'tail':txt[-3000:],'summary':txt[:1200],'warnings':warns,'contains_nul':'\x00' in txt,'contains_replacement_char':'\ufffd' in txt or '��' in txt}
    except Exception as e:
        return {'path':str(p),'status':'WARN','encoding':'','summary':f'WARN validation read failed: {e}','warnings':[str(e)],'contains_nul':False,'contains_replacement_char':False}
