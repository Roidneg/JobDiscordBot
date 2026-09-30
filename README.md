# Discord Job Intelligence

A free-first Python job-monitoring pipeline that collects public job postings from Lever and Ashby, filters and scores them, deduplicates previously posted roles, and sends a daily digest to Discord through a webhook.

## MVP

- Lever public postings
- Ashby public postings
- Remote-role filtering
- Keyword-weighted scoring
- Cross-run deduplication
- Discord embeds
- Daily GitHub Actions schedule
- No paid API required

## 1. Create a Discord webhook

In Discord:

1. Open your server.
2. Open **Server Settings → Integrations → Webhooks**.
3. Create a webhook for the channel that should receive jobs.
4. Copy the webhook URL.

Never commit that URL to GitHub.

## 2. Configure job boards

Edit `config/search.yaml`.

For Lever, add the site slug from a URL like:

`https://jobs.lever.co/companyslug`

For Ashby, add the board name from:

`https://jobs.ashbyhq.com/CompanyName`

Example:

```yaml
sources:
  lever:
    - company: Example Company
      site: example
  ashby:
    - company: Example AI
      board: ExampleAI
```

Delete the sample entries until you replace them with real companies.

## 3. Local setup

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DISCORD_WEBHOOK_URL="YOUR_WEBHOOK_URL"
python -m src.main
```

Without `DISCORD_WEBHOOK_URL`, the program runs in dry-run mode and prints matching jobs instead of posting them.

## 4. Add the GitHub secret

In your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

Name:

`DISCORD_WEBHOOK_URL`

Paste the webhook URL as the value.

## 5. Daily automation

`.github/workflows/daily-jobs.yml` runs every day at 7:30 AM in `America/Chicago`.

The workflow also commits `data/seen_jobs.json` so jobs already sent to Discord do not get reposted on later runs.

## Search tuning

The default profile targets roles around:

- AI / technical project management
- AI program management
- AI evaluation / QA
- data analytics
- responsible AI / governance
- AI technical writing
- product / AI operations

Edit `config/search.yaml` to change title terms, scoring weights, excluded locations, or the score threshold.

## Run tests

```bash
pytest
```

## Next milestones

1. Add Greenhouse.
2. Add richer location parsing.
3. Add salary normalization.
4. Add description-based scoring.
5. Add optional LLM ranking.
6. Add multiple Discord channels by score/category.
7. Add a lightweight dashboard and application tracker integration.
