from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class FactorDefinition:
    factor_id: str
    name_zh: str
    category: str
    description_zh: str
    params_schema: dict[str, Any]
    default_params: dict[str, Any]
    direction: str
    default_weight: float
    enabled: bool
    requires_fields: list[str]

_CATS={'momentum':'动量','volatility':'波动率','volume':'成交量','ma':'均线','drawdown':'回撤'}
_DEFAULTS=[
 FactorDefinition('momentum_5d','5日动量','动量','最近5个交易日收盘价涨跌幅',{'window':{'type':'integer','min':1}}, {'window':5}, 'positive',1.0,True,['close']),
 FactorDefinition('momentum_20d','20日动量','动量','最近20个交易日收盘价涨跌幅',{'window':{'type':'integer','min':1}}, {'window':20}, 'positive',1.2,True,['close']),
 FactorDefinition('momentum_60d','60日动量','动量','最近60个交易日收盘价涨跌幅',{'window':{'type':'integer','min':1}}, {'window':60}, 'positive',0.8,True,['close']),
 FactorDefinition('volatility_20d','20日波动率','波动率','最近20日年化波动率，越低越好',{'window':{'type':'integer','min':2}}, {'window':20}, 'negative',0.9,True,['close']),
 FactorDefinition('volume_ratio_20d','20日量比','成交量','最近成交量相对20日均量的比例',{'window':{'type':'integer','min':2}}, {'window':20}, 'positive',0.7,True,['volume']),
 FactorDefinition('drawdown_60d','60日回撤','回撤','最近60日最大回撤，越小越好',{'window':{'type':'integer','min':2}}, {'window':60}, 'negative',0.8,True,['close']),
 FactorDefinition('ma_trend_20_60','20/60均线趋势','均线','20日均线相对60日均线强弱',{'short_window':{'type':'integer'},'long_window':{'type':'integer'}}, {'short_window':20,'long_window':60}, 'positive',1.0,True,['close']),
 FactorDefinition('return_reversal_5d','5日反转','动量','短期反转因子，最近5日跌幅越大分数越高',{'window':{'type':'integer','min':1}}, {'window':5}, 'negative',0.5,True,['close']),
]

def list_default_factors()->list[FactorDefinition]: return list(_DEFAULTS)
def get_factor(factor_id:str)->FactorDefinition|None: return next((f for f in _DEFAULTS if f.factor_id==factor_id), None)
def catalog_as_dict()->list[dict[str,Any]]: return [asdict(f) for f in _DEFAULTS]
