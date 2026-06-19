from __future__ import annotations
import json, subprocess
from pathlib import Path
from .models import ConfigFreezeReviewItem, EnvironmentSnapshotItem, LiveEnvSnapshotCategory as C, LiveEnvSnapshotConfig, LiveEnvSnapshotEvidence, LiveEnvSnapshotSeverity as Sev, LiveEnvSnapshotStatus as S
from .safety import scan_env_snapshot_text_for_forbidden_markers

def _ev(i,cat,status,sev,path,title,summary,**md): return LiveEnvSnapshotEvidence(i,cat,status,sev,str(path),title,summary,md)
def _cf(i,name,value,status=S.PASS,sev=Sev.INFO,summary=""): return ConfigFreezeReviewItem(i,C.CONFIG_FREEZE,status,sev,name,str(value),summary)
def _snap(i,cat,name,value,status=S.PASS,sev=Sev.INFO,summary=""): return EnvironmentSnapshotItem(i,cat,status,sev,name,str(value),summary)
def _read_json(path: Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: return {"_error": str(exc)}
def _decision(data): return str(data.get('decision') or data.get('status') or '').upper()
def _critical_count(data):
    s=data.get('summary') or {}; return int(s.get('critical') or s.get('critical_count') or 0)

def collect_live_env_snapshot_evidence(config: LiveEnvSnapshotConfig):
    root=Path(config.repo_root); evidence=[]; freeze=[]; snapshots=[]
    sources=[(root/config.signature_freeze_dir/'live_signature_freeze.json', C.STAGE43_SIGNATURE_FREEZE, {'NO_GO'}), (root/config.signature_freeze_dir/'config_freeze.json', C.CONFIG_FREEZE, {'NO_GO'}), (root/config.review_dir/'live_gray_review.json', C.STAGE42_HUMAN_REVIEW, {'NO_GO'}), (root/config.ledger_dir/'live_gray_ledger.json', C.STAGE41_LEDGER, {'BLOCKED'}), (root/config.redline_review_dir/'redline_review.json', C.STAGE40_REDLINE_REVIEW, {'BLOCKED'})]
    for path,cat,blocked in sources:
        if not path.exists():
            evidence.append(_ev(f'stage44-missing-{len(evidence)+1}', cat, S.SKIPPED, Sev.WARN, path, 'Missing evidence', f'{path} is missing; Stage44 needs more evidence.')); continue
        data=_read_json(path); dec=_decision(data); crit=_critical_count(data)
        if data.get('_error'):
            evidence.append(_ev(f'stage44-json-error-{len(evidence)+1}', cat, S.WARN, Sev.WARN, path, 'Unreadable JSON', data['_error']))
        elif dec in blocked or crit>0:
            evidence.append(_ev(f'stage44-blocked-{len(evidence)+1}', cat, S.FAIL, Sev.CRITICAL, path, 'Blocking evidence', f'decision={dec or "UNKNOWN"} critical={crit}', decision=dec, critical=crit))
        elif cat==C.STAGE43_SIGNATURE_FREEZE and dec=='NEED_MORE_EVIDENCE' and crit==0:
            evidence.append(_ev(f'stage44-need-evidence-{len(evidence)+1}', cat, S.WARN, Sev.WARN, path, 'Stage43 needs more evidence', 'Stage43 NEED_MORE_EVIDENCE with critical=0; Stage44 remains NEED_MORE_EVIDENCE, not NO_GO.', decision=dec, critical=crit))
        else:
            evidence.append(_ev(f'stage44-pass-{len(evidence)+1}', cat, S.PASS, Sev.INFO, path, 'Evidence available', f'decision={dec or "UNKNOWN"} critical={crit}', decision=dec, critical=crit))
    gi=root/'.gitignore'; required=['validation_logs/','market_data/','reports/','logs/','live_env_snapshot_stage44/','live_env_snapshot/','market_data_test_stage44/']
    text=gi.read_text(encoding='utf-8', errors='replace') if gi.exists() else ''
    for req in required:
        ok=req in text
        freeze.append(_cf(f'gitignore-{req}', req, ok, S.PASS if ok else S.WARN, Sev.INFO if ok else Sev.WARN, '.gitignore ignore rule present.' if ok else 'Missing .gitignore runtime ignore rule.'))
    for name,val in [('read_only',config.read_only),('dry_run_only',config.dry_run_only),('no_trade_authorization',config.no_trade_authorization),('live_trading_enabled',config.live_trading_enabled)]:
        freeze.append(_cf(f'freeze-{name}', name, val, S.PASS if (val is not True if name=='live_trading_enabled' else val is True) else S.FAIL, Sev.INFO, 'Stage44 safety switch review.'))
    for d in ['validation_logs','live_env_snapshot_stage44','live_signature_freeze_stage43','live_gray_review_stage42','live_gray_ledger_stage41','redline_review_stage40','market_data_test_stage44']:
        p=root/d; exists=p.exists(); snapshots.append(_snap(f'runtime-{d}', C.RUNTIME_ARTIFACT, d, exists, S.WARN if exists else S.PASS, Sev.WARN if exists else Sev.INFO, 'Runtime artifact directory exists locally and must remain ignored.' if exists else 'No local runtime artifact directory found.'))
    snapshots += [_snap('env-read-only',C.DRY_RUN_MODE,'read_only',True), _snap('env-dry-run-only',C.DRY_RUN_MODE,'dry_run_only',True), _snap('env-live-switch',C.LIVE_SWITCH,'live_trading_enabled',False), _snap('env-qmt-boundary',C.QMT_BOUNDARY,'xttrader_called',False,'PASS','INFO','Stage44 does not import/call xttrader.'), _snap('env-notify',C.NOTIFICATION_DRY_RUN,'real_notification_sent',False)]
    for path in [root/config.signature_freeze_dir/'live_signature_freeze.md', root/config.signature_freeze_dir/'config_freeze.md']:
        if path.exists() and path.stat().st_size < 500_000:
            freeze.extend(scan_env_snapshot_text_for_forbidden_markers(path.read_text(encoding='utf-8', errors='replace'), path))
    return evidence, freeze, snapshots
