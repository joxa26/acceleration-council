# Vendorix — Lead Research Agent

Agentic workflow that researches and drafts outreach for **Vendorix** (formerly AI Invoice Capturer), Factloops' AP invoice automation product. It does **not** log into LinkedIn or automate connection requests/DMs — it uses Claude's web-search tool to find publicly indexed profiles/companies matching the ICP, then drafts a personalized connection note + follow-up DM for a human to review and send manually.

## Why research-only, not automated outreach

Automating LinkedIn login, connection requests, or DMs violates LinkedIn's Terms of Service and risks account restriction. This workflow instead treats outreach the way a human researcher would: search the public web, verify plausible fit, draft the message — then a person sends it.

## What it does

1. Reads the Ideal Customer Profile (`config/icp.yaml`) describing Vendorix's target buyers.
2. Uses Claude (`claude-opus-5`) with the server-side web-search tool to find people/companies whose public presence, role, or company matches that ICP.
3. For each lead, drafts (in **Serbian** by default — see below):
   - A short, specific LinkedIn connection note (≤300 characters)
   - A follow-up DM to send after the connection is accepted
4. Writes new leads straight into the **Leads** database under the Vendorix Lead Capturer Notion page (deduped against what's already there), or to a local CSV if Notion isn't configured.

## Outreach language

Vendorix's initial target market is Serbian companies, so `connection_note`, `followup_dm`, and `fit_reason` are drafted in natural, fluent business Serbian (Latin script, formal "Vi" register) by default. Leads that are clearly part of the secondary English-speaking market (see `config/icp.yaml` → `geography`) get English outreach instead. Factual fields (name, title, company, URLs) are never translated. Edit `prompts/system_prompt.md` → `## Language` if you want a different default.

## Setup

```bash
cd growth/vendorix-leadgen
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

- `ANTHROPIC_API_KEY` — https://console.anthropic.com/settings/keys
- `NOTION_API_KEY` — create an internal integration at https://www.notion.so/my-integrations, then open the **Vendorix Lead Capturer** page in Notion → `···` menu → **Connections** → add your integration so it can read/write the Leads database.
- `NOTION_DATABASE_ID` — already filled in for you; it's the ID of the existing Leads database.

If you skip the Notion variables, the script falls back to writing `output/leads.csv` locally instead — useful for testing without touching the real database.

## Run

```bash
python -m src.cli --limit 15
```

Each new lead lands in Notion with `Status = New`. Review every draft before sending anything, then update `Status` as you work the pipeline (`Reviewing` → `Sent` → `Connected` → `Replied`, or `Not a fit`).

## Notion schema

| Column | Type | Filled by |
|---|---|---|
| Name | title | agent |
| Title | text | agent |
| Company | text | agent |
| LinkedIn Profile | url | agent (only if a real, verified profile URL was found) |
| Contact/Email | email | agent, only if publicly listed — never guessed |
| Connection Note | text | agent — the ≤300 char connection request (Serbian by default) |
| Outreach Message | text | agent — the follow-up DM sent after connecting (Serbian by default) |
| Fit Reason | text | agent — why this lead matches the ICP, for quick review (Serbian by default) |
| Source URL | url | agent — the page the lead was found/verified on |
| Status | select | defaults to `New`; you update it as leads progress |

## Configuring the ICP

Edit `config/icp.yaml` to change target personas, geography, or messaging as the product evolves. `prompts/system_prompt.md` controls the researcher's behavior and guardrails (no scraping, no fabricated profiles/emails, message tone, outreach language) — edit it if you want stricter or looser sourcing rules.

## Scheduling

`.github/workflows/vendorix-leadgen.yml` runs this weekly (and on manual dispatch). Add `ANTHROPIC_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID` as repository secrets to have it write straight into Notion; if you omit the Notion secrets it uploads the CSV as a workflow artifact instead.

## Extending

`src/notion_store.py` and `src/storage.py` both implement the same two-function interface (`load_existing_keys`, `append_leads`). Swap in another backend (Airtable, Sheets) the same way without touching the research logic in `src/agent.py`.
