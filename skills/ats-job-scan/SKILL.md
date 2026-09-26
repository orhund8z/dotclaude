---
name: ats-job-scan
description: Scans every Ashby and Greenhouse job board it can discover (thousands of companies) for roles that fit the user's profile — Munich (on-site/hybrid/remote) or remote open to Germany/Europe/worldwide — scores them, and writes a dated markdown report (optionally published to a doc hub) with 🆕 markers for postings new since the last scan. Use when the user says "run the ATS job scan", "scan Ashby/Greenhouse for jobs", "find new openings across job boards", "what's new since last scan", "re-score the job scan", or wants a recurring job radar that does not depend on knowing company names.
---

# ATS Job Scan Skill

Company-agnostic job radar. Ashby and Greenhouse publish no company index, so this skill **discovers**
board slugs (Common Crawl + local seeds), pulls every board through the public JSON APIs, filters by
location and title, scores fit, and writes `ats-scan-<date>.md`.

It complements `job-tracker` (a watchlist of known companies via web search) and `job-evaluator`
(deep evaluation of one company). This skill answers: **"which companies I have never heard of are hiring
for a role like mine?"** — and stops at posting-text fit; reviews, funding and layoffs are `job-evaluator`'s job.

Everything runs from one Python script (standard library only, Python 3.9+):
`scripts/scan_ats_jobs.py` in this skill's directory. Resolve that directory from the location of this
`SKILL.md` (if it is reached through a symlink, use the real path, e.g. `realpath`); all paths below are relative to it.

---

## Step 0 — Check setup

1. `config.json` (filters, scoring) and `local.json` (paths, publish command) live next to this file and are gitignored.
   - `config.json` missing → the script falls back to `config.example.json`; fine, but tell the user.
   - `local.json` missing → output goes to `reports/` inside the skill and nothing is published. Tell the user to copy `local.example.json` to `local.json` if they want a different output folder or doc-hub publishing.
2. Make sure no scan is already running (`pgrep -f scan_ats_jobs`). Two scans share one cache; never run them concurrently.

## Step 1 — Pick the mode

| Situation | Command |
|---|---|
| Default / "run the scan" / scheduled run | `python3 scripts/scan_ats_jobs.py` |
| User edited `config.json` (terms, weights, thresholds) or asks to "re-score" / "re-filter" | `python3 scripts/scan_ats_jobs.py --rescore` (seconds, no network) |
| User wants newly appeared companies | add `--refresh-slugs` (re-crawls Common Crawl; slug list is otherwise refreshed every 14 days) |
| Remote jobs that state no region should be included | add `--include-unspecified-remote` |
| Ignore the dead-board cache | add `--recheck` |
| Testing a single board | `--slug ashby:nango --seeds-only --max-boards 20 --no-publish` |

**Do not rescan needlessly.** A full scan hits roughly 10,000 boards. If the cache (`~/.cache/ats-job-scan/candidates.json`, or the `cache_dir` in `local.json`) is younger than about 24 h and the user did not ask for fresh data, offer `--rescore` instead of a full scan.

## Step 2 — Run it

A full scan takes roughly **25–35 minutes** (Common Crawl discovery ~15 min on a cold cache, then ~10,000 API calls paced at 4 requests/second per host). Therefore:

- Run it in the background, with stdout (the JSON summary) and stderr (progress) going to separate files, for example under the session scratchpad:
  `python3 scripts/scan_ats_jobs.py > scan-summary.json 2> scan-progress.log`
- Wait for completion with a notification-based watcher (e.g. a Monitor filtered to `boards (`, `[report]`, `[publish]`, `!!`, `Traceback`, and reporting every 1,000 boards at most). Do **not** poll with `sleep` loops, and do not tell the user it is done until the process has exited and the summary JSON exists.
- Never raise `--rps-*` or `--workers` beyond the defaults unless the user asks. The tool adapts by itself: HTTP 429 doubles the spacing and honours `Retry-After`; 15 consecutive failures trip a per-host circuit breaker. If `[rate] ... throttled` appears in the log, mention it.
- If the user interrupts (Ctrl-C), the script writes a **partial** report from what it fetched and keeps its cache; re-running continues cheaply.

## Step 3 — Report back

`stdout` is a single JSON document. Read it (not the 100 KB markdown) and summarise, using only values from it:

- **Headline:** scan date, boards fetched / errors, postings seen, how many are in the report (top / good), Munich vs remote counts, and how many are 🆕 (say "baseline run — no 🆕 yet" if `baseline_run` is true).
- **Top Munich** and **top remote** tables (`top_munich`, `top_remote`: score, company, role, where, pay, link). Mark `new: true` rows with 🆕 and `evaluated_before: true` rows with 📁.
- **Flags worth surfacing:** `pay < €125k?`, `German required?`, `open Nd` (stale posting), `level?`, off-stack penalties.
- **Where the files are:** the report path, and whether it was published (`published`).
- **Caveats, always:** companies are discovered, not enumerated (some are invisible); pay is shown only when the posting states it; "Munich · on-site/hybrid?" means the posting does not say; scores are keyword heuristics on the posting text.

Then offer the next step, don't take it: run `/job-evaluator` on the rows the user picks.

## Data integrity

- Nothing in the chat summary may be invented: every company, title, pay figure, count and link comes from the JSON summary or the report.
- Missing values are written `—` or `not stated`, never estimated. Pay is never guessed from market data here.
- Do not describe a role as a match beyond what the score and signals show; a high score with `⚠` flags is a lead, not a recommendation.
- Do not edit `config.json` or `local.json` unless the user asks. Suggest changes; let them decide.

## Failure modes

| Symptom | Meaning / action |
|---|---|
| `no cached candidates — run a normal scan first` | `--rescore` needs a previous full scan; run without it |
| `!! circuit breaker ... skipping the rest of that host` | one API host failed repeatedly; report is partial for that ATS; retry later |
| Common Crawl `502` / incomplete reads | its index is flaky; requests retry with backoff and a failing crawl is skipped, coverage just shrinks slightly |
| `publish step failed` | markdown is written; run the publish command manually (see `local.json`) |
| 0 matches | filters too tight for today's data; inspect `config.json` (`title.*`, `location.*`, `scoring.min_score`) and `--rescore` |
