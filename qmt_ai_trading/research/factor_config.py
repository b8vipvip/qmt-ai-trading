from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
from .factor_registry import list_default_factors
@dataclass
class FactorConfig:
    factor_id:str; window:int|None=None; lookback:int|None=None; weight:float=1.0; direction:str='positive'; winsorize:bool=True; standardize:bool=True; neutralize:bool=False; enabled:bool=True; params:dict[str,Any]|None=None

def build_default_config()->list[FactorConfig]:
    out=[]
    for f in list_default_factors():
        p=dict(f.default_params); out.append(FactorConfig(f.factor_id,p.get('window') or p.get('long_window'),p.get('lookback'),f.default_weight,f.direction,True,True,False,f.enabled,p))
    return out

def config_seed_as_dict()->list[dict[str,Any]]: return [asdict(c) for c in build_default_config()]
