from __future__ import annotations
from .safety import assert_safe_selected_models
DRAFT={'mappings':{},'updated_at':None,'note':'session_only; no api key stored'}
def save_usage_draft(mappings):
    vals=[v for v in mappings.values() if v]
    if vals: assert_safe_selected_models(list(dict.fromkeys(vals))[:5])
    DRAFT.update({'mappings':dict(mappings),'note':'模型用途映射草稿不包含 API Key'}); return DRAFT
def get_usage_draft(): return DRAFT
