"""Symbol blacklist checks for the Risk Gate."""

from __future__ import annotations


def normalize_symbol(symbol: str) -> str:
    """Normalize symbols for stable blacklist matching."""

    return (symbol or "").strip().upper()


def validate_symbol_blacklist(symbol: str, blacklist: set[str] | list[str] | tuple[str, ...]) -> list[str]:
    """Reject a symbol when it is present in the configured blacklist."""

    normalized = normalize_symbol(symbol)
    blocked = {normalize_symbol(item) for item in blacklist}
    if normalized and normalized in blocked:
        return [f"symbol {normalized} is blocked by SYMBOL_BLACKLIST"]
    return []
