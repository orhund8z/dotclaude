# job-tracker

A Claude Code skill that watches a list of companies for job openings matching your profile — and discovers *other* companies working on the same topics that are hiring for the same kind of role.

Each run produces one **self-contained HTML report** with two groups:

- **📌 Tracked Companies** — the watchlist you defined
- **💡 Suggested Companies** — companies found via your topics, included only when they actually have a matching opening

Postings you have not seen before are flagged `🆕`, so running it every other day gives you a diff, not a re-read.

> **No email.** This skill is manual-run by design: you run it, it writes the report, you open the file.

## Usage

Type naturally in Claude Code — no slash command needed:

```
Run the job tracker
```
```
Any new openings at my companies?
```
```
Who else is hiring on event-driven platforms?
```

Output lands in `reports/`:

```
reports/2026-08-02-job-tracker.html
reports/latest.html          # always the most recent run
```

Chat gets a short summary and the list of new postings only.

## Setup

`CONFIG.md` is gitignored — your watchlist, salary floor, and preferences stay local.

```bash
cp CONFIG.example.md CONFIG.md
```

Then fill in:

| Section | What it controls |
|---------|------------------|
| **Candidate Profile** | Optional path to an existing profile (e.g. `job-evaluator`'s `PROFILE.md`) for sharper fit scoring |
| **Tracked Companies** | The explicit watchlist scanned every run |
| **Topics** | Used to *discover* companies not on the watchlist — be specific |
| **Target Roles** | Priority-ordered role titles; synonyms are allowed |
| **Match Filter** | Locations, work model, salary floor, must-haves, deal-breakers |
| **Discovery Settings** | Max suggested companies/topics per run, exclusions |
| **Source Settings** | Toggle individual job boards |
| **Output Settings** | Report directory, filename pattern, timezone, state retention |

The skill reads `CONFIG.md` at the start of every run. It never edits it for you.

## How a run works

1. **Load config** (and profile, if configured).
2. **Load state** from `state/seen-jobs.json` — this is what makes `🆕` meaningful.
3. **Scan tracked companies** across careers pages, Greenhouse/Lever/Ashby, LinkedIn, and the regional boards you enabled.
4. **Discover suggested companies** per topic, then scan them the same way. A suggested company with no matching opening is dropped.
5. **Write the HTML report** from `templates/report.html`, plus `latest.html`.
6. **Update state** — new jobs get `first_seen`, existing jobs get `last_seen`, disappeared jobs are retained (so a reappearing posting is not re-announced) until `state_retention_days`.

Re-running on the same day is idempotent: the second run reports nothing new.

## Data integrity

Zero-hallucination mode, same policy as `job-evaluator`:

- Nothing enters the report that did not come from a live search result.
- Missing values are written `not listed` — never estimated.
- Apply links are never invented; a posting without a real link says `link not available`.
- Fit is `✅` / `⚠️` / `❌`, and `⚠️` is used whenever data is missing — never `✅` on an assumption.
- A posting is only "closed" when a source confirms it; otherwise it is `not seen this run`.

## Report anatomy

- **Header** — run timestamp, scan scope, chips: new / matching / suggested / filtered-out counts
- **📌 Tracked Companies** — one card per company (new postings first), table of matching roles; companies with nothing get a one-line "no matching openings" note rather than being hidden
- **💡 Suggested Companies** — same table, plus a `Why suggested:` line naming the matched topic with a source link
- **🔄 Changes since last run** — new postings, postings no longer visible, new suggestions (omitted on the first run)
- **🔗 Coverage & sources** — every source queried and whether it returned results

The HTML is fully self-contained (inline CSS, no external requests) and follows the system light/dark theme.

## Requirements

Live web search. Works with Claude Code's built-in `WebSearch` / `WebFetch`, and is noticeably better with the **Tavily MCP server**:

```bash
claude mcp add tavily-mcp \
  -e TAVILY_API_KEY=tvly-YOUR_KEY_HERE \
  -- npx -y tavily-mcp
```

Free tier is 1,000 credits/month at [tavily.com](https://tavily.com). Budget roughly **10–20 credits per company per run** at basic search depth — so a 7-company watchlist plus 6 suggested companies costs ~150–250 credits per run. Running every other day fits inside the free tier; tighten `max_suggested_companies` if you run more often. See [`docs/tavily-mcp-setup.md`](../../docs/tavily-mcp-setup.md).

### Permissions

Add to `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "mcp__tavily-mcp__tavily_search",
      "mcp__tavily-mcp__tavily_extract"
    ]
  }
}
```

## Installation

```bash
cp -r skills/job-tracker ~/.claude/skills/
# or symlink:
ln -s $(pwd)/skills/job-tracker ~/.claude/skills/job-tracker
```

Restart Claude Code after installation.

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill definition — config loading, scan/discovery steps, report spec |
| `CONFIG.example.md` | Configuration template — copy to `CONFIG.md` |
| `CONFIG.md` | Your watchlist and filters — **gitignored** |
| `templates/report.html` | Self-contained HTML report template |
| `state/seen-jobs.json` | Run state powering the `🆕` badge — **gitignored**, created on first run |
| `reports/` | Generated reports — **gitignored** |
| `README.md` | This file |

## Related

- [`job-evaluator`](../job-evaluator/) — deep-dive evaluation of a single company (reviews, salary, layoffs, interview prep). `job-tracker` finds the opening; `job-evaluator` tells you whether to take it.

## License

MIT
