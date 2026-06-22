from __future__ import annotations
import time
from collections import deque

class AccountReadonlyRateLimiter:
    def __init__(self, max_queries_per_minute: int = 3):
        self.max_queries_per_minute = int(max_queries_per_minute)
        self._events: deque[float] = deque()
    def allow(self) -> dict:
        now = time.monotonic()
        while self._events and now - self._events[0] >= 60:
            self._events.popleft()
        if len(self._events) >= self.max_queries_per_minute:
            return {"status":"BLOCKED_BY_RATE_LIMIT","message":"account readonly query rate limit exceeded","account_query_attempted":False,"remaining":0,"max_queries_per_minute":self.max_queries_per_minute}
        self._events.append(now)
        return {"status":"PASS","message":"account readonly query allowed","account_query_attempted":True,"remaining":self.max_queries_per_minute-len(self._events),"max_queries_per_minute":self.max_queries_per_minute}
