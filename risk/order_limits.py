# -*- coding: utf-8 -*-
def cap_order_amount(amount, max_amount, cash):
    vals = [float(amount or 0), float(cash or 0)]
    if max_amount is not None: vals.append(float(max_amount))
    return max(0.0, min(vals))
