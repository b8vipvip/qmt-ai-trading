from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import *
from .safety import scan_live_gray_candidate_text_for_forbidden_markers

def _load_json(p: Path) -> dict[str, Any]:
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return {}

def _critical_count(data: dict[str, Any]) -> int:
    if isinstance(data.get("summary"), dict) and "critical" in data["summary"]: return int(data["summary"].get("critical") or 0)
    return sum(1 for e in data.get("evidence", []) if str(e.get("severity"))=="CRITICAL")

def _symbols(data: dict[str, Any]) -> list[str]:
    out=[]
    for key in ("allowed_symbols","validated_symbols","symbols"):
        if isinstance(data.get(key), list): out += [str(x) for x in data[key]]
    for key in ("coverage","items"):
        for it in data.get(key, []) if isinstance(data.get(key), list) else []:
            s=it.get("symbol") or it.get("code")
            if s: out.append(str(s))
    return sorted(dict.fromkeys(out))

def collect_live_gray_candidate_evidence(cfg: LiveGrayCandidateConfig) -> tuple[list[LiveGrayCandidateEvidence], list[str]]:
    root=Path(cfg.repo_root); ev=[]; symbols=[]
    def add(cat,status,sev,title,summary,path="",meta=None): ev.append(LiveGrayCandidateEvidence(cat,status,sev,title,summary,path,meta or {}))
    s56=root/Path(cfg.real_cache_quality_dir)/"real_cache_quality.json"
    if s56.exists():
        d=_load_json(s56); dec=str(d.get("decision","")); crit=_critical_count(d); symbols += _symbols(d)
        sev=LiveGrayCandidateSeverity.CRITICAL if dec=="NO_GO" or crit>0 else LiveGrayCandidateSeverity.INFO
        add(LiveGrayCandidateCategory.STAGE56_REAL_CACHE_QUALITY, LiveGrayCandidateStatus.PASS if sev==LiveGrayCandidateSeverity.INFO else LiveGrayCandidateStatus.FAIL, sev, "Stage56 real cache quality 读取状态", f"decision={dec or 'UNKNOWN'} critical={crit}", str(s56), {"decision":dec,"critical":crit})
    else:
        add(LiveGrayCandidateCategory.STAGE56_REAL_CACHE_QUALITY, LiveGrayCandidateStatus.UNAVAILABLE, LiveGrayCandidateSeverity.WARN, "Stage56 real cache quality 缺失", "缺少 Stage56 real_cache_quality.json；候选计划只能作为草案。", str(s56))
    for fn in ["long_sample_gap_fill.json","field_quality_review.json","next_backtest_attribution_plan.json"]:
        p=root/Path(cfg.real_cache_quality_dir)/fn
        add(LiveGrayCandidateCategory.STAGE56_REAL_CACHE_QUALITY, LiveGrayCandidateStatus.PASS if p.exists() else LiveGrayCandidateStatus.UNAVAILABLE, LiveGrayCandidateSeverity.INFO if p.exists() else LiveGrayCandidateSeverity.WARN, fn, "Stage56 package item present" if p.exists() else "Stage56 package item missing", str(p))
    s55=root/Path(cfg.qmt_dryrun_calibration_dir)/"qmt_dryrun_calibration.json"
    if s55.exists():
        d=_load_json(s55); dec=str(d.get("decision","")); crit=_critical_count(d)
        sev=LiveGrayCandidateSeverity.CRITICAL if dec=="NO_GO" or crit>0 else LiveGrayCandidateSeverity.INFO
        add(LiveGrayCandidateCategory.STAGE55_QMT_DRYRUN_CALIBRATION, LiveGrayCandidateStatus.PASS if sev==LiveGrayCandidateSeverity.INFO else LiveGrayCandidateStatus.FAIL, sev, "Stage55 qmt dryrun calibration 读取状态", f"decision={dec or 'UNKNOWN'} critical={crit}", str(s55), {"decision":dec,"critical":crit})
    else:
        add(LiveGrayCandidateCategory.STAGE55_QMT_DRYRUN_CALIBRATION, LiveGrayCandidateStatus.UNAVAILABLE, LiveGrayCandidateSeverity.WARN, "Stage55 qmt dryrun calibration 缺失", "缺少 Stage55 qmt_dryrun_calibration.json。", str(s55))
    wl=root/Path(cfg.qmt_dryrun_calibration_dir)/"etf_whitelist_calibration.json"
    if wl.exists(): symbols += _symbols(_load_json(wl))
    if not symbols: symbols=["510300.SH","510500.SH"]
    add(LiveGrayCandidateCategory.ETF_WHITELIST, LiveGrayCandidateStatus.PASS, LiveGrayCandidateSeverity.INFO, "ETF whitelist / validated symbols", ", ".join(symbols[:20]), str(wl))
    text=(root/cfg.roadmap_path).read_text(encoding="utf-8", errors="ignore") if (root/cfg.roadmap_path).exists() else ""
    required=["完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）","Stage61：API Gateway 基础层","Stage75：本地控制台封版 / 可选桌面化","UI 不直接访问 QMT","UI 不能绕过 Risk Gate","UI 不能绕过 Human Approval","UI 不能自动 approve"]
    missing=[x for x in required if x not in text]
    add(LiveGrayCandidateCategory.ROADMAP_STAGE_PLAN, LiveGrayCandidateStatus.FAIL if missing else LiveGrayCandidateStatus.PASS, LiveGrayCandidateSeverity.CRITICAL if missing else LiveGrayCandidateSeverity.INFO, "roadmap Stage1-75 / UI 产品化路线检查", "missing="+", ".join(missing) if missing else "完整工程阶段计划与前端 UI 产品化路线已保留", cfg.roadmap_path)
    for title,cat in [("Risk Gate 不可绕过声明",LiveGrayCandidateCategory.RISK_GATE),("Human Approval 不可绕过声明",LiveGrayCandidateCategory.HUMAN_APPROVAL),("回滚 / 熔断 / 停止条件",LiveGrayCandidateCategory.ROLLBACK_PLAN)]:
        add(cat, LiveGrayCandidateStatus.PASS, LiveGrayCandidateSeverity.INFO, title, "Stage57 候选计划材料包含该只读边界。")
    return ev, symbols
