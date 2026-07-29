"""CSV storage for researched leads — dedupes by LinkedIn URL, else name+company."""
import csv
from pathlib import Path

FIELDS = [
    "name",
    "title",
    "company",
    "company_domain",
    "linkedin_profile_url",
    "source_url",
    "fit_reason",
    "connection_note",
    "followup_dm",
]


def _key(lead: dict) -> str:
    url = (lead.get("linkedin_profile_url") or "").strip().lower()
    if url:
        return url
    return f"{lead.get('name', '').strip().lower()}|{lead.get('company', '').strip().lower()}"


def load_existing_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as f:
        return {_key(row) for row in csv.DictReader(f)}


def append_leads(path: Path, leads: list[dict]) -> int:
    existing = load_existing_keys(path)
    new_rows = [lead for lead in leads if _key(lead) not in existing]
    if not new_rows:
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(new_rows)
    return len(new_rows)
