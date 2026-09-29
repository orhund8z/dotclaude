# n8n job radar — webhook contract, test, and follow-up prompt

The scanner pushes its rows to an n8n workflow ("ATS intake") that upserts them into a Data Table `jobs`.
A second workflow ("Daily report") adds LinkedIn job-alert emails from Gmail and mails one PDF report.

## Webhook contract (scanner → n8n)

`POST https://<instance>.app.n8n.cloud/webhook/job-radar/ats` (production URL, workflow activated),
header `X-Job-Radar-Key: <secret>` (name and secret are configurable). One request per batch of 150 rows:

```json
{
  "scan_date": "2026-09-26", "baseline_run": true, "partial": false, "batch": 1, "batches": 4,
  "jobs": [{
    "key": "ats:greenhouse:grafanalabs:6103688004", "ats": "greenhouse", "company": "Grafana Labs",
    "title": "Staff Software Engineer - Databases SRE | Germany | Remote", "where": "Remote · Germany",
    "bucket": "remote-eu", "score": 93, "pay": "EUR 110k–132k", "signals": ["Java", "AWS"], "flags": [],
    "url": "https://job-boards.greenhouse.io/...", "published": "2026-09-10", "new": false
  }]
}
```

`bucket` is `munich | remote-eu | unknown`. `key` is stable across runs, so re-pushing is idempotent.

## Scanner side

In `local.json` set the URL and, in your shell profile or launchd plist, the secret:

```json
"push": { "url": "https://<instance>.app.n8n.cloud/webhook/job-radar/ats", "header": "X-Job-Radar-Key", "secret_env": "JOB_RADAR_SECRET" }
```

```bash
export JOB_RADAR_SECRET='<same value as in the n8n Header Auth credential>'
python3 scripts/scan_ats_jobs.py --rescore --push-dry-run   # build payload, no POST
python3 scripts/scan_ats_jobs.py --rescore                  # push the cached scan
python3 scripts/scan_ats_jobs.py                            # full scan, then push
```

Exit code 3 means the report was written but the push failed (see the `push` object in the JSON summary).

## Test the workflow without the scanner

```bash
curl -X POST "https://<instance>.app.n8n.cloud/webhook/job-radar/ats" \
  -H "X-Job-Radar-Key: <secret>" -H "Content-Type: application/json" \
  -d '{"scan_date":"2026-09-26","baseline_run":true,"jobs":[{"key":"ats:ashby:test:1","ats":"ashby","company":"Test","title":"Staff Platform Engineer","where":"Remote · Germany","bucket":"remote-eu","score":80,"pay":null,"signals":["AWS"],"flags":[],"url":"https://example.com","published":"2026-09-20","new":true}]}'
```

Expected: HTTP 200 immediately, one row `ats:ashby:test:1` in the table. Missing `jobs` → 400.

## Follow-up prompt for the n8n AI builder (paste as-is)

```
Update the existing job radar workflows in place. Keep node names, credentials (newCredential placeholders),
the existing 'jobs' Data Table, the sticky notes and the Error Workflow assignments. Do not rebuild from scratch.

WORKFLOW A - ATS intake
A1. Respond first, process after. Right after payload validation, return the Respond to Webhook 200 with
    {received: n} (400 stays for a missing/non-array jobs), then continue with the upserts in the same execution.
    The scanner POSTs batches of 150 rows and must never wait for the upserts.
A2. Accept the extra fields the scanner sends (ats, batch, batches, partial). bucket may be 'unknown'.
A3. first_seen for new rows = body.scan_date (not today). Keep the rule: never overwrite first_seen or sent_at
    on update.
A4. Add a small separate workflow "Jobs cleanup" (Schedule, Sundays 03:00 Europe/Berlin) that deletes rows
    with first_seen older than 90 days.

WORKFLOW B - Daily report
B1. Gmail search string must be exactly (with the parentheses):
    (from:jobalerts-noreply@linkedin.com OR from:jobs-noreply@linkedin.com) newer_than:2d -label:job-radar-processed
    built from the sender-list variable.
B2. Cross-source dedupe before the LinkedIn upsert: normalise company (lowercase, remove GmbH|Inc|Ltd|SE|AG|LLC|
    Corp|B.V., strip non-alphanumerics) and title (lowercase, strip non-alphanumerics). Read the rows with
    source='ats' and first_seen in the last 60 days; drop a LinkedIn job when an ATS row has the same
    normalised company and title. Log how many were dropped.
B3. Disable the AI re-rank branch (leave the nodes, deactivated) and add a sticky note "enable after jobs are
    enriched with full descriptions".
B4. Report selection: rows with sent_at empty, tier in (top, good, glance) and first_seen within the last 7 days,
    sorted by score desc, at most 150 rows in total and at most 40 'glance' rows. Rows that do not fit stay
    unsent and roll into the next day's report until the 7 days are over.
B5. Set the workflow timezone to Europe/Berlin (workflow settings) and use it for 'today'.
B6. Add a boolean 'dry_run' (Set node at the top, default false). When true, do everything except: labelling the
    Gmail messages, sending the email, and updating sent_at (log what would have been sent instead).
B7. Keep PDF.co with continueOnFail and the HTML-only fallback.
```
