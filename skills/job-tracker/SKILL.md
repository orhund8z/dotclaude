---
name: job-tracker
description: Tracks a watchlist of companies for job openings that match the user's profile, and discovers additional companies working on the same topics. Produces a self-contained HTML report with two groups — "Tracked Companies" and "Suggested Companies" — and marks which postings are new since the previous run. Use this skill when the user says "check job openings", "run the job tracker", "any new jobs at my companies", "who else is hiring on <topic>", or asks to refresh/rerun the job report.
---

# Job Tracker Skill

Run-on-demand job radar. Every run answers two questions:

1. **Did the companies I follow open a role that fits me?**
2. **Which other companies working on my topics are hiring a role that fits me?**

The output is a single self-contained HTML report. This skill does **not** send email —
delivery is out of scope; the user runs it manually (typically every other day) and reads the file.

---

## Step 0 — Load Configuration

Before anything else, read `CONFIG.md` in the same directory as this skill.

It defines:

- **Tracked companies** — the explicit watchlist
- **Topics** — the domains/technologies used to discover *suggested* companies
- **Target roles**, **locations / work model**, **salary floor**, **must-haves** and **deal-breakers** — the match filter
- **Discovery settings** — how many suggested companies per run, exclusions
- **Output settings** — report directory, filename pattern, timezone

If `CONFIG.md` does not exist, tell the user to copy `CONFIG.example.md` to `CONFIG.md` and fill it in. Do not proceed with guessed values.

If `CONFIG.md` points to a candidate profile file (e.g. the `job-evaluator` skill's `PROFILE.md`), read that too and use it to sharpen the fit assessment. If it points to a file that does not exist, continue with `CONFIG.md` alone and note this in the report footer.

---

## Step 1 — Load Previous State

Read `state/seen-jobs.json` (same directory as this skill). Shape:

```json
{
  "last_run": "2026-08-02T09:14:00+02:00",
  "jobs": {
    "<stable-job-id>": {
      "company": "Acme",
      "title": "Principal Engineer",
      "url": "https://...",
      "group": "tracked | suggested",
      "first_seen": "2026-07-29",
      "last_seen": "2026-08-02"
    }
  },
  "suggested_companies": {
    "Acme": { "topic": "streaming platforms", "first_suggested": "2026-07-29" }
  }
}
```

- `<stable-job-id>` = lowercase slug of `company|title|location`, with the canonical apply URL as tiebreaker. Use the same rule every run so IDs stay comparable.
- If the file is missing, this is the first run: treat every posting as new but say so explicitly in the report header (otherwise the "🆕 new" badge is meaningless).
- Never delete the file. Rewrite it at the end of the run (Step 5).

---

## Step 2 — Scan Tracked Companies

For every company in the watchlist, search for currently open roles matching the target roles from `CONFIG.md`. Parallelize searches across companies.

Sources, per company (skip any the config disables):

1. **Careers page:** `[company] careers [target role]`
2. **Greenhouse / Lever / Ashby ATS:** `[company] site:job-boards.greenhouse.io`, `site:jobs.lever.co`, `site:jobs.ashbyhq.com`
3. **LinkedIn Jobs:** `[company] [target role] jobs [location]`
4. **Local/regional boards from config** (e.g. Indeed, Xing, Hiring.cafe, Builtin, Wellfound, Remotely.de)

For each posting found, capture: title, location, work model, posted date, salary if listed, apply URL.

Then apply the **match filter** from `CONFIG.md`:

- Title must map to one of the target roles (allow reasonable synonyms — "Staff Engineer" ≈ "Principal Engineer" if the config lists both levels).
- Location / work model must satisfy the configured preference.
- If a salary is listed and is below the floor → keep it, but mark `❌` on the salary criterion. Never silently drop it.
- If a deal-breaker from config is explicitly present in the posting → exclude it and count it under "filtered out".

Roles that fail the filter are **not** listed individually — only counted.

---

## Step 3 — Discover Suggested Companies

For each topic in `CONFIG.md`, find companies working on that topic that are **not** already on the watchlist and **not** in the config's exclusion list.

Search patterns per topic:

- `companies working on [topic] [region]`
- `[topic] startups hiring [target role] [region]`
- `[topic] [target role] jobs [region]`
- `site:hiring.cafe [topic] [target role]` / `site:wellfound.com [topic]` / `site:builtin.com [topic]`

Then, for each candidate company, run the same opening scan as Step 2. **Only include a suggested company in the report if it currently has at least one matching open role** — a company with no matching opening is noise, not a suggestion.

Respect `max_suggested_companies` from the config. Rank by: (1) strength of topic match, (2) number of matching openings, (3) whether it is new since the last run.

Carry `suggested_companies` forward in state so the report can distinguish a first-time suggestion from a recurring one.

---

## Step 4 — Data Integrity Policy

This skill runs in **strict zero-hallucination mode**:

- Never infer, estimate, or fabricate a posting, a salary, a location, or a company's topic focus. If it is not in a search result, it does not go in the report.
- Missing values are written as `not listed` — never guessed from training data.
- Never invent an apply URL. A posting without a real link is reported with the source that mentioned it and `link not available`.
- If a source returns nothing for a company, record it as `no results` in the coverage table rather than omitting it.
- Do not claim a posting is new unless it is genuinely absent from `state/seen-jobs.json`.
- Do not mark a posting closed unless the source confirms it is gone; if it merely was not seen this run, say `not seen this run`.

---

## Step 5 — Write the Report

Render a **self-contained HTML file** (all CSS inline in a `<style>` tag, no external requests, no CDN links) to the output directory from `CONFIG.md` — default `reports/`.

- Filename: `reports/YYYY-MM-DD-job-tracker.html` (per the config pattern).
- Also write/overwrite `reports/latest.html` with identical content so the user always has one stable path to open.
- If a report for today already exists, ask before overwriting it.

Use `templates/report.html` as the base — replace its placeholder blocks; keep the styling, the light/dark handling, and the two-group structure.

### Report structure

**Header**
- Run timestamp, number of tracked companies scanned, number of topics, first-run notice if applicable.
- Summary chips: `X new postings`, `Y total matching`, `Z suggested companies`.

**Group 1 — 📌 Tracked Companies**

One block per tracked company, companies with new postings first, then companies with matches, then companies with none.

| Title | Location | Work Model | Salary | Posted | Fit | Link |
|-------|----------|------------|--------|--------|-----|------|

- Prefix new postings with a `🆕` badge; postings seen in an earlier run get no badge.
- `Fit` is `✅` / `⚠️` / `❌` with a short reason on hover/next to it, derived from the config filter (and the profile file if present). Use `⚠️` whenever data is missing — never `✅` on an assumption.
- Companies with zero matching openings still get a one-line row: `No matching openings found — sources checked: N`.

**Group 2 — 💡 Suggested Companies**

Same table shape, plus per company:
- `Why suggested:` one sentence naming the matched topic and the evidence found (with source link).
- `🆕 first suggested this run` badge where applicable.

**Changes since last run**
- New postings (grouped by company)
- Postings no longer visible (`not seen this run` vs. confirmed closed)
- New companies entering the suggestion list

Omit this section entirely on a first run.

**Coverage & sources footer**
- Table of every source queried and whether it returned results.
- Config file used, profile file used (or "none"), previous run timestamp.

### Then update state

Rewrite `state/seen-jobs.json`:
- Add newly found jobs with `first_seen` = today.
- Update `last_seen` on jobs still present.
- Keep jobs that disappeared (do not delete) so a reappearing posting is not re-announced as new; drop entries whose `last_seen` is older than `state_retention_days` from the config (default 90).
- Update `last_run` and `suggested_companies`.

---

## Step 6 — Report Back in Chat

After writing the file, print a short summary (not the whole report):

```
Job tracker run — 2026-08-02
  📌 Tracked:   3 new postings across 2 of 7 companies
  💡 Suggested: 4 companies with matching roles (2 new)
  Report: reports/2026-08-02-job-tracker.html (also latest.html)
```

Then list only the **new** postings as one line each: `Company — Title — Location — link`.

---

## Behavioural Rules

- Write the report in **English** regardless of the user's input language.
- The report is the deliverable — always write the file, even if nothing new was found (an empty run is a valid, useful result).
- Never send email, and never suggest a delivery mechanism unless the user asks — this skill is manual-run by design.
- Never modify `CONFIG.md` on the user's behalf. If the config looks wrong (e.g. no topics defined), say so and continue with what is there.
- Re-running on the same day must be idempotent: the second run marks nothing new, because the first run already recorded it.
- Keep every run's searches bounded — the config's company and topic counts are the budget. Do not fan out into unrelated companies.
