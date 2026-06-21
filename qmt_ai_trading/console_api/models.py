from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable

def now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
@dataclass(frozen=True)
class ConsoleTask:
    task_id: str; title_zh: str; category: str; description_zh: str
    allowed_params_schema: dict[str, Any] = field(default_factory=dict)
    default_params: dict[str, Any] = field(default_factory=dict)
    safe_mode: bool = True; dry_run_only: bool = True; requires_human_approval: bool = False; forbidden_in_live: bool = True
    command_adapter: str = "python_callable"; python_callable: str = "mock_safe_task"; output_artifacts: list[str] = field(default_factory=list)
@dataclass
class TaskRun:
    run_id: str; task_id: str; task_name: str; category: str; status: str='PENDING'; params: dict[str, Any]=field(default_factory=dict)
    started_at: str|None=None; finished_at: str|None=None; logs: list[str]=field(default_factory=list); output: dict[str, Any]=field(default_factory=dict); output_artifacts: list[str]=field(default_factory=list)
    def to_dict(self): return asdict(self)
