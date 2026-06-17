"""Position concentration checks that do not read real accounts."""

from __future__ import annotations


def validate_target_percent(target_percent: float, max_position_pct: float) -> list[str]:
    """Reject target position percentages above the configured per-symbol cap."""

    if target_percent > max_position_pct:
        return [
            f"target_percent {target_percent:.4f} exceeds max position pct {max_position_pct:.4f}"
        ]
    return []
