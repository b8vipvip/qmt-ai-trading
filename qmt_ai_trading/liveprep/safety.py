from __future__ import annotations
from typing import Any, Mapping
from .models import LiveGrayConfig, LiveGrayCheck, LiveGrayCheckStatus as S, LiveGraySeverity as V, LiveGrayScope as C, LiveGrayReadinessReport
SENSITIVE=("token","key","password","secret")
FORBIDDEN=("自动实盘下单","绕过人工审批","绕过风控","直接提交订单","无需审计","无需确认")
def sanitize_live_gray_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    out={}
    for k,v in dict(metadata or {}).items():
        if any(x in str(k).lower() for x in SENSITIVE): out[str(k)]="<redacted>"
        elif isinstance(v, Mapping): out[str(k)]=sanitize_live_gray_metadata(v)
        else: out[str(k)]=v
    return out
def build_default_live_gray_config(**kwargs: Any) -> LiveGrayConfig:
    kwargs["metadata"]=sanitize_live_gray_metadata(kwargs.get("metadata"))
    return LiveGrayConfig(**kwargs)
def assert_live_disabled_by_default(config: LiveGrayConfig) -> LiveGrayCheck:
    return LiveGrayCheck("live_disabled_default",C.CONFIG,S.PASS if not config.live_enabled else S.FAIL,V.INFO if not config.live_enabled else V.CRITICAL,"Live trading disabled by default","live_enabled is False by default" if not config.live_enabled else "live_enabled=True is not allowed without future explicit manual process",{"live_enabled":config.live_enabled},"Keep --live-enabled omitted for Stage 30.")
def validate_live_gray_config(config: LiveGrayConfig) -> list[LiveGrayCheck]:
    checks=[assert_live_disabled_by_default(config)]
    if config.live_enabled:
        checks.append(LiveGrayCheck("live_enabled_block",C.CONFIG,S.FAIL,V.CRITICAL,"Live switch explicit block","Stage 30 cannot enable live trading even when requested.",{"live_enabled":True},"Do not pass --live-enabled."))
    return checks
def contains_forbidden_live_action(text: str | None) -> bool:
    return any(item in str(text or "") for item in FORBIDDEN)
def validate_no_live_execution_intent(report: LiveGrayReadinessReport) -> LiveGrayCheck:
    hay=str(report.to_dict())
    bad=contains_forbidden_live_action(hay)
    return LiveGrayCheck("no_live_execution_intent",C.SYSTEM,S.FAIL if bad else S.PASS,V.CRITICAL if bad else V.INFO,"No live execution intent","Forbidden live execution phrase found." if bad else "No forbidden live execution intent detected.",{},"Remove live execution language.")
