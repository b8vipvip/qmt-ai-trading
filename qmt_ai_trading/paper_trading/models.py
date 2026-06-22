from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any

SAFETY_FLAGS={"paper_trading":True,"shadow_trading":True,"dry_run":True,"read_only":True,"not_live_trading":True,"no_xttrader":True,"no_order_submitted":True,"no_account_query":True,"requires_human_approval":True}

@dataclass
class PaperOrder:
    order_id:str; intent_id:str; symbol:str; side:str; quantity:int; intent_price:float; target_weight:float=0.0; risk_decision:dict[str,Any]=field(default_factory=dict); fill_status:str="PENDING"; reject_reason:str=""; paper_order:bool=True
    def to_dict(self): return {**asdict(self), **SAFETY_FLAGS}
@dataclass
class PaperFill:
    fill_id:str; order_id:str; symbol:str; side:str; quantity:int; simulated_fill_price:float; fill_time:str; fill_status:str; reject_reason:str=""
    def to_dict(self): return {**asdict(self), **SAFETY_FLAGS}
@dataclass
class ShadowPosition:
    symbol:str; quantity:int; average_price:float; last_price:float; target_weight:float=0.0; current_weight:float=0.0; position_value:float=0.0; unrealized_pnl:float=0.0
    def to_dict(self): return {**asdict(self), **SAFETY_FLAGS}
@dataclass
class ShadowPortfolio:
    paper_cash:float; paper_position_value:float; paper_total_value:float; positions:list[dict[str,Any]]
    def to_dict(self): return {**asdict(self), **SAFETY_FLAGS}
@dataclass
class ShadowPnL:
    unrealized_pnl:float; realized_pnl:float; daily_pnl:float; portfolio_return:float; max_drawdown:float; warnings:list[str]=field(default_factory=list)
    def to_dict(self): return {**asdict(self), **SAFETY_FLAGS}
@dataclass
class RiskReplayResult:
    order_id:str; allowed:bool; reasons:list[str]; safety_violation:bool=False
    def to_dict(self): return {**asdict(self), **SAFETY_FLAGS}
@dataclass
class PaperTradingReport:
    stage:str; paper_order_count:int; paper_fill_count:int; shadow_position_count:int; paper_trading_status:str; safety_status:str
    def to_dict(self): return {**asdict(self), **SAFETY_FLAGS}
