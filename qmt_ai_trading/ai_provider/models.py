from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

def now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
@dataclass
class AiProviderConfig:
    provider_id:str; provider_type:str; base_url:str; api_key_masked:str; timeout_seconds:int=60; created_at:str=field(default_factory=now_iso); persist_mode:str='session_only'
@dataclass
class AiModelInfo:
    model_id:str; object:str='model'; owned_by:str='unknown'; created:int|None=None; raw:dict[str,Any]=field(default_factory=dict); supports_chat:bool=True; supports_responses:bool=False; status:str='available'
@dataclass
class AiModelDiscoveryResult:
    success:bool; provider_type:str; base_url:str; model_count:int; models:list[AiModelInfo]=field(default_factory=list); error_message:str|None=None; elapsed_ms:int=0; provider:dict[str,Any]=field(default_factory=dict)
@dataclass
class AiStressTestCase:
    case_id:str; input_chars:int; prompt:str; timeout_seconds:int=90
@dataclass
class AiStressTestResult:
    model_id:str; case_id:str; input_chars:int; success:bool; http_status:int|None; elapsed_ms:int; output_chars:int; error_type:str|None=None; error_message:str|None=None; raw_usage:dict[str,Any]=field(default_factory=dict); recommendation:str='待人工复核'
@dataclass
class AiModelBenchmarkReport:
    provider:dict[str,Any]; selected_models:list[str]; test_results:list[AiStressTestResult]; summary:dict[str,Any]; recommended_models:dict[str,str]; warnings:list[str]=field(default_factory=list)
def to_dict(obj):
    if hasattr(obj,'__dataclass_fields__'): return asdict(obj)
    return obj
