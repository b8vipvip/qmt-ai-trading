from __future__ import annotations
import json
from pathlib import Path
SENSITIVE=('env','token','key','secret','credential')
def _blocked(path):
    s=str(path).replace('\\','/').lower(); n=Path(path).name.lower()
    return any(x in n for x in SENSITIVE) or '/market_data/' in s or '/logs/' in s and not s.endswith('.log')
def strip_bom(text): return text.lstrip('\ufeff')
def clean_nul_text(text): return text.replace('\x00','')
def clean_replacement_chars_for_display(text): return text.replace('\ufffd','').replace('��','')
def _score(t): return t.count('\ufffd')+t.count('\x00')*3
def decode_text_file_auto(path):
    p=Path(path)
    if _blocked(p): return {'text':'','encoding_used':'blocked','warnings':['blocked sensitive/runtime path']}
    data=p.read_bytes()[:512000]
    best=('','utf-8-replace',10**9,[])
    for enc in ('utf-8-sig','utf-8','utf-16','utf-16le','utf-16be'):
        try:
            txt=clean_nul_text(strip_bom(data.decode(enc)))
            sc=_score(txt)
            if sc < best[2]: best=(txt,enc,sc,[])
            if sc==0: break
        except UnicodeError: pass
    else:
        txt=clean_nul_text(strip_bom(data.decode('utf-8',errors='replace'))); best=(txt,'utf-8-replace',_score(txt),[])
    txt,enc,_,warns=best
    if '\ufffd' in txt or '��' in txt: warns.append('encoding warning: replacement char detected')
    return {'text':clean_nul_text(strip_bom(txt)),'encoding_used':enc,'warnings':warns,'contains_replacement_char':'\ufffd' in txt or '��' in txt,'contains_nul':'\x00' in txt}
def summarize_for_shell(text, max_chars=1000): return clean_replacement_chars_for_display(clean_nul_text(strip_bom(str(text))))[:max_chars]
def safe_read_json_or_markdown(path_json, path_markdown=None):
    warnings=[]; p=Path(path_json)
    if p.exists():
        d=decode_text_file_auto(p); warnings+=d.get('warnings',[])
        try: return {'data':json.loads(d['text']),'summary':summarize_for_shell(d['text']),'source':str(p),'status':'PASS','warnings':warnings,'encoding_used':d.get('encoding_used')}
        except Exception as e: warnings.append(f'json read failed: {e}')
    if path_markdown and Path(path_markdown).exists():
        d=decode_text_file_auto(path_markdown); warnings+=d.get('warnings',[])
        return {'data':{},'summary':summarize_for_shell(d['text']),'source':str(path_markdown),'status':'WARN','warnings':warnings,'encoding_used':d.get('encoding_used')}
    return {'data':{},'summary':'UNAVAILABLE','source':str(p),'status':'UNAVAILABLE','warnings':warnings or ['report unavailable'],'encoding_used':''}
def read_latest_validation_for_shell(log_dir):
    d=Path(log_dir)
    if not d.exists(): return {'path':str(d),'summary':'UNAVAILABLE','status':'UNAVAILABLE','warnings':['validation_logs missing']}
    files=sorted(d.glob('stage*_validation_*.log'), key=lambda p:(p.stat().st_mtime,p.name), reverse=True)
    if not files: return {'path':str(d),'summary':'UNAVAILABLE','status':'UNAVAILABLE','warnings':['no validation log found']}
    raw=files[0].read_bytes(); sample=raw[:6000]+(b'\n...TRUNCATED...\n'+raw[-6000:] if len(raw)>12000 else b'')
    tmp=files[0].with_suffix(files[0].suffix+'.sample.tmp')
    try:
        tmp.write_bytes(sample); dct=decode_text_file_auto(tmp)
    finally:
        try: tmp.unlink()
        except OSError: pass
    return {'path':str(files[0]),'summary':summarize_for_shell(dct['text'],1200),'status':'PASS','warnings':dct.get('warnings',[]),'encoding_used':dct.get('encoding_used'),'contains_nul':'\x00' in dct.get('text',''),'contains_replacement_char':'\ufffd' in dct.get('text','') or '��' in dct.get('text','')}
