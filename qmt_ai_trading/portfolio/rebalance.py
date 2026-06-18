from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable
from uuid import uuid4
from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.datahub.symbols import normalize_symbol
from .models import PortfolioAdjustment, PortfolioPosition, PortfolioSnapshot, PortfolioTarget, round_lot

@dataclass
class PortfolioRebalanceConfig:
    rebalance_threshold: float = 0.05
    min_trade_value: float = 0.0
    board_lot_size: int = 100
    default_price: float = 1.0
    allow_sell: bool = True
    allow_buy: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

def build_portfolio_snapshot(*, cash=0.0,total_asset=None,positions=None,source='local_mock_snapshot',dry_run=True,metadata=None):
    pos=[p if isinstance(p,PortfolioPosition) else PortfolioPosition(**p) for p in (positions or [])]
    ta=float(total_asset if total_asset is not None else cash+sum(p.market_value for p in pos))
    for p in pos: p.weight=(p.market_value/ta) if ta>0 else 0.0
    return PortfolioSnapshot(f"snapshot-{uuid4().hex[:12]}", cash=float(cash), total_asset=ta, positions=pos, source=source, dry_run=dry_run, metadata=dict(metadata or {}))

def compute_rebalance_adjustments(snapshot, targets, config=None):
    cfg=config or PortfolioRebalanceConfig(); by={normalize_symbol(p.symbol):p for p in snapshot.positions}; out=[]
    for t in targets or []:
        sym=normalize_symbol(t.symbol); p=by.get(sym); curv=float(p.market_value if p else 0.0); curw=float(p.weight if p else 0.0)
        tv=float(t.target_value or t.target_weight*snapshot.total_asset); dw=float(t.target_weight)-curw; dv=tv-curv; side='BUY' if dw>0 else ('SELL' if dw<0 else 'HOLD')
        reason='rebalance adjustment'
        if abs(dw)<float(cfg.rebalance_threshold): side='HOLD'; qty=0; reason=f'skipped: abs(delta_weight) {abs(dw):.4f} below rebalance_threshold {cfg.rebalance_threshold:.4f}'
        else:
            if side=='BUY' and not cfg.allow_buy: qty=0; reason='skipped: BUY disabled'
            elif side=='SELL' and not cfg.allow_sell: qty=0; reason='skipped: SELL disabled'
            elif abs(dv)<float(cfg.min_trade_value): qty=0; reason=f'skipped: trade value {abs(dv):.2f} below min_trade_value {cfg.min_trade_value:.2f}'
            else:
                price=float((p.last_price if p and p.last_price else 0) or t.metadata.get('last_price') or cfg.default_price or 1.0)
                qty=round_lot(int(abs(dv)/max(price,0.0001)), cfg.board_lot_size); reason=f'{side} to target_weight {t.target_weight:.4f}'
        price=float((p.last_price if p and p.last_price else 0) or t.metadata.get('last_price') or cfg.default_price or 1.0)
        out.append(PortfolioAdjustment(sym,curw,float(t.target_weight),dw,curv,tv,side,qty,price,reason,{**dict(t.metadata or {}),'dry_run':True}))
    return out

def adjustment_to_trade_intent(adjustment, run_id, dry_run=True):
    if adjustment.quantity<=0 or adjustment.side not in {'BUY','SELL'}: return None
    return TradeIntent(adjustment.symbol, adjustment.side, adjustment.quantity, adjustment.target_weight, reason=f"portfolio_plan {run_id}: {adjustment.reason}", source='portfolio_plan', dry_run=bool(dry_run))

def adjustments_to_trade_intents(adjustments, run_id, dry_run=True):
    return [i for i in (adjustment_to_trade_intent(a,run_id,dry_run) for a in (adjustments or [])) if i is not None]
