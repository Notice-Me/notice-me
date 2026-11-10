import asyncio
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

    def __str__(self):
        # Never stringify httpx exceptions, bodies or URLs (query/path may contain credentials).
        return f"{self.provider}: {self.code} (HTTP {self.http_status})"


class SafeHTTP:
    def __init__(self, provider: str, timeout: float = 10, transport=None, min_interval: float = 0):
        self.provider = provider
        self.timeout = timeout
        self.transport = transport
        self.min_interval = min_interval
        self.last_call = 0.0
        self.last_http_status: int | None = None
        self.calls = 0

    async def get(self, url: str, *, params=None, headers=None) -> httpx.Response:
        pause = self.min_interval - (time.monotonic() - self.last_call)
        if pause > 0:
            await asyncio.sleep(pause)
        self.last_call = time.monotonic()
        self.calls += 1
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, transport=self.transport, follow_redirects=False
            ) as client:
                response = await client.get(url, params=params, headers=headers)
        except httpx.TimeoutException:
            raise ProviderError(self.provider, "TIMEOUT") from None
        except httpx.HTTPError:
            raise ProviderError(self.provider, "NETWORK_ERROR") from None
        self.last_http_status = response.status_code
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
            raise ProviderError(self.provider, code, response.status_code)
        return response

    async def json(self, url: str, **kwargs) -> dict:
        response = await self.get(url, **kwargs)
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except ValueError:
            raise ProviderError(self.provider, "INVALID_JSON", response.status_code) from None

    async def xml(self, url: str, **kwargs):
        response = await self.get(url, **kwargs)
        try:
            return ElementTree.fromstring(response.content)
        except Exception:
            raise ProviderError(self.provider, "INVALID_XML", response.status_code) from None


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
