from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping
import os, time

_TRUE={"1","true","yes","on"}
_FALSE={"0","false","no","off"}

def _bool(v, default=False):
    if isinstance(v,bool): return v
    if v is None: return default
    s=str(v).strip().lower()
    if s in _TRUE: return True
    if s in _FALSE: return False
    return default

def _env_file(path: Path) -> dict[str,str]:
    out={}
    if not path.exists(): return out
    for line in path.read_text(encoding='utf-8',errors='ignore').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k,v=line.split('=',1); out[k.strip()]=v.strip().strip('"').strip("'")
    return out

def _first(qs: Mapping[str, Any], name: str):
    if name not in qs: return None
    v=qs[name]
    return v[0] if isinstance(v,(list,tuple)) else v

@dataclass(frozen=True)
class AccountReadonlyConfig:
    enabled: bool = False
    dry_run: bool = True
    read_only: bool = True
    allow_import_xttrader: bool = False
    allow_create_xtquant_trader: bool = False
    allow_connect_trade_session: bool = False
    allow_account_query: bool = False
    allow_position_query: bool = False
    allow_order_query: bool = False
    allow_trade_query: bool = False
    allow_order_submit: bool = False
    allow_order_cancel: bool = False
    requires_human_approval: bool = True
    manual_confirmation_completed: bool = False
    mask_account_required: bool = True
    rate_limit_required: bool = True
    max_queries_per_minute: int = 3
    allow_auto_refresh: bool = False
    notes: str = "Stage91 account readonly boundary; order submit disabled"
    repo_root: str = "."
    userdata_mini_path: str = ""
    account_id: str = ""
    account_type: str = "STOCK"
    session_id_base: int = 910000
    session_id: int = 910000
    config_source: str = "default"
    def to_dict(self) -> dict[str, Any]:
        d=asdict(self)
        if not any([self.repo_root != '.', self.userdata_mini_path, self.account_id, self.account_type != 'STOCK', self.session_id_base != 910000, self.session_id != 910000, self.config_source != 'default']):
            for k in ['repo_root','userdata_mini_path','account_id','account_type','session_id_base','session_id','config_source']:
                d.pop(k, None)
            return d
        d['account_id_masked']=mask_account_for_config(self.account_id); d.pop('account_id',None); return d

def mask_account_for_config(account_id: Any) -> str:
    s="" if account_id is None else str(account_id)
    return "" if not s else ("****" if len(s)<6 else f"{s[:2]}****{s[-2:]}")

def default_account_readonly_config() -> AccountReadonlyConfig:
    return AccountReadonlyConfig()

def build_account_readonly_config(repo_root, request_params: Mapping[str, Any] | None = None) -> AccountReadonlyConfig:
    root=Path(repo_root).resolve(); file_env=_env_file(root/'.env'); request_params=request_params or {}
    def val(name, default=""):
        rv=_first(request_params,name)
        if rv not in (None,""): return str(rv), 'request_params'
        if name in os.environ and os.environ.get(name,"")!="": return os.environ[name], 'os.environ'
        if name in file_env and file_env.get(name,"")!="": return file_env[name], '.env'
        return default, 'default'
    mini, s1=val('QMT_USERDATA_MINI_PATH','')
    fallback, s2=val('QMT_USERDATA_PATH','')
    path = mini or fallback; path_source = s1 if mini else s2
    account, acc_source=val('QMT_ACCOUNT_ID','')
    atype, type_source=val('QMT_ACCOUNT_TYPE','STOCK')
    base_s, base_source=val('QMT_SESSION_ID_BASE','910000')
    try: base=int(base_s)
    except Exception: base=910000
    try: offset=int(str(_first(request_params,'request_offset') or 0))
    except Exception: offset=0
    session_id=base+(os.getpid()%10000)+(int(time.time())%1000)+offset
    source='/'.join(dict.fromkeys([path_source,acc_source,type_source,base_source]).keys())
    return AccountReadonlyConfig(
        enabled=_bool(_first(request_params,'enable_account_readonly'), False), dry_run=_bool(_first(request_params,'dry_run'), True), read_only=True,
        allow_import_xttrader=_bool(_first(request_params,'allow_import_xttrader'), False), allow_connect_trade_session=_bool(_first(request_params,'allow_connect_trade_session'), False),
        allow_account_query=_bool(_first(request_params,'allow_account_query'), False), allow_position_query=_bool(_first(request_params,'allow_position_query'), False),
        manual_confirmation_completed=_bool(_first(request_params,'manual_confirmed'), False), allow_order_submit=False, allow_order_cancel=False,
        repo_root=str(root), userdata_mini_path=path, account_id=account, account_type=str(atype or 'STOCK').upper(), session_id_base=base, session_id=session_id, config_source=source)
