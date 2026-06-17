"""QMT account query gateway shell.

This module is read-only and does not perform order submission.
"""

from __future__ import annotations

from typing import Any


class QmtAccountGateway:
    """Account, cash, and position query interface placeholder."""

    def get_account_snapshot(self) -> dict[str, Any]:
        """Return account snapshot data.

        TODO: Adapt existing safe QMT account query logic here.
        """

        raise NotImplementedError("QMT account adapter is not implemented yet")
