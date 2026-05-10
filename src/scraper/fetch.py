"""Fetch wrapper: curl_cffi by default, Patchright on failure.

Per kickoff §2 + SOP §1.6:
- Default: curl_cffi (Chrome impersonation, fast).
- Switch to Patchright on 403/429/Cloudflare/empty-body.
- Pacing: 3-5s/req/host with jitter; 200 reqs/hour/host hard cap; 5-min cooldown after 4xx.

Returns a FetchResult with status, body, and which fetcher succeeded.
"""
from __future__ import annotations

import logging
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional
from urllib.parse import urlparse

log = logging.getLogger(__name__)

# Pacing constants (SOP §1.6).
PACE_MIN_SEC = 3.0
PACE_MAX_SEC = 5.0
RATE_PER_HOUR = 200
COOLDOWN_4XX_SEC = 300
EMPTY_BODY_THRESHOLD = 400      # bytes; below this we treat as suspicious

# Hosts where we know curl_cffi is unlikely to work (per kickoff §2).
PATCHRIGHT_PREFERRED_HOSTS = {
    "www.bbc.com", "bbc.com",
    "www.theguardian.com", "theguardian.com",
    "www.ft.com", "ft.com",
    "www.nytimes.com", "nytimes.com",
    "www.politico.eu", "politico.eu",
    "www.dw.com", "dw.com",
}


@dataclass
class FetchResult:
    url: str
    status: Optional[int]
    body: str
    fetcher: str                # 'curl_cffi' | 'patchright' | 'none'
    error: Optional[str] = None
    elapsed_sec: float = 0.0

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300 and len(self.body) >= EMPTY_BODY_THRESHOLD


@dataclass
class _HostState:
    last_fetch: float = 0.0
    timestamps: deque = field(default_factory=deque)
    cooldown_until: float = 0.0


class HostPacer:
    """Per-host token bucket + cooldown tracker."""

    def __init__(self) -> None:
        self._states: dict[str, _HostState] = defaultdict(_HostState)
        self._lock = Lock()

    def wait_if_needed(self, host: str) -> None:
        with self._lock:
            state = self._states[host]
            now = time.monotonic()
            # Cooldown wins over pacing.
            if state.cooldown_until > now:
                wait = state.cooldown_until - now
                log.info("host=%s in cooldown for %.1fs", host, wait)
                time.sleep(wait)
                now = time.monotonic()
            # Hourly rate limit.
            cutoff = now - 3600
            while state.timestamps and state.timestamps[0] < cutoff:
                state.timestamps.popleft()
            if len(state.timestamps) >= RATE_PER_HOUR:
                wait = state.timestamps[0] + 3600 - now
                log.warning("host=%s hourly cap reached; sleeping %.1fs", host, wait)
                time.sleep(max(wait, 1.0))
                now = time.monotonic()
            # Per-request pacing with jitter.
            since = now - state.last_fetch
            min_wait = random.uniform(PACE_MIN_SEC, PACE_MAX_SEC)
            if since < min_wait:
                time.sleep(min_wait - since)
            state.last_fetch = time.monotonic()
            state.timestamps.append(state.last_fetch)

    def begin_cooldown(self, host: str, seconds: float = COOLDOWN_4XX_SEC) -> None:
        with self._lock:
            self._states[host].cooldown_until = time.monotonic() + seconds
            log.warning("host=%s entering cooldown for %.0fs", host, seconds)


_PACER = HostPacer()


# --------------------------------------------------------------------------- #
# Fetchers                                                                    #
# --------------------------------------------------------------------------- #

def _fetch_curl_cffi(url: str, *, timeout: float = 30.0) -> FetchResult:
    """curl_cffi with Chrome impersonation."""
    import curl_cffi.requests as creq

    started = time.monotonic()
    try:
        r = creq.get(url, impersonate="chrome120", timeout=timeout, allow_redirects=True)
        elapsed = time.monotonic() - started
        body = r.text or ""
        return FetchResult(url=url, status=r.status_code, body=body, fetcher="curl_cffi", elapsed_sec=elapsed)
    except Exception as e:
        return FetchResult(
            url=url, status=None, body="", fetcher="curl_cffi",
            error=f"{type(e).__name__}: {e}", elapsed_sec=time.monotonic() - started,
        )


def _fetch_patchright(url: str, *, timeout_ms: int = 45_000) -> FetchResult:
    """Patchright (stealth Playwright fork)."""
    started = time.monotonic()
    try:
        from patchright.sync_api import sync_playwright
    except ImportError as e:
        return FetchResult(
            url=url, status=None, body="", fetcher="patchright",
            error=f"patchright not installed: {e}", elapsed_sec=time.monotonic() - started,
        )

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=10_000)
            except Exception:
                pass
            body = page.content()
            status = response.status if response else None
            context.close()
            browser.close()
        return FetchResult(
            url=url, status=status, body=body, fetcher="patchright",
            elapsed_sec=time.monotonic() - started,
        )
    except Exception as e:
        return FetchResult(
            url=url, status=None, body="", fetcher="patchright",
            error=f"{type(e).__name__}: {e}", elapsed_sec=time.monotonic() - started,
        )


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #

def fetch(url: str, *, preferred_fetcher: str = "curl_cffi") -> FetchResult:
    """Fetch a URL with pacing + automatic fetcher escalation.

    Strategy:
        - Wait per host pacer.
        - If preferred_fetcher='patchright' OR host is in the patchright-preferred set,
          go straight to Patchright.
        - Else try curl_cffi first; on failure (4xx/5xx/empty-body/exception),
          escalate to Patchright once.
        - On 4xx: open a 5-min host cooldown after the call returns.
    """
    host = urlparse(url).netloc.lower()
    _PACER.wait_if_needed(host)

    use_patchright_first = (
        preferred_fetcher == "patchright" or host in PATCHRIGHT_PREFERRED_HOSTS
    )

    if use_patchright_first:
        result = _fetch_patchright(url)
    else:
        result = _fetch_curl_cffi(url)
        if not result.ok:
            log.info(
                "curl_cffi non-ok for %s (status=%s, body_len=%d, error=%s); escalating to patchright",
                url, result.status, len(result.body), result.error,
            )
            _PACER.wait_if_needed(host)
            escalated = _fetch_patchright(url)
            if escalated.ok or (escalated.status and escalated.status != 0):
                result = escalated

    if result.status is not None and 400 <= result.status < 500:
        _PACER.begin_cooldown(host)

    return result
