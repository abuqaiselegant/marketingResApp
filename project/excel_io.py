from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from project.models import CompanyEmailResult, InputRow


_COMPANY_COL_CANDIDATES = ["company", "company_name", "name"]
_URL_COL_CANDIDATES = ["website", "url", "domain", "site", "web"]


def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    lowered = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lowered:
            return str(lowered[cand])
    return None


def read_companies_from_excel(
    path: Path, *, company_col: Optional[str] = None, url_col: Optional[str] = None
) -> list[InputRow]:
    df = pd.read_excel(path)

    resolved_company_col = company_col or _find_col(df, _COMPANY_COL_CANDIDATES)
    resolved_url_col = url_col or _find_col(df, _URL_COL_CANDIDATES)
    if not resolved_company_col or not resolved_url_col:
        raise ValueError(
            "Could not auto-detect required columns. "
            "Pass --company-col and --url-col explicitly."
        )

    rows: list[InputRow] = []
    for idx, r in df.iterrows():
        company = "" if pd.isna(r[resolved_company_col]) else str(r[resolved_company_col]).strip()
        url = "" if pd.isna(r[resolved_url_col]) else str(r[resolved_url_col]).strip()
        rows.append(InputRow(company=company, url=url, row_index=int(idx)))
    return rows


def write_results_to_excel(
    *,
    in_path: Path,
    out_path: Path,
    results: Iterable[CompanyEmailResult],
) -> None:
    df = pd.read_excel(in_path)

    result_by_idx = {r.row_index: r for r in results}

    normalized_urls = []
    emails = []
    email_counts = []
    source_notes = []

    for idx, _ in df.iterrows():
        r = result_by_idx.get(int(idx))
        if r is None:
            normalized_urls.append("")
            emails.append("")
            email_counts.append(0)
            source_notes.append("none")
        else:
            normalized_urls.append(r.normalized_url or "")
            emails.append("; ".join(r.emails))
            email_counts.append(r.email_count)
            source_notes.append(r.source_notes)

    df["normalized_url"] = normalized_urls
    df["emails"] = emails
    df["email_count"] = email_counts
    df["source_notes"] = source_notes

    df.to_excel(out_path, index=False)

