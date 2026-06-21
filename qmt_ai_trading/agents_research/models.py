from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any
ALLOWED_RECOMMENDATIONS={"RESEARCH_ONLY","WATCHLIST_SUGGESTION","RISK_WARNING","PORTFOLIO_REVIEW","NO_ACTION"}
def now_iso(): return datetime.now(timezone.utc).isoformat()
@dataclass
class AgentOutput:
    agent_id:str; agent_name:str; role:str; model_id:str; input_sources:list[str]
    summary:str; arguments:list[str]; confidence:float; risk_flags:list[str]; limitations:list[str]
    recommendation_type:str="RESEARCH_ONLY"; created_at:str=field(default_factory=now_iso)
    dry_run:bool=True; not_live_trading:bool=True; research_only:bool=True
    def to_dict(self)->dict[str,Any]:
        d=asdict(self)
        if d["recommendation_type"] not in ALLOWED_RECOMMENDATIONS: d["recommendation_type"]="NO_ACTION"
        return d
