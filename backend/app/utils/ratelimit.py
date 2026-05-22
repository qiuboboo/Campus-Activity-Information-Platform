"""Simple Redis-backed rate limiter using sliding window counters."""

import time

from flask import current_app, jsonify, request
from functools import wraps


class RateLimiter:
    """Sliding-window rate limiter backed by Redis.

    Usage::

        limiter = RateLimiter()
        limiter.init_app(redis_client)

        @limiter.limit("5 per minute")
        def my_route():
            ...
    """

    def __init__(self):
        self._redis = None

    def init_app(self, redis_client) -> None:
        self._redis = redis_client

    def limit(self, rule: str = "60 per minute"):
        """Decorator: enforce *rule* per client IP.

        Rule format: ``"<count> per <second|minute|hour>"``
        Example: ``"5 per minute"``, ``"100 per hour"``
        """
        parts = rule.split()
        if len(parts) != 3:
            raise ValueError(f"invalid rate-limit rule: {rule!r}")
        max_calls = int(parts[0])
        unit = parts[2]
        window = {"second": 1, "minute": 60, "hour": 3600}.get(unit)
        if window is None:
            raise ValueError(f"unknown time unit: {unit!r} (use second/minute/hour)")

        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Skip rate limiting when Redis is not available
                redis = current_app.redis if hasattr(current_app, "redis") else None
                if redis is not None:
                    key = f"ratelimit:{request.remote_addr}:{f.__name__}"
                    now = time.time()
                    cutoff = now - window

                    pipe = redis.pipeline()
                    pipe.zremrangebyscore(key, 0, cutoff)
                    pipe.zcard(key)
                    pipe.zadd(key, {str(now): now})
                    pipe.expire(key, window * 2)
                    _, current, _, _ = pipe.execute()

                    if current >= max_calls:
                        return jsonify({
                            "error": "Too Many Requests",
                            "message": f"Rate limit exceeded ({rule})",
                            "code": 429,
                            "retry_after": int(window),
                        }), 429

                return f(*args, **kwargs)
            return wrapper
        return decorator


limiter = RateLimiter()
