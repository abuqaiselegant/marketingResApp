from __future__ import annotations

import re
from typing import Optional

from project.crawl import CrawlSettings, crawl_site
from project.extract_emails import extract_emails_from_text, merge_emails
from project.models import CompanyEmailResult
from project.normalize import domain_from_url, normalize_url
from project.search_providers import extract_emails_via_search


_PLACEHOLDER_LOCALPARTS = {
    "example",
    "test",
    "testing",
    "infoexample",
}

_BLOCKED_EMAIL_DOMAINS = {
    # Common “fake”/demo addresses that often appear in templates/snippets.
    "example.com",
    "example.org",
    "example.net",
    # Form/automation artifacts that are not useful as business contact emails.
    "webform.boxly.ai",
}

_GENERIC_TRASH_PATTERNS = [
    re.compile(r"(?i)^noreply@"),
    re.compile(r"(?i)^no-reply@"),
    re.compile(r"(?i)^donotreply@"),
    re.compile(r"(?i)^do-not-reply@"),
]


def _looks_like_trash(email: str) -> bool:
    e = (email or "").strip().lower()
    if "@" not in e:
        return True
    local, domain = e.split("@", 1)
    if not local or not domain:
        return True
    if local in _PLACEHOLDER_LOCALPARTS:
        return True
    if domain in _BLOCKED_EMAIL_DOMAINS:
        return True
    if any(p.search(e) for p in _GENERIC_TRASH_PATTERNS):
        return True
    return False


def _filter_emails_for_site(emails: list[str], normalized_url: Optional[str]) -> list[str]:
    """
    Keep emails that look real, and if we know the site domain, prefer matching-domain emails.
    """
    cleaned = [e for e in emails if e and not _looks_like_trash(e)]
    site_domain = domain_from_url(normalized_url or "") or ""
    if not site_domain:
        return cleaned

    site_domain = site_domain.lstrip(".").lower()

    def matches_site(e: str) -> bool:
        try:
            d = e.strip().lower().split("@", 1)[1]
        except Exception:
            return False
        return d == site_domain or d.endswith("." + site_domain)

    matching = [e for e in cleaned if matches_site(e)]
    return matching if matching else cleaned


def extract_emails_for_company(
    *,
    company: str,
    url: str,
    max_pages: int = 8,
    timeout_s: float = 15.0,
    use_search: bool = False,
    search_provider: str = "serpapi",
    serpapi_key: Optional[str] = None,
) -> CompanyEmailResult:
    norm = normalize_url(url)
    normalized_url = norm.normalized

    emails_onsite: list[str] = []
    crawl_report_note = ""
    if normalized_url:
        pages, report = crawl_site(
            normalized_url,
            settings=CrawlSettings(max_pages=max_pages, timeout_s=timeout_s),
        )
        for _, html in pages:
            emails_onsite = merge_emails(emails_onsite, extract_emails_from_text(html))
        crawl_report_note = (
            f"crawl(attempted={report.attempted}, html={report.fetched_html}, "
            f"blocked={report.blocked}, non_html={report.non_html}, errors={report.errors}, "
            f"last_status={report.last_status})"
        )
    else:
        crawl_report_note = f"normalize({norm.reason})"

    emails_search: list[str] = []
    if use_search and not emails_onsite:
        emails_search = extract_emails_via_search(
            provider=search_provider,
            company=company,
            normalized_url=normalized_url,
            serpapi_key=serpapi_key,
            timeout_s=timeout_s,
        )

    all_emails_raw = merge_emails(emails_onsite, emails_search)
    all_emails = _filter_emails_for_site(list(all_emails_raw), normalized_url)
    filtered_note = f"filtered={len(all_emails)}/{len(all_emails_raw)}"

    if emails_onsite and emails_search:
        source_notes = "both " + filtered_note
    elif emails_onsite:
        source_notes = "onsite " + crawl_report_note + " " + filtered_note
    elif emails_search:
        source_notes = "search_api " + filtered_note
    else:
        source_notes = "none " + crawl_report_note + " " + filtered_note

    return CompanyEmailResult(
        row_index=-1,  # excel layer overwrites; single-url uses -1
        company=company,
        input_url=url,
        normalized_url=normalized_url,
        emails=all_emails,
        source_notes=source_notes,
    )

