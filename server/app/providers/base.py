import asyncio
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256

import httpx
from defusedxml import ElementTree

KST = timezone(timedelta(hours=9))


@dataclass
class ProviderError(Exception):
    provider: str
    code: str
    http_status: int | None = None
    timeout_phase: str | None = None
    attempts: int = 1
    response_sha256: str | None = None

    def __str__(self):
        # Never stringify httpx exceptions, bodies or URLs (query/path may contain credentials).
        return f"{self.provider}: {self.code} (HTTP {self.http_status})"


@dataclass
class RequestBudget:
    limit: int = 20
    used: int = 0

    def consume(self, provider: str):
        if self.used >= self.limit:
            raise ProviderError(provider, "REQUEST_BUDGET_EXHAUSTED", attempts=0)
        self.used += 1


class SafeHTTP:
    def __init__(
        self,
        provider: str,
        timeout: float | httpx.Timeout = 10,
        transport=None,
        min_interval: float = 0,
        *,
        max_retries: int = 0,
        backoff_seconds: float = 1,
        budget: RequestBudget | None = None,
        total_timeout: float | None = None,
    ):
        self.provider = provider
        self.timeout = timeout
        self.transport = transport
        self.min_interval = min_interval
        self.last_call = 0.0
        self.last_http_status: int | None = None
        self.calls = 0
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.budget = budget
        self.total_timeout = total_timeout
        self.last_attempts: list[dict] = []
        self.quota_remaining: int | None = None
        self.rate_limited = False

    async def get(self, url: str, *, params=None, headers=None) -> httpx.Response:
        self.last_attempts = []
        self.last_http_status = None
        for index in range(self.max_retries + 1):
            if self.rate_limited or self.quota_remaining == 0:
                raise ProviderError(self.provider, "RATE_LIMITED", attempts=len(self.last_attempts))
            if self.budget:
                self.budget.consume(self.provider)
            started = time.monotonic()
            try:
                response = await self._get_once(url, params=params, headers=headers)
            except ProviderError as error:
                self.last_attempts.append(
                    {
                        "attempt": index + 1,
                        "code": error.code,
                        "http_status": error.http_status,
                        "timeout_phase": error.timeout_phase,
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                        "response_sha256": error.response_sha256,
                    }
                )
                retryable = error.code in {"TIMEOUT", "NETWORK_ERROR"} or error.http_status in {502, 503, 504}
                can_retry = (
                    index < self.max_retries
                    and retryable
                    and not self.rate_limited
                    and self.quota_remaining != 0
                    and (self.budget is None or self.budget.used < self.budget.limit)
                )
                if not can_retry:
                    error.attempts = len(self.last_attempts)
                    raise
                delay = self.backoff_seconds * (2**index) + random.uniform(0, 0.25)
                self.last_attempts[-1]["retry_delay_seconds"] = round(delay, 3)
                await asyncio.sleep(delay)
            else:
                self.last_attempts.append(
                    {
                        "attempt": index + 1,
                        "code": "SUCCESS",
                        "http_status": response.status_code,
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                    }
                )
                return response
        raise AssertionError("Unreachable retry state")

    async def _get_once(self, url: str, *, params=None, headers=None) -> httpx.Response:
        pause = self.min_interval - (time.monotonic() - self.last_call)
        if pause > 0:
            await asyncio.sleep(pause)
        self.last_call = time.monotonic()
        self.calls += 1
        self.last_http_status = None
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, transport=self.transport, follow_redirects=False
            ) as client:
                async with asyncio.timeout(self.total_timeout):
                    response = await client.get(url, params=params, headers=headers)
        except httpx.TimeoutException as error:
            phase = next(
                (
                    name
                    for kind, name in [
                        (httpx.ConnectTimeout, "connect"),
                        (httpx.ReadTimeout, "read"),
                        (httpx.WriteTimeout, "write"),
                        (httpx.PoolTimeout, "pool"),
                    ]
                    if isinstance(error, kind)
                ),
                "unknown",
            )
            raise ProviderError(self.provider, "TIMEOUT", timeout_phase=phase) from None
        except TimeoutError:
            raise ProviderError(self.provider, "TIMEOUT", timeout_phase="total") from None
        except httpx.HTTPError:
            raise ProviderError(self.provider, "NETWORK_ERROR") from None
        self.last_http_status = response.status_code
        remaining = response.headers.get("x-ratelimit-remaining-day", "")
        if remaining.isdigit():
            self.quota_remaining = int(remaining)
        if response.status_code == 429:
            self.rate_limited = True
        if not response.is_success:
            code = {401: "AUTH_REQUIRED", 403: "ACCESS_DENIED", 429: "RATE_LIMITED"}.get(
                response.status_code, "HTTP_ERROR"
            )
            if self.provider == "gnews" and response.status_code == 400:
                try:
                    errors = response.json().get("errors", [])
                    if any(isinstance(e, str) and e.startswith("No API key was sent.") for e in errors):
                        code = "AUTH_REQUIRED"
                except (ValueError, AttributeError, TypeError):
                    pass
            raise ProviderError(
                self.provider,
                code,
                response.status_code,
                response_sha256=sha256(response.content).hexdigest(),
            )
        return response

    async def json(self, url: str, **kwargs) -> dict:
        response = await self.get(url, **kwargs)
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except ValueError:
            raise ProviderError(
                self.provider, "INVALID_JSON", response.status_code, attempts=len(self.last_attempts)
            ) from None

    async def xml(self, url: str, **kwargs):
        response = await self.get(url, **kwargs)
        try:
            return ElementTree.fromstring(response.content)
        except Exception:
            raise ProviderError(
                self.provider, "INVALID_XML", response.status_code, attempts=len(self.last_attempts)
            ) from None


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}:{sha256(value.encode()).hexdigest()[:24]}"


def parse_datetime(value: str | None, *, local=False) -> datetime | None:
    if not value or value == "-":
        return None
    value = str(value).strip()
    try:
        if len(value) in (8, 12, 14) and value.isdigit():
            fmt = {8: "%Y%m%d", 12: "%Y%m%d%H%M", 14: "%Y%m%d%H%M%S"}[len(value)]
            dt = datetime.strptime(value, fmt)
        else:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return (dt.replace(tzinfo=KST if local else UTC) if dt.tzinfo is None else dt).astimezone(UTC)
    except (ValueError, TypeError):
        return None


def end_of_day(value: str) -> datetime | None:
    dt = parse_datetime(value, local=True)
    if dt is None:
        return None
    return (
        dt.astimezone(KST).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    ).astimezone(UTC)


def coordinates(lat, lon) -> tuple[float | None, float | None]:
    try:
        a, b = float(lat), float(lon)
        if -90 <= a <= 90 and -180 <= b <= 180 and (a, b) != (0, 0):
            return a, b
    except (ValueError, TypeError):
        pass
    return None, None


def check_seoul_xml(root, provider: str):
    code = root.findtext(".//RESULT.CODE") or root.findtext(".//CODE")
    if code != "INFO-000":
        raise ProviderError(provider, code or "SCHEMA_MISMATCH", 200)
