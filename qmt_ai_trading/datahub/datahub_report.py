from __future__ import annotations
import json
from pathlib import Path
from .real_xtdata_loader import load_stage88_bars, SAFETY
from .real_xtdata_cache import build_real_cache
from .data_quality_gate import evaluate_quality

def _write(path, obj): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8')
def _md(path, title, obj): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(f'# {title}\n\n```json\n'+json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n```\n',encoding='utf-8')
def run_stage88_datahub(repo_root='.', output_dir='local_console_datahub_stage88', symbols=None, period='1d', limit=120, **flags):
    ctx,bars,status=load_stage88_bars(repo_root,symbols,period,limit,**flags)
    cache=build_real_cache(bars,ctx); quality=evaluate_quality(cache)
    out=Path(repo_root)/output_dir; canon=Path(repo_root)/'artifacts/reports/stage88/datahub'
    report={'stage':'Stage88','module':'Data Hub','status':'SUCCESS','datahub_cache_ready':True,'quality_status':quality['status'],'bar_count':cache['bar_count'],**SAFETY, **{k:ctx.get(k) for k in ['fallback_used','mock_data','real_market_data','sandbox_fallback','xtdata_imported','mini_qmt_connected']}}
    contract={'module':'stage88_datahub','api':'/api/v1/stage88/datahub/status','cache_path':str(out/'datahub_real_cache.json'),**report}
    files={'datahub_input_context':ctx,'datahub_real_cache':cache,'datahub_quality_gate':quality,'datahub_status':report,'datahub_report':report,'frontend_datahub_contract':contract}
    for stem,obj in files.items(): _write(out/f'{stem}.json',obj); _md(out/f'{stem}.md',stem,obj); _write(canon/f'{stem}.json',obj); _md(canon/f'{stem}.md',stem,obj)
    return report
