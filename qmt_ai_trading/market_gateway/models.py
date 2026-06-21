from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any
SAFE_FLAGS={'sandbox':True,'not_live_trading':True,'no_qmt_trader_api':True,'read_only':True}
@dataclass
class MarketSymbol:
    symbol:str; exchange:str; name:str=''; provider:str='mock_provider'; source:str='local sandbox market data seed'; sandbox:bool=True; mock_data:bool=True; recorded_data:bool=False; not_live_trading:bool=True; no_qmt_trader_api:bool=True; read_only:bool=True
    def to_dict(self): return asdict(self)
@dataclass
class MarketQuote:
    symbol:str; exchange:str; timestamp:str; bid_price:float; ask_price:float; bid_volume:int; ask_volume:int; source:str='mock_quote'; provider:str='mock_provider'; sandbox:bool=True; mock_data:bool=True; recorded_data:bool=False; not_live_trading:bool=True; no_qmt_trader_api:bool=True; read_only:bool=True
    def to_dict(self): return asdict(self)
@dataclass
class MarketBar:
    symbol:str; exchange:str; timestamp:str; open:float; high:float; low:float; close:float; volume:int; amount:float; timeframe:str='1d'; source:str='mock_bar'; provider:str='mock_provider'; sandbox:bool=True; mock_data:bool=True; recorded_data:bool=False; not_live_trading:bool=True; no_qmt_trader_api:bool=True; read_only:bool=True
    def to_dict(self): return asdict(self)
@dataclass
class MarketTick:
    symbol:str; exchange:str; timestamp:str; price:float; volume:int; amount:float; source:str='mock_tick'; provider:str='mock_provider'; sandbox:bool=True; mock_data:bool=True; recorded_data:bool=False; not_live_trading:bool=True; no_qmt_trader_api:bool=True; read_only:bool=True
    def to_dict(self): return asdict(self)
@dataclass
class MarketSnapshot:
    symbol:str; exchange:str; timestamp:str; last_price:float; open:float; high:float; low:float; close:float; volume:int; amount:float; bid_price:float; ask_price:float; bid_volume:int; ask_volume:int; source:str='mock_snapshot'; provider:str='mock_provider'; sandbox:bool=True; mock_data:bool=True; recorded_data:bool=False; not_live_trading:bool=True; no_qmt_trader_api:bool=True; read_only:bool=True
    def to_dict(self): return asdict(self)
@dataclass
class ReplayEvent:
    event_id:str; event_type:str; symbol:str; timestamp:str; payload:dict[str,Any]; sequence:int; sandbox:bool=True; mock_data:bool=True; read_only:bool=True; not_live_trading:bool=True; no_qmt_trader_api:bool=True
    def to_dict(self): return asdict(self)
@dataclass
class ReplaySession:
    session_id:str; provider:str; symbols:list[str]; status:str='CREATED'; speed:float=1.0; limit:int=100; event_count:int=0; sandbox:bool=True; mock_data:bool=True; read_only:bool=True; not_live_trading:bool=True; no_qmt_trader_api:bool=True; no_order_submitted:bool=True
    def to_dict(self): return asdict(self)
@dataclass
class MarketDataQualityReport:
    symbol_count:int; quote_count:int; bar_count:int; tick_count:int; missing_timestamp_count:int=0; duplicate_timestamp_count:int=0; non_monotonic_timestamp_count:int=0; missing_price_count:int=0; zero_volume_count:int=0; outlier_price_count:int=0; data_quality:str='GOOD'; warnings:list[str]=field(default_factory=list); sandbox:bool=True; mock_data:bool=True; not_live_trading:bool=True; read_only:bool=True; no_qmt_trader_api:bool=True
    def to_dict(self): return asdict(self)
