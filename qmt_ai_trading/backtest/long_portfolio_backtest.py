"""Long-horizon dry-run portfolio backtest using LocalBarStore only."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.performance.attribution import attribute_by_factor
from qmt_ai_trading.performance.metrics import summarize_performance
from qmt_ai_trading.performance.models import BacktestPeriod, LongBacktestResult, PortfolioBacktestTrade, PortfolioEquityPoint, now_iso, to_jsonable, PortfolioPerformanceSummary, FactorAttribution
from qmt_ai_trading.performance.report import format_long_backtest_markdown
from qmt_ai_trading.portfolio.allocator import PortfolioAllocationConfig
from qmt_ai_trading.portfolio.models import PortfolioSnapshot
from qmt_ai_trading.portfolio.rebalance import PortfolioRebalanceConfig, build_portfolio_snapshot
from qmt_ai_trading.portfolio.service import build_portfolio_plan
from qmt_ai_trading.risk.trade_validator import validate_trade_intent
from qmt_ai_trading.strategies.etf_rotation import ETFCandidate

@dataclass
class LongPortfolioBacktestConfig:
    symbols: list[str] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    frequency: str = "1d"
    rebalance_frequency: str = "5d"
    cache_root: str = "market_data"
    min_bars: int = 20
    lookback_bars: int = 20
    initial_cash: float = 1000000.0
    portfolio_method: str = "score_weight"
    portfolio_top_n: int = 2
    cash_reserve_ratio: float = 0.2
    max_symbol_weight: float = 0.2
    max_portfolio_weight: float = 0.8
    rebalance_threshold: float = 0.05
    data_source_mode: str = "cached_real_first"
    quality_report_dir: str = ""
    allow_unknown_quality_for_dry_run: bool = True
    risk_gate_enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

def _d(s): return datetime.fromisoformat(str(s)).date()
def _day(bar):
    v=getattr(bar,"datetime","")
    return str(v).split("T",1)[0].split(" ",1)[0]
def _close(bar): return float(getattr(bar,"close",0) or 0)

def generate_rebalance_dates(start_date, end_date, rebalance_frequency="5d"):
    step=int(str(rebalance_frequency or "5d").lower().replace("d","") or 5)
    cur=_d(start_date); end=_d(end_date); out=[]
    while cur<=end:
        out.append(cur.isoformat()); cur+=timedelta(days=max(1,step))
    return out

def _load_symbol_bars(store, symbol, cfg):
    return store.load_bars(BarQuery([symbol], cfg.start_date, cfg.end_date, cfg.frequency))

def _candidate_from_bars(symbol, bars):
    closes=[_close(b) for b in bars if _close(b)>0]
    vols=[float(getattr(b,"volume",0) or 0) for b in bars]
    if len(closes)<2: mom=0.0; vol=0.0
    else:
        mom=closes[-1]/closes[0]-1.0
        rets=[b/a-1 for a,b in zip(closes,closes[1:]) if a]
        mean=sum(rets)/len(rets) if rets else 0.0
        vol=(sum((x-mean)**2 for x in rets)/len(rets))**0.5 if rets else 0.0
    volume=(sum(vols)/len(vols)) if vols else 0.0
    score=max(0.0, min(100.0, 50+mom*100-vol*100+(min(volume,1_000_000_000)/1_000_000_000)*10))
    return ETFCandidate(symbol=symbol, score=score, target_percent=0.0, eligible=True, reason="long backtest cached factors", metrics={"score":score,"momentum":mom,"volatility":vol,"volume":volume,"bar_count":len(bars),"last_price":closes[-1] if closes else 1.0})

def run_rebalance_step(cfg, rebalance_date, bars_by_symbol, cash, positions):
    candidates=[]; warnings=[]; selected_by_date={}
    for symbol,bars in bars_by_symbol.items():
        hist=[b for b in bars if _day(b) < rebalance_date]
        hist=hist[-int(cfg.lookback_bars):]
        if len(hist) < int(cfg.min_bars):
            warnings.append(f"{rebalance_date} {symbol} insufficient bars: {len(hist)} < {cfg.min_bars}")
            continue
        candidates.append(_candidate_from_bars(symbol,hist))
    candidates.sort(key=lambda c:c.score, reverse=True)
    selected=candidates[:max(1,int(cfg.portfolio_top_n or 1))]
    selected_by_date[rebalance_date]=selected
    price_map={}
    for s,bars in bars_by_symbol.items():
        prior=[b for b in bars if _day(b)<=rebalance_date and _close(b)>0]
        if prior: price_map[s]=_close(prior[-1])
    pos_objs=[]; mv=0.0
    from qmt_ai_trading.portfolio.models import PortfolioPosition
    for sym, qty in positions.items():
        val=qty*price_map.get(sym,0.0); mv+=val
        pos_objs.append(PortfolioPosition(sym, qty, val, 0.0, last_price=price_map.get(sym,0.0)))
    total=cash+mv
    snap=PortfolioSnapshot(f"bt-{rebalance_date}", cash=cash, total_asset=total, positions=pos_objs, source="long_backtest_mock_snapshot", dry_run=True)
    ac=PortfolioAllocationConfig(method=cfg.portfolio_method, top_n=cfg.portfolio_top_n, cash_reserve_ratio=cfg.cash_reserve_ratio, max_symbol_weight=cfg.max_symbol_weight, max_portfolio_weight=cfg.max_portfolio_weight)
    rc=PortfolioRebalanceConfig(rebalance_threshold=cfg.rebalance_threshold, default_price=1.0)
    plan=build_portfolio_plan(selected, snap, ac, rc, run_id=f"long-backtest-{rebalance_date}")
    trades=[]
    for intent in plan.trade_intents:
        decision=validate_trade_intent(intent) if cfg.risk_gate_enabled else type("D",(),{"allowed":True,"reasons":[]})()
        price=price_map.get(intent.symbol,0.0); value=abs(int(intent.quantity)*price)
        trades.append(PortfolioBacktestTrade(rebalance_date, intent.symbol, intent.side, int(intent.quantity), price, value, float(intent.target_percent or 0), bool(decision.allowed), "; ".join(decision.reasons) if not decision.allowed else "", "portfolio_plan_to_risk_gate", {"dry_run":True}))
    return {"candidates":candidates,"selected":selected,"plan":plan,"trades":trades,"warnings":warnings}

def simulate_portfolio_equity(cfg, bars_by_symbol, rebalance_outputs):
    cash=float(cfg.initial_cash); positions={s:0 for s in bars_by_symbol}; trades=[]; equity=[]; peak=cfg.initial_cash; trade_by_date={}
    for out in rebalance_outputs: trade_by_date.setdefault(out["date"],[]).extend(out["trades"])
    all_dates=sorted({ _day(b) for bars in bars_by_symbol.values() for b in bars if cfg.start_date <= _day(b) <= cfg.end_date })
    price_by_date={d:{} for d in all_dates}
    for s,bars in bars_by_symbol.items():
        for b in bars:
            d=_day(b)
            if d in price_by_date: price_by_date[d][s]=_close(b)
    prev=cfg.initial_cash
    for d in all_dates:
        prices=price_by_date.get(d,{})
        for t in trade_by_date.get(d,[]):
            trades.append(t)
            if not t.allowed_by_risk or t.price<=0: continue
            if t.side.upper()=="BUY":
                cost=t.quantity*t.price
                if cost<=cash: cash-=cost; positions[t.symbol]=positions.get(t.symbol,0)+t.quantity
            elif t.side.upper()=="SELL":
                qty=min(positions.get(t.symbol,0), t.quantity); cash+=qty*t.price; positions[t.symbol]=positions.get(t.symbol,0)-qty
        mv=sum(qty*prices.get(sym,0.0) for sym,qty in positions.items())
        eq=cash+mv; ret=(eq/prev-1) if prev else 0.0; peak=max(peak,eq); dd=(eq/peak-1) if peak else 0.0
        equity.append(PortfolioEquityPoint(d,eq,cash,mv,ret,dd,{"dry_run":True})); prev=eq
    return equity,trades

def run_long_portfolio_backtest(cfg):
    symbols=cfg.symbols or [x.symbol for x in get_default_etf_universe()]
    store=LocalBarStore(cfg.cache_root)
    bars_by_symbol={s:_load_symbol_bars(store,s,cfg) for s in symbols}
    warnings=[]
    if not any(len(v)>=cfg.min_bars for v in bars_by_symbol.values()): warnings.append("insufficient cached bars for all symbols")
    dates=generate_rebalance_dates(cfg.start_date,cfg.end_date,cfg.rebalance_frequency)
    outputs=[]; candidates_by_date={}; selected_by_date={}
    for rd in dates:
        out=run_rebalance_step(cfg,rd,bars_by_symbol,cfg.initial_cash, {})
        outputs.append({"date":rd, **out}); candidates_by_date[rd]=out["candidates"]; selected_by_date[rd]=out["selected"]; warnings.extend(out["warnings"])
    equity,trades=simulate_portfolio_equity(cfg,bars_by_symbol,outputs)
    blocked=sum(1 for t in trades if not t.allowed_by_risk)
    summary=summarize_performance(equity,trades,cfg.initial_cash,cfg.start_date,cfg.end_date,len(dates),blocked)
    period=BacktestPeriod(cfg.start_date,cfg.end_date,cfg.frequency,cfg.rebalance_frequency)
    quality="unknown_allowed_for_dry_run" if cfg.allow_unknown_quality_for_dry_run else "unknown"
    return LongBacktestResult(f"long-backtest-{uuid4().hex[:12]}", now_iso(), period, f"LocalBarStore:{cfg.cache_root}", quality, equity, trades, summary, attribute_by_factor(candidates_by_date, selected_by_date, trades), warnings, True, "long backtest completed" if equity else "long backtest completed with no equity points", {"dry_run":True,"symbols":symbols,"risk_gate_enabled":cfg.risk_gate_enabled})

def save_long_backtest_result(result, path):
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower()==".md": p.write_text(format_long_backtest_markdown(result),encoding="utf-8")
    else: p.write_text(json.dumps(to_jsonable(result),ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return p

def load_long_backtest_result(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    period=BacktestPeriod(**data["period"])
    equity=[PortfolioEquityPoint(**x) for x in data.get("equity_curve",[])]
    trades=[PortfolioBacktestTrade(**x) for x in data.get("trades",[])]
    summary=PortfolioPerformanceSummary(**data["summary"]) if data.get("summary") else None
    factors=[FactorAttribution(**x) for x in data.get("factor_attribution",[])]
    return LongBacktestResult(data["run_id"],data["created_at"],period,data.get("data_source",""),data.get("cache_quality",""),equity,trades,summary,factors,data.get("warnings",[]),data.get("success",True),data.get("message",""),data.get("metadata",{}))
