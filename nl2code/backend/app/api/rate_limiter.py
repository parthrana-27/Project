import time
from typing import Dict, List
from fastapi import Request, HTTPException
from nl2code.backend.app.config import get_settings

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}

    def check_rate_limit(self, request: Request):
        settings = get_settings()
        limit = settings.rate_limit_per_minute
        client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        window_start = now - 60.0

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Keep only timestamps in the last 60 seconds
        self.requests[client_ip] = [ts for ts in self.requests[client_ip] if ts > window_start]

        if len(self.requests[client_ip]) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: maximum {limit} compilation requests per minute."
            )

        self.requests[client_ip].append(now)

rate_limiter = RateLimiter()
