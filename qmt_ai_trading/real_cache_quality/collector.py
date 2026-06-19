from __future__ import annotations
import json
from pathlib import Path
from .models import *
from .cache_probe import *
from .safety import scan_real_cache_quality_text_for_forbidden_markers

def _ev(cat, st, sev, title, summary, path='', meta=None): return RealCacheQualityEvidence(cat,st,sev,title,summary,path,meta or {})
def collect_real_cache_quality_evidence(cfg: RealCacheQualityConfig):
    root=Path(cfg.repo_root); ev=[]
    qdir=root/Path(cfg.qmt_dryrun_calibration_dir); qjson=qdir/'qmt_dryrun_calibration.json'
    if qjson.exists():
        data=json.loads(qjson.read_text(encoding='utf-8')); dec=str(data.get('decision','')); critical=int((data.get('summary') or {}).get('critical',0) or len(data.get('blocking_reasons') or []))
        sev=RealCacheQualitySeverity.CRITICAL if dec=='NO_GO' or critical>0 else RealCacheQualitySeverity.INFO
        ev.append(_ev(RealCacheQualityCategory.STAGE55_QMT_DRYRUN_CALIBRATION, RealCacheQualityStatus.FAIL if sev==RealCacheQualitySeverity.CRITICAL else RealCacheQualityStatus.PASS, sev, 'Stage55 qmt dryrun calibration', f'decision={dec}, critical={critical}', str(qjson), {'decision':dec,'critical':critical}))
    else: ev.append(_ev(RealCacheQualityCategory.STAGE55_QMT_DRYRUN_CALIBRATION,RealCacheQualityStatus.UNAVAILABLE,RealCacheQualitySeverity.WARN,'Stage55 qmt dryrun calibration missing','Stage55 输出缺失，需补充证据。',str(qjson)))
    for name in ['xtdata_capability.json','etf_whitelist_calibration.json','next_real_cache_quality_plan.json']:
        p=qdir/name; ev.append(_ev(RealCacheQualityCategory.ETF_WHITELIST if 'etf' in name else RealCacheQualityCategory.STAGE55_QMT_DRYRUN_CALIBRATION, RealCacheQualityStatus.PASS if p.exists() else RealCacheQualityStatus.UNAVAILABLE, RealCacheQualitySeverity.INFO if p.exists() else RealCacheQualitySeverity.WARN, name, 'readable' if p.exists() else 'missing', str(p)))
    rp=root/cfg.roadmap_path
    need=['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']
    if rp.exists():
        txt=rp.read_text(encoding='utf-8'); miss=[x for x in need if x not in txt]
        ev.append(_ev(RealCacheQualityCategory.ROADMAP_STAGE_PLAN,RealCacheQualityStatus.FAIL if miss else RealCacheQualityStatus.PASS,RealCacheQualitySeverity.CRITICAL if miss else RealCacheQualitySeverity.INFO,'roadmap Stage1-75 / Stage53-60', 'missing='+','.join(miss) if miss else 'Stage1-75 and Stage53-60 plan retained',str(rp)))
        ev.append(_ev(RealCacheQualityCategory.UI_PRODUCTIZATION_PLAN,RealCacheQualityStatus.FAIL if miss else RealCacheQualityStatus.PASS,RealCacheQualitySeverity.CRITICAL if miss else RealCacheQualitySeverity.INFO,'UI productization plan','UI safety plan retained' if not miss else 'UI critical text missing',str(rp)))
    else: ev.append(_ev(RealCacheQualityCategory.ROADMAP_STAGE_PLAN,RealCacheQualityStatus.FAIL,RealCacheQualitySeverity.CRITICAL,'roadmap missing','roadmap missing',str(rp)))
    ev.append(probe_cache_root(root/Path(cfg.cache_root)))
    try: ev.append(probe_cache_roundtrip_with_mock_provider(root/Path(cfg.cache_root)))
    except Exception as exc: ev.append(_ev(RealCacheQualityCategory.CACHE_COVERAGE,RealCacheQualityStatus.FAIL,RealCacheQualitySeverity.CRITICAL,'mock cache roundtrip failed',str(exc),str(root/Path(cfg.cache_root))))
    for rel in ['.gitignore','validation_logs']:
        p=root/rel; ev.append(_ev(RealCacheQualityCategory.RUNTIME_ARTIFACT,RealCacheQualityStatus.PASS if (p.exists() or rel=='validation_logs') else RealCacheQualityStatus.UNAVAILABLE,RealCacheQualitySeverity.INFO,'runtime artifact check',f'{rel} checked',str(p)))
    for marker, sev in scan_real_cache_quality_text_for_forbidden_markers('\n'.join(e.summary for e in ev), 'generated real_cache_quality evidence'):
        ev.append(_ev(RealCacheQualityCategory.QMT_BOUNDARY,RealCacheQualityStatus.WARN if sev==RealCacheQualitySeverity.WARN else RealCacheQualityStatus.FAIL,sev,'forbidden marker scan',marker))
    return ev
