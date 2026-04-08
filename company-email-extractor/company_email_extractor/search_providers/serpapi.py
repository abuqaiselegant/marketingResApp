from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

import httpx


def _domain_hint(normalized_url: Optional[str]) -> Optional[str]:
    if not normalized_url:
        return None
    try:
        return urlparse(normalized_url).netloc.lower() or None
    except Exception:
        return None


def serpapi_search_texts(
    *,
    company: str,
    normalized_url: Optional[str],
    api_key: str,
    timeout_s: float = 15.0,
) -> list[str]:
    """
    Calls SerpAPI and returns a list of text blobs (snippets/titles) to run email regex over.

    We intentionally keep this lightweight: the goal is to *discover* emails and/or likely contact pages.
    """
    domain = _domain_hint(normalized_url)
    company_q = (company or "").strip()

    queries: list[str] = []
    if domain:
        queries.extend(
            [
                f'site:{domain} email',
                f'site:{domain} contact email',
                f'"@{domain}" email',
            ]
        )
    if company_q:
        queries.append(f'{company_q} email contact')

    # Keep bounded to avoid burning API credits.
    queries = queries[:3]

    texts: list[str] = []
    timeout = httpx.Timeout(timeout_s)
    # Avoid picking up system proxy vars that can cause hard failures.
    with httpx.Client(timeout=timeout, trust_env=False) as client:
        for q in queries:
            try:
                r = client.get(
                    "https://serpapi.com/search.json",
                    params={
                        "engine": "google",
                        "q": q,
                        "api_key": api_key,
                    },
                    headers={"User-Agent": "company-email-extractor/0.1"},
                )
                r.raise_for_status()
                data = r.json()
            except Exception:
                continue

            organic = data.get("organic_results") or []
            for item in organic:
                title = str(item.get("title") or "")
                snippet = str(item.get("snippet") or "")
                link = str(item.get("link") or "")
                if title:
                    texts.append(title)
                if snippet:
                    texts.append(snippet)
                if link:
                    texts.append(link)

    return texts

