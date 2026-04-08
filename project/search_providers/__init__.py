from __future__ import annotations

from typing import Optional

from project.extract_emails import extract_emails_from_text, merge_emails


def extract_emails_via_search(
    *,
    provider: str,
    company: str,
    normalized_url: Optional[str],
    serpapi_key: Optional[str] = None,
    timeout_s: float = 15.0,
) -> list[str]:
    provider_l = (provider or "").strip().lower()
    if provider_l in ("serpapi", "serp"):
        from project.search_providers.serpapi import serpapi_search_texts

        if not serpapi_key:
            return []
        texts = serpapi_search_texts(
            company=company,
            normalized_url=normalized_url,
            api_key=serpapi_key,
            timeout_s=timeout_s,
        )
        emails: list[str] = []
        for t in texts:
            emails = merge_emails(emails, extract_emails_from_text(t))
        return emails

    # Unknown provider (or not implemented yet)
    return []

