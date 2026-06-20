from __future__ import annotations
import json, re
from datetime import datetime, timezone
from pathlib import Path
from .binding_models import *
SENSITIVE=('env','token','key','secret','credential')

def _blocked(path):
    s=str(path).replace('\\','/').lower(); n=Path(path).name.lower()
    return any(x in n for x in SENSITIVE) or '/market_data/' in s or '/reports/' in s or ('/logs/' in s and 'validation_logs/' not in s)
def strip_bom(text): return str(text).lstrip('\ufeff')
def clean_nul_text(text): return str(text).replace('\x00','')
def _mojibake_score(t): return t.count('\ufffd')*5+t.count('�')*5+t.count('\x00')*10+len(re.findall(r'[锟斤拷]{2,}',t))*5
def clean_mojibake_for_display(text, max_chars=1200):
    t=clean_nul_text(strip_bom(text))
    if _mojibake_score(t)>20 or t.count('\ufffd')>5:
        return 'encoding_warning=True; display suppressed to avoid mojibake.'
    return t.replace('\ufffd','').replace('��','')[:max_chars]
def decode_text_file_auto(path):
    p=Path(path); warnings=[]
    if _blocked(p): return {'text':'','encoding':'blocked','warnings':['blocked sensitive/runtime path']}
    data=p.read_bytes()[:512000]
    best=None
    for enc in ('utf-8-sig','utf-8','utf-16','utf-16le','utf-16be'):
        try:
            txt=clean_nul_text(strip_bom(data.decode(enc)))
            cand=( _mojibake_score(txt), txt, enc)
            if best is None or cand[0]<best[0]: best=cand
            if cand[0]==0: break
        except UnicodeError: continue
    if best is None:
        txt=clean_nul_text(strip_bom(data.decode('utf-8',errors='replace'))); best=(_mojibake_score(txt),txt,'utf-8-replace')
    score,txt,enc=best
    if '\ufffd' in txt or '�' in txt: warnings.append('encoding_warning=True replacement char detected')
    if score>20: warnings.append('encoding_warning=True mojibake suspected')
    return {'text':clean_nul_text(strip_bom(txt)),'encoding':enc,'warnings':warnings,'contains_nul':'\x00' in txt,'contains_replacement_char':'\ufffd' in txt or '�' in txt}
def read_json_tolerant(path):
    d=decode_text_file_auto(path)
    return {'data':json.loads(d['text']),'summary':clean_mojibake_for_display(d['text']),'encoding':d['encoding'],'warnings':d['warnings'],'fallback_used':False,'source':str(path),'status':'PASS'}
def read_markdown_tolerant(path):
    d=decode_text_file_auto(path)
    return {'data':{},'summary':clean_mojibake_for_display(d['text']),'encoding':d['encoding'],'warnings':d['warnings'],'fallback_used':True,'source':str(path),'status':'WARN'}
def read_json_or_markdown_tolerant(path_json, path_markdown=None):
    warnings=[]; p=Path(path_json)
    if p.exists():
        try: return read_json_tolerant(p)
        except Exception as e: warnings.append(f'json read failed: {e}')
    if path_markdown and Path(path_markdown).exists():
        r=read_markdown_tolerant(path_markdown); r['warnings']=warnings+r['warnings']; return r
    return {'data':{},'summary':'UNAVAILABLE','encoding':'','warnings':warnings+['source unavailable'],'fallback_used':False,'source':str(p),'status':'UNAVAILABLE'}
def read_latest_validation_summary(log_dir):
    d=Path(log_dir)
    if not d.exists(): return {'path':str(d),'summary':'UNAVAILABLE','status':'UNAVAILABLE','warnings':['validation_logs missing']}
    files=sorted(d.glob('stage*_validation_*.log'), key=lambda p:(p.stat().st_mtime,p.name), reverse=True)
    if not files: return {'path':str(d),'summary':'UNAVAILABLE','status':'UNAVAILABLE','warnings':['no validation log found']}
    raw=files[0].read_bytes(); sample=raw[:6000]+(b'\n...TRUNCATED...\n'+raw[-6000:] if len(raw)>12000 else b'')
    txt=''
    for enc in ('utf-8-sig','utf-8','utf-16','utf-16le','utf-16be'):
        try: txt=sample.decode(enc); break
        except UnicodeError: pass
    if not txt: txt=sample.decode('utf-8',errors='replace')
    return {'path':str(files[0]),'summary':clean_mojibake_for_display(txt,1200),'status':'PASS','warnings':[],'encoding':'sample-auto'}
def build_data_source_entry(source_path, source_type, target_section_id, read_result=None):
    read_result=read_result or {}; st=read_result.get('status','UNAVAILABLE')
    return LocalConsoleDataSource(str(source_path), source_type, target_section_id, LocalConsoleBindingStatus.PASS if st=='PASS' else LocalConsoleBindingStatus.WARN if st=='WARN' else LocalConsoleBindingStatus.UNAVAILABLE, LocalConsoleBindingSeverity.INFO if st=='PASS' else LocalConsoleBindingSeverity.WARN, read_result.get('encoding',''), bool(read_result.get('fallback_used')), True, True, True, list(read_result.get('warnings',[])))
def build_data_bundle(bindings, latest_validation=None, warnings=None, blocking=None):
    data={b.source.target_section_id:b.payload for b in bindings}
    return {'metadata':{'stage':'Stage66','read_only':True,'dry_run_only':True,'no_trade_authorization':True,'generated_at':datetime.now(timezone.utc).isoformat(),'source_count':len(bindings)},'dashboard':data.get('#dashboard-overview-section',{}),'stage_status':data.get('#stage-status-section',{}),'latest_validation':latest_validation or {},'warnings':{'items':warnings or []},'blocking_reasons':{'items':blocking or []},'manifest':data.get('#manifest-section',{}),'scheduler_preview':data.get('#scheduler-preview-section',{}),'safety_boundary':data.get('#safety-boundary-section',{}),'api_capability':data.get('#api-capability-section',{}),'report_list':data.get('#report-list-section',{}),'detail_filters':data.get('#detail-filter-section',{}),'placeholders':{},'warnings_summary':warnings or []}
