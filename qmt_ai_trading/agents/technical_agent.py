"""Technical analysis agent shell."""

from __future__ import annotations

from qmt_ai_trading.agents.base_agent import BaseAgent
from qmt_ai_trading.common.types import AgentDecision


class TechnicalAgent(BaseAgent):
    """Technical agent placeholder that never places orders."""

    name = "technical_agent"

    def analyze(self, symbol: str) -> AgentDecision:
        """Return an analysis-only neutral technical decision."""

        return AgentDecision(
            symbol=symbol,
            signal="HOLD",
            confidence=0.0,
            score=0.0,
            max_position_pct=0.0,
            reasons=["technical agent placeholder; indicators not wired yet"],
            risk_flags=["no direct order access", "LLM-generated code execution is disabled"],
        )
