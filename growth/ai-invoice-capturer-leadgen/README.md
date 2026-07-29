# AI Invoice Capturer — LinkedIn Lead Research Agent

Agentic workflow that researches and drafts outreach for **AI Invoice Capturer** (Factloops' AP invoice automation product). It does **not** log into LinkedIn or automate connection requests/DMs — it uses Claude's web-search tool to find publicly indexed LinkedIn profiles/companies matching the ICP, then drafts a personalized connection note + follow-up DM for a human to review and send manually.

## Why research-only, not automated outreach

Automating LinkedIn login, connection requests, or DMs violates LinkedIn's Terms of Service and risks account restriction. This workflow instead treats LinkedIn outreach the way a human researcher would: search the public web, verify plausible fit, draft the message — then a person sends it.

## What it does

1. Reads the Ideal Customer Profile (`config/icp.yaml`) describing AI Invoice Capturer's target buyers.
2. Uses Claude (`claude-opus-5`) with the server-side web-search tool to find people/companies whose public presence, role, or company matches that ICP.
3. For each lead, drafts:
   - A short, specific LinkedIn connection note (≤300 characters)
   - A follow-up DM to send after the connection is accepted
4. Appends new leads to `output/leads.csv`, deduped against what's already there.

## Setup

```bash
cd growth/ai-invoice-capturer-leadgen
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY
```

## Run

```bash
python -m src.cli --limit 15
```

Output goes to `output/leads.csv` — review every draft before sending anything. The CSV is gitignored so prospect data never gets committed to this repo.

## Configuring the ICP

Edit `config/icp.yaml` to change target personas, geography, or messaging as the product evolves. `prompts/system_prompt.md` controls the researcher's behavior and guardrails (no scraping, no fabricated profiles, message tone) — edit it if you want stricter or looser sourcing rules.

## Scheduling

`.github/workflows/ai-invoice-capturer-leadgen.yml` runs this weekly (and on manual dispatch) and uploads the resulting CSV as a workflow artifact — it does not commit leads into the repo. Add `ANTHROPIC_API_KEY` as a repository secret to enable it.

## Extending

`src/storage.py` is the only place that knows about CSV. Swap it for an Airtable/Notion/Sheets writer if you want leads to land somewhere your team already works, without touching the research logic in `src/agent.py`.
