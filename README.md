# Discord Job Intelligence

A free-first Python job-monitoring pipeline that collects public job postings from Lever, Ashby, Greenhouse, and Himalayas, filters and scores them, deduplicates previously posted roles, and sends a daily digest to Discord through a webhook.

## MVP

- Lever public postings
- Ashby public postings
- Greenhouse public postings
- Himalayas remote-jobs API
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

For Greenhouse, add the board token from:

`https://job-boards.greenhouse.io/companytoken`

Himalayas searches are configured under `sources.himalayas`. The default searches cover the job categories in this project. `max_pages` limits API requests per search; `max_age_days` prevents older listings from filling the first digest. Results must allow U.S. applicants and pass the same title, remote, and score filters as other sources. Himalayas asks that reused listings link back to its job page and name Himalayas as the source; the Discord embed does both.

Example:

```yaml
sources:
  lever:
    - company: Example Company
      site: example
  ashby:
    - company: Example AI
      board: ExampleAI
  greenhouse:
    - company: Example Data
      board: exampledata
  himalayas:
    queries:
      - project manager
      - data analyst
    max_pages: 2
    max_age_days: 14
```

The default configuration includes verified boards for DataHub, Innodata, Neo4j, and Grafana Labs. Add or remove boards in the same format; the remote and location filters still apply to every source. Himalayas data refreshes daily and its API may return HTTP 429 when rate limited; reduce searches or pages if that happens.

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
python -m pytest -q
```

## Next milestones

1. Expand the company board list.
2. Add richer location parsing.
3. Add salary normalization.
4. Add description-based scoring.
5. Add optional LLM ranking.
6. Add multiple Discord channels by score/category.
7. Add a lightweight dashboard and application tracker integration.
