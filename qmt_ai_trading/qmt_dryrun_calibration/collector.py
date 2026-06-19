from __future__ import annotations
import json, os
from pathlib import Path
from .models import *
from .xtdata_probe import *

def _ev(cat,status,severity,title,summary,path='',decision='',metadata=None): return QmtDryrunCalibrationEvidence(category=cat,status=status,severity=severity,title=title,summary=summary,path=path,decision=decision,metadata=metadata or {})
def collect_qmt_dryrun_calibration_evidence(cfg:QmtDryrunCalibrationConfig):
    root=Path(cfg.repo_root); ev=[]
    gp=root/cfg.gap_clearance_dir/'live_gap_clearance.json'
    if gp.exists():
        data=json.loads(gp.read_text(encoding='utf-8')); dec=str(data.get('decision','')); critical=int((data.get('summary') or {}).get('critical',0) or len(data.get('blocking_reasons') or []))
        sev=QmtDryrunCalibrationSeverity.CRITICAL if dec=='NO_GO' or critical>0 else QmtDryrunCalibrationSeverity.INFO
        st=QmtDryrunCalibrationStatus.FAIL if sev==QmtDryrunCalibrationSeverity.CRITICAL else QmtDryrunCalibrationStatus.PASS
        ev.append(_ev(QmtDryrunCalibrationCategory.STAGE54_GAP_CLEARANCE,st,sev,'Stage54 gap clearance',f'decision={dec}, critical={critical}',str(gp),dec,{'critical':critical}))
    else: ev.append(_ev(QmtDryrunCalibrationCategory.STAGE54_GAP_CLEARANCE,QmtDryrunCalibrationStatus.SKIPPED,QmtDryrunCalibrationSeverity.WARN,'Stage54 gap clearance missing','Stage54 gap clearance JSON 缺失，需补证。',str(gp)))
    for p in [os.environ.get('QMT_PATH',''),os.environ.get('MINIQMT_PATH',''), 'D:/AI/qmt', 'C:/国金证券QMT交易端']:
        if p: ev.append(_ev(QmtDryrunCalibrationCategory.QMT_PATH,QmtDryrunCalibrationStatus.PASS if Path(p).exists() else QmtDryrunCalibrationStatus.WARN,QmtDryrunCalibrationSeverity.INFO if Path(p).exists() else QmtDryrunCalibrationSeverity.WARN,'QMT/MiniQMT path',f'{p} exists={Path(p).exists()}',p))
    ok,msg=probe_xtquant_import(); ev.append(_ev(QmtDryrunCalibrationCategory.XTQUANT_IMPORT,QmtDryrunCalibrationStatus.PASS if ok else QmtDryrunCalibrationStatus.UNAVAILABLE,QmtDryrunCalibrationSeverity.INFO if ok else QmtDryrunCalibrationSeverity.WARN,'xtquant import',msg))
    ok,xtdata,msg=probe_xtdata_import(); ev.append(_ev(QmtDryrunCalibrationCategory.XTDATA_IMPORT,QmtDryrunCalibrationStatus.PASS if ok else QmtDryrunCalibrationStatus.UNAVAILABLE,QmtDryrunCalibrationSeverity.INFO if ok else QmtDryrunCalibrationSeverity.WARN,'xtdata import',msg))
    for name,(present,msg) in probe_xtdata_functions(xtdata).items(): ev.append(_ev(QmtDryrunCalibrationCategory.XTDATA_FUNCTION,QmtDryrunCalibrationStatus.PASS if present else QmtDryrunCalibrationStatus.UNAVAILABLE,QmtDryrunCalibrationSeverity.INFO if present else QmtDryrunCalibrationSeverity.WARN,name,msg))
    smoke,meta,msg=probe_xtdata_smoke_readonly(cfg.provider,cfg.max_symbols,cfg.max_days); ev.append(_ev(QmtDryrunCalibrationCategory.XTDATA_SMOKE_TEST,QmtDryrunCalibrationStatus.PASS if smoke else QmtDryrunCalibrationStatus.UNAVAILABLE,QmtDryrunCalibrationSeverity.INFO if smoke else QmtDryrunCalibrationSeverity.WARN,'xtdata readonly smoke',msg,metadata=meta))
    rp=root/cfg.roadmap_path
    if rp.exists():
        txt=rp.read_text(encoding='utf-8'); need=['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']
        missing=[x for x in need if x not in txt]
        ev.append(_ev(QmtDryrunCalibrationCategory.ROADMAP_STAGE_PLAN,QmtDryrunCalibrationStatus.FAIL if missing else QmtDryrunCalibrationStatus.PASS,QmtDryrunCalibrationSeverity.CRITICAL if missing else QmtDryrunCalibrationSeverity.INFO,'roadmap Stage1-75', 'missing='+','.join(missing) if missing else 'Stage1-75 plan retained',str(rp)))
        ev.append(_ev(QmtDryrunCalibrationCategory.UI_PRODUCTIZATION_PLAN,QmtDryrunCalibrationStatus.FAIL if missing else QmtDryrunCalibrationStatus.PASS,QmtDryrunCalibrationSeverity.CRITICAL if missing else QmtDryrunCalibrationSeverity.INFO,'UI productization plan','UI safety plan retained' if not missing else 'UI plan missing critical text',str(rp)))
    else: ev.append(_ev(QmtDryrunCalibrationCategory.ROADMAP_STAGE_PLAN,QmtDryrunCalibrationStatus.FAIL,QmtDryrunCalibrationSeverity.CRITICAL,'roadmap missing','roadmap 缺失',str(rp)))
    return ev
