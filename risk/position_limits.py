# -*- coding: utf-8 -*-
def cap_target(raw_target, max_symbol, max_total):
    capped = min(float(raw_target or 0), float(max_symbol), float(max_total))
    return max(0.0, capped)
