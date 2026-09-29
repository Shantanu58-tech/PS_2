"""Collector resilience (PRD 7.3): exponential backoff with jitter, a circuit
breaker, and per-collector health exposed at /api/collectors."""
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


@dataclass
class CollectorHealth:
    name: str
    state: str = "idle"  # idle | ok | degraded | circuit_open | stopped
    errors: int = 0
    consecutive_failures: int = 0
    last_error: str | None = None
    last_ok: float | None = None
    opened_at: float | None = None
    failure_threshold: int = 5
    cooldown_s: float = 120.0
    records: int = 0

    @property
    def circuit_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.monotonic() - self.opened_at >= self.cooldown_s:
            return False  # half-open: allow a trial call
        return True

    def success(self, n: int = 1) -> None:
        self.consecutive_failures = 0
        self.opened_at = None
        self.state = "ok"
        self.last_ok = time.time()
        self.records += n

    def failure(self, exc: BaseException) -> None:
        self.errors += 1
        self.consecutive_failures += 1
        self.last_error = f"{type(exc).__name__}: {exc}"[:300]
        if self.consecutive_failures >= self.failure_threshold:
            self.opened_at = time.monotonic()
            self.state = "circuit_open"
        else:
            self.state = "degraded"


@dataclass
class HealthRegistry:
    items: dict[str, CollectorHealth] = field(default_factory=dict)

    def get(self, name: str) -> CollectorHealth:
        return self.items.setdefault(name, CollectorHealth(name))


registry = HealthRegistry()


class CircuitOpen(RuntimeError):
    pass


async def call_with_backoff(
    health: CollectorHealth,
    fn: Callable[[], Awaitable[T]],
    retries: int = 4,
    base: float = 1.0,
    cap: float = 60.0,
    sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
) -> T:
    """Run fn with exponential backoff + full jitter; trips the breaker."""
    if health.circuit_open:
        raise CircuitOpen(f"{health.name}: circuit open")
    for attempt in range(retries + 1):
        try:
            result = await fn()
            health.success(0)
            return result
        except Exception as exc:
            wait = getattr(exc, "seconds", None)  # Telethon FloodWaitError carries .seconds
            health.failure(exc)
            if attempt == retries or health.circuit_open:
                raise
            await sleep(float(wait) if wait else random.uniform(0, min(cap, base * 2 ** attempt)))
    raise RuntimeError("unreachable")
