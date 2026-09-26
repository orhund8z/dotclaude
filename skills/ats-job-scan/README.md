# ats-job-scan

A Claude Code skill (plus a standalone Python script) that scans **every Ashby and Greenhouse job board it can discover** — thousands of companies you would never think to look up — and reports the roles that fit your profile.

- **Munich** in any work model (on-site, hybrid, remote), or **remote open to Germany / Europe / worldwide**
- Titles such as Staff/Principal/Senior SRE, platform, infrastructure, architect, engineering manager
- Scored on skills, stated pay vs. your threshold, freshness, and penalties (German required, off-stack, stale posting)
- Output: one **date-stamped markdown report** per run, optionally published to a doc hub, with `🆕` on postings that are new since the previous scan

It answers *"who is hiring for a role like mine that I have not heard of?"* It is complementary to [`job-tracker`](../job-tracker/) (a watchlist of known companies) and [`job-evaluator`](../job-evaluator/) (deep evaluation of one company, with reviews, funding and layoffs).

## Usage

In Claude Code, type naturally:

```
Run the ATS job scan
```
```
What's new on Ashby and Greenhouse since the last scan?
```
```
Re-score the job scan (I changed the config)
```

Or run the script directly from the skill folder:

```bash
python3 scripts/scan_ats_jobs.py            # full scan, ~30 min the first time
python3 scripts/scan_ats_jobs.py --rescore  # re-filter the cached scan, takes seconds
```

Progress and logs go to **stderr**; **stdout** is one JSON summary (report path, counts, top Munich and remote rows) that the skill turns into a chat summary.

Reports land in `<output_dir>/ats-scan-YYYY-MM-DD.md`; a second run on the same day overwrites that day's file.

## Install

Link the **whole folder** (it contains the script and your two config files, not just `SKILL.md`):

```bash
ln -s ~/dotclaude/skills/ats-job-scan ~/.claude/skills/ats-job-scan
```

Restart Claude Code and the skill auto-loads. Per project instead: `ln -s ~/dotclaude/skills/ats-job-scan .claude/skills/ats-job-scan`.

## Setup

Two gitignored files hold your personal settings — copy the templates:

```bash
cp config.example.json config.json   # what counts as a match: terms, weights, thresholds
cp local.example.json  local.json    # where things live on this machine
```

**`local.json`** (all keys optional; `~` allowed)

| Key | Purpose |
|-----|---------|
| `output_dir` | Where `ats-scan-<date>.md` is written (default: `reports/` in the skill) |
| `cache_dir` | Slug list, per-board state, seen-jobs, candidate cache (default `~/.cache/ats-job-scan`) |
| `publish_cmd` | Command run after the report is written; `{file}` is replaced with the report path. E.g. `python3 tools/publish_analysis.py {file}` |
| `publish_cwd` | Working directory for `publish_cmd` |
| `company_dirs` | Folders whose sub-folder names are companies you already track. They are guessed as board slugs, and matching results get a `📁` |
| `link_roots` | Folders searched for Ashby/Greenhouse links, to seed the company list |
| `extra_slugs_file` | Optional text file, one `ashby:slug` or `greenhouse:slug` per line (`#` comments allowed) |
| `contact` | Put in the User-Agent so API operators can reach you |

**`config.json`** (the matching rules; edit, then `--rescore`)

| Section | Controls |
|---------|----------|
| `location` | Munich terms; remote and region terms; "weak" region terms (`global`, `worldwide`); title restrictions such as `US`/`LATAM` that veto weak evidence |
| `title` | Strong and generic role words, seniority words, excluded titles (sales, frontend, IT support, …), junior words, point values |
| `skills` | Skill groups with weights and a cap; each group counts once per posting |
| `penalties` | Regex/term penalties (`German required?`, `Founding/always-on`, TS/PHP-only stacks unless you also use Kotlin/Java) |
| `compensation` | Your EUR threshold, bonus/penalty points, fixed FX rates |
| `freshness` | Bonus for young postings, penalty for postings open too long |
| `scoring` | `min_score` shown in the report, tier cut-offs (Top / Good / Worth a glance), row cap for the lowest tier |

## How a run works

1. **Discover** board slugs from Common Crawl (last 12 crawls: `jobs.ashbyhq.com`, `job-boards[.eu].greenhouse.io`, `boards.greenhouse.io`), plus links and folder names from your `local.json`. Cached for 14 days.
2. **Fetch** each board through the public JSON API (Greenhouse `boards-api`, Ashby `posting-api`) — see [Rate limiting](#rate-limiting).
3. **Keep candidates**: title/seniority fits and the job is in Munich or remote. Cached, so filters can be tuned offline.
4. **Filter by location, score, de-duplicate** (same company, same title).
5. **Write the report** (Munich and Remote sections in each tier), update the seen-jobs baseline, run `publish_cmd`, print the JSON summary.

Typical first-run numbers (September 2026): ~10,700 boards, ~214,000 postings seen, ~8,200 candidates, ~510 matches in the report; about half an hour end to end.

### Rate limiting

- Per-host pacing: 4 requests/second each to Ashby and Greenhouse, 1 request/second to Common Crawl (`--rps-ashby`, `--rps-greenhouse`, `--rps-cdx`).
- Adaptive: HTTP 429 doubles the spacing (max 10 s) and honours `Retry-After`; 50 consecutive successes shrink it back.
- Retries with exponential backoff and jitter on 5xx and network errors; 404/410 is treated as "no such board".
- A per-host circuit breaker stops a host after 15 consecutive failures, so one outage cannot stall the run.
- Boards that returned 404 are skipped for 30 days, empty boards for 7 (`--recheck` ignores that).

## Reading the report

| Column | Meaning |
|--------|---------|
| Score | 0–100 heuristic: title (role + seniority) + skills − penalties ± pay ± freshness |
| Where | `Munich · Hybrid`, `Remote · Germany`, `Remote · EMEA`, … `on-site/hybrid?` means the posting does not say |
| Pay | Only when the posting states it (Ashby structured data, or a range parsed from the text); converted with the fixed FX rates in `config.json` |
| Fit signals | Matched skill groups; `⚠` lists things to check (`level?`, `German required?`, `pay < €125k?`, `open 315d`, off-stack) |
| 🆕 / 📁 | New posting since the last scan / company already has a folder in `company_dirs` |

The first run is the baseline: no `🆕` markers. From the next run on, `🆕` means the posting was not in the previous candidate set (rule changes alone do not trigger it).

## Running it regularly

The skill is manual-run by design (a scan takes about half an hour, so run it weekly rather than daily). Two ways to automate:

**cron** (weekly, Monday 07:30):

```cron
30 7 * * 1  cd ~/dotclaude/skills/ats-job-scan && /usr/bin/python3 scripts/scan_ats_jobs.py >/tmp/ats-job-scan.json 2>>/tmp/ats-job-scan.log
```

**launchd** (macOS) — save as `~/Library/LaunchAgents/dev.ats-job-scan.plist`, then `launchctl load` it:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>dev.ats-job-scan</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string>
    <string>/Users/YOU/dotclaude/skills/ats-job-scan/scripts/scan_ats_jobs.py</string>
  </array>
  <key>StartCalendarInterval</key><dict>
    <key>Weekday</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>30</integer>
  </dict>
  <key>StandardOutPath</key><string>/tmp/ats-job-scan.json</string>
  <key>StandardErrorPath</key><string>/tmp/ats-job-scan.log</string>
</dict></plist>
```

Scheduled runs write the dated report and run `publish_cmd`; open the report (or ask Claude "what's new in the ATS scan?") afterwards.

## Tuning workflow

1. Open the latest report, note what should have been filtered out or ranked higher.
2. Edit `config.json` (`title.exclude`, `skills`, `penalties`, `scoring`).
3. `python3 scripts/scan_ats_jobs.py --rescore` — regenerates the report from the cached candidates in seconds.

## Limits

- **Discovery, not enumeration.** Common Crawl only knows pages it crawled; a company never crawled is invisible. Add known companies to `extra_slugs_file`.
- **Posting text only.** No employee reviews, funding or layoffs — use `job-evaluator` on the shortlist.
- **Heuristic scoring.** Keyword matching can rank a security-heavy or off-stack role too high; the `⚠` flags and `level?` help, judgement is still yours.
- **Pay is sparse.** Most postings state none, and USD/GBP are converted at fixed rates.
- **Region rules are conservative.** A bare "Remote" without a region is excluded by default (usually US-only); `--include-unspecified-remote` lists them, marked as unverified. Country-specific remote roles (for example "Remote — Ireland") are excluded because they are not open to someone living in Germany.
- **No login-gated boards.** Only public API data is used.

## Requirements

Python 3.9+ and network access. No third-party packages.
