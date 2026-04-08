from __future__ import annotations

import re
from typing import Iterable


_EMAIL_RE = re.compile(
    r"(?i)(?<![a-z0-9._%+-])([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})(?![a-z0-9._%+-])"
)

# Very small set of common obfuscations.
_OBFUSCATIONS = [
    (re.compile(r"(?i)\s*\[\s*at\s*\]\s*"), "@"),
    (re.compile(r"(?i)\s*\(\s*at\s*\)\s*"), "@"),
    (re.compile(r"(?i)\s+at\s+"), "@"),
    (re.compile(r"(?i)\s*\[\s*dot\s*\]\s*"), "."),
    (re.compile(r"(?i)\s*\(\s*dot\s*\)\s*"), "."),
    (re.compile(r"(?i)\s+dot\s+"), "."),
]


def _deobfuscate(text: str) -> str:
    s = text
    for pattern, repl in _OBFUSCATIONS:
        s = pattern.sub(repl, s)
    return s


def extract_emails_from_text(text: str) -> list[str]:
    if not text:
        return []
    t = _deobfuscate(text)
    found = [m.group(1) for m in _EMAIL_RE.finditer(t)]
    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for e in found:
        el = e.lower()
        if el not in seen:
            seen.add(el)
            out.append(e)
    return out


def merge_emails(*email_lists: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for lst in email_lists:
        for e in lst:
            el = e.lower()
            if el not in seen:
                seen.add(el)
                out.append(e)
    return out

