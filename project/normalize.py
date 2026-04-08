from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urlunparse


@dataclass(frozen=True)
class NormalizedUrl:
    original: str
    normalized: Optional[str]
    reason: str = ""


def normalize_url(raw: str) -> NormalizedUrl:
    s = (raw or "").strip()
    if not s:
        return NormalizedUrl(original=raw, normalized=None, reason="empty")

    # If user passed a bare domain, add scheme.
    if "://" not in s:
        s = "https://" + s

    try:
        p = urlparse(s)
    except Exception:
        return NormalizedUrl(original=raw, normalized=None, reason="parse_error")

    if not p.netloc:
        return NormalizedUrl(original=raw, normalized=None, reason="missing_host")

    scheme = p.scheme if p.scheme in ("http", "https") else "https"
    netloc = p.netloc.lower()
    path = p.path or "/"

    normalized = urlunparse((scheme, netloc, path, "", "", ""))
    return NormalizedUrl(original=raw, normalized=normalized, reason="ok")


def domain_from_url(url: str) -> Optional[str]:
    try:
        p = urlparse(url)
        return p.netloc.lower() if p.netloc else None
    except Exception:
        return None

