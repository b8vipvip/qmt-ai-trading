"""QMT client connection management placeholder.

The manager reads account and user-data settings from environment-backed
configuration, but it never connects during module import. Connection behavior
must be triggered explicitly by callers in a local Windows MiniQMT environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qmt_ai_trading.config.settings import get_settings


@dataclass
class QmtClientManager:
    """Lazy QMT client manager for future gateway adapters."""

    account_id: str = ""
    userdata_path: str = ""
    _client: Any = None

    @classmethod
    def from_settings(cls) -> "QmtClientManager":
        """Build a manager from safe environment-backed settings."""

        settings = get_settings()
        return cls(account_id=settings.qmt_account_id, userdata_path=settings.qmt_userdata_path)

    def is_configured(self) -> bool:
        """Return whether account id and user-data path are both configured."""

        return bool(self.account_id and self.userdata_path)

    def connect_readonly(self) -> Any:
        """Explicitly create the existing read-only QMT client adapter.

        TODO(stage2): centralize lifecycle management here as more gateway
        methods are migrated. This remains read-only and does not submit orders.
        """

        if self._client is None:
            from qmt_gateway.trade_readonly_client import QmtTradeReadonlyClient

            self._client = QmtTradeReadonlyClient(
                {"account_id": self.account_id, "qmt_userdata_path": self.userdata_path}
            )
        return self._client
