from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class CrawlSettings:
    max_pages: int = 8
    timeout_s: float = 15.0
    # Use a browser-like UA by default to reduce trivial bot-blocking.
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )


@dataclass
class CrawlReport:
    attempted: int = 0
    fetched_html: int = 0
    non_html: int = 0
    errors: int = 0
    blocked: int = 0
    last_status: Optional[int] = None
    last_error: str = ""


_HIGH_VALUE_PATHS = [
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
    "/team",
    "/impressum",
    "/legal",
    "/privacy",
    "/support",
]


def _same_host(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()
    except Exception:
        return False


def _extract_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#"):
            continue
        u = urljoin(base_url, href)
        if u.startswith("http://") or u.startswith("https://"):
            links.append(u)
    return links


def _prioritize_links(home: str, links: Iterable[str]) -> list[str]:
    home_host = urlparse(home).netloc.lower()
    candidates = []
    for u in links:
        try:
            p = urlparse(u)
        except Exception:
            continue
        if p.netloc.lower() != home_host:
            continue
        # Ignore obvious non-HTML resources
        if any(p.path.lower().endswith(ext) for ext in (".pdf", ".jpg", ".png", ".zip", ".mp4", ".doc", ".docx")):
            continue
        candidates.append(u)

    def score(u: str) -> int:
        path = urlparse(u).path.lower()
        for i, hv in enumerate(_HIGH_VALUE_PATHS):
            if path == hv or path.startswith(hv + "/"):
                return 100 - i
        return 0

    # High-value first, then stable order
    return sorted(dict.fromkeys(candidates), key=score, reverse=True)


def crawl_site(start_url: str, settings: CrawlSettings) -> tuple[list[tuple[str, str]], CrawlReport]:
    """
    Returns (pages, report) where pages is list of (url, html) for up to settings.max_pages pages.
    """
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    timeout = httpx.Timeout(settings.timeout_s)
    # Avoid picking up system proxy vars that can cause hard failures in some environments.
    client = httpx.Client(timeout=timeout, headers=headers, follow_redirects=True, trust_env=False)

    visited: set[str] = set()
    queue: deque[str] = deque()

    # Seed with homepage + high-value paths.
    queue.append(start_url)
    for path in _HIGH_VALUE_PATHS:
        queue.append(urljoin(start_url, path))

    pages: list[tuple[str, str]] = []
    report = CrawlReport()

    try:
        while queue and len(pages) < settings.max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            try:
                report.attempted += 1
                r = client.get(url)
            except Exception as e:
                report.errors += 1
                report.last_error = f"{type(e).__name__}: {e}"
                continue

            report.last_status = r.status_code
            if r.status_code in (401, 403, 429):
                report.blocked += 1

            ct = (r.headers.get("content-type") or "").lower()
            if "text/html" not in ct and "application/xhtml+xml" not in ct:
                report.non_html += 1
                continue

            html = r.text or ""
            pages.append((str(r.url), html))
            report.fetched_html += 1

            links = _extract_links(str(r.url), html)
            for u in _prioritize_links(start_url, links)[:20]:
                if u not in visited:
                    queue.append(u)
    finally:
        client.close()

    return pages, report

