"""Notion storage backend — writes researched leads into the Vendorix Lead
Capturer "Leads" database and dedupes against what's already there.
"""
from __future__ import annotations

from notion_client import Client

STATUS_NEW = "New"

# Notion property names on the "Leads" data source (note the trailing space
# on "Name " — it's part of the actual column name in Notion).
PROP_NAME = "Name "
PROP_TITLE = "Title"
PROP_COMPANY = "Company"
PROP_LINKEDIN = "LinkedIn Profile"
PROP_EMAIL = "Contact/Email"
PROP_OUTREACH_MESSAGE = "Outreach Message"
PROP_CONNECTION_NOTE = "Connection Note"
PROP_FIT_REASON = "Fit Reason"
PROP_SOURCE_URL = "Source URL"
PROP_STATUS = "Status"


def _client(api_key: str) -> Client:
    return Client(auth=api_key, notion_version="2022-06-28")


def _rich_text(value: str | None) -> list[dict]:
    if not value:
        return []
    return [{"text": {"content": value[:2000]}}]


def _plain_text(rich_text_list: list[dict] | None) -> str:
    return "".join(block.get("plain_text", "") for block in (rich_text_list or []))


def _key(lead: dict) -> str:
    url = (lead.get("linkedin_profile_url") or "").strip().lower()
    if url:
        return url
    return f"{lead.get('name', '').strip().lower()}|{lead.get('company', '').strip().lower()}"


def load_existing_keys(api_key: str, database_id: str) -> set[str]:
    client = _client(api_key)
    keys: set[str] = set()
    cursor = None
    while True:
        response = client.databases.query(
            database_id=database_id,
            start_cursor=cursor,
            page_size=100,
        )
        for page in response["results"]:
            props = page["properties"]
            linkedin = (props.get(PROP_LINKEDIN) or {}).get("url") or ""
            name = _plain_text((props.get(PROP_NAME) or {}).get("title"))
            company = _plain_text((props.get(PROP_COMPANY) or {}).get("rich_text"))
            keys.add(_key({
                "linkedin_profile_url": linkedin,
                "name": name,
                "company": company,
            }))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return keys


def append_leads(api_key: str, database_id: str, leads: list[dict]) -> int:
    existing = load_existing_keys(api_key, database_id)
    client = _client(api_key)
    added = 0
    for lead in leads:
        if _key(lead) in existing:
            continue
        properties = {
            PROP_NAME: {"title": _rich_text(lead.get("name") or "Unknown")},
            PROP_TITLE: {"rich_text": _rich_text(lead.get("title"))},
            PROP_COMPANY: {"rich_text": _rich_text(lead.get("company"))},
            PROP_LINKEDIN: {"url": lead.get("linkedin_profile_url") or None},
            PROP_EMAIL: {"email": lead.get("contact_email") or None},
            PROP_OUTREACH_MESSAGE: {"rich_text": _rich_text(lead.get("followup_dm"))},
            PROP_CONNECTION_NOTE: {"rich_text": _rich_text(lead.get("connection_note"))},
            PROP_FIT_REASON: {"rich_text": _rich_text(lead.get("fit_reason"))},
            PROP_SOURCE_URL: {"url": lead.get("source_url") or None},
            PROP_STATUS: {"select": {"name": STATUS_NEW}},
        }
        client.pages.create(parent={"database_id": database_id}, properties=properties)
        added += 1
    return added
