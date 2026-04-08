from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class InputRow:
    company: str
    url: str
    row_index: int


@dataclass(frozen=True)
class CompanyEmailResult:
    row_index: int
    company: str
    input_url: str
    normalized_url: Optional[str]
    emails: Sequence[str]
    source_notes: str

    @property
    def email_count(self) -> int:
        return len(self.emails)

    def to_dict(self) -> dict:
        return {
            "row_index": self.row_index,
            "company": self.company,
            "input_url": self.input_url,
            "normalized_url": self.normalized_url or "",
            "emails": "; ".join(self.emails),
            "email_count": self.email_count,
            "source_notes": self.source_notes,
        }

