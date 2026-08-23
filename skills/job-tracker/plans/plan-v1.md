# job-tracker — Plan v1

**Status:** draft, awaiting review
**Date:** 2026-08-07
**Scope:** design of the `job-tracker` Claude Code skill (already scaffolded under `skills/job-tracker/`)

---

## 1. Goal

A run-on-demand job radar that answers two questions on every run:

1. **Did the companies I follow open a role that fits me?**
2. **Which *other* companies working on my topics are hiring the same kind of role?**

Output is a single self-contained HTML report the user opens manually, typically every other day.

---

## 2. Decisions taken

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **No email delivery.** Manual run, file output. | User's call — email adds SMTP/OAuth setup and a background scheduler for value that a file open already provides. |
| D2 | **HTML report**, self-contained (inline CSS, no external requests), light/dark aware. | Portable, opens anywhere, survives being copied out of the repo. |
| D3 | **Separate config file** `CONFIG.md`, gitignored. | Watchlist, salary floor and deal-breakers are personal. Copied from `CONFIG.example.md`. |
| D4 | **Persistent state** in `state/seen-jobs.json`. | Without it "new posting" is meaningless on a repeat run — the 🆕 badge is the whole point of running every other day. |
| D5 | **Suggested companies are listed only if they currently have a matching opening.** | A company that merely works on your topic is noise, not a suggestion. |
| D6 | **Non-matching roles are counted, not listed.** Postings below the salary floor are kept but marked ❌. | Keeps the report short without silently hiding a role that might still be worth a look. |
| D7 | **Zero-hallucination mode**, inherited verbatim from `job-evaluator`. | Consistency across the two career skills; a fabricated apply link is worse than no link. |
| D8 | **Profile file is optional**, pointed at from `CONFIG.md` (defaults to `job-evaluator/PROFILE.md`). | Avoids duplicating stack/salary/location in two files. |
| D9 | **Same-day re-runs are idempotent.** | Second run reports nothing new because the first already recorded it. |

---

## 3. File layout

```
skills/job-tracker/
├── SKILL.md                 # skill definition — the executable spec
├── CONFIG.example.md        # config template
├── CONFIG.md                # user's real config      [gitignored]
├── templates/report.html    # HTML report template
├── state/seen-jobs.json     # run state              [gitignored, created on 1st run]
├── reports/                 # generated reports      [gitignored]
├── plans/plan-v1.md         # this document
└── README.md
```

---

## 4. Configuration surface (`CONFIG.md`)

| Section | Controls |
|---------|----------|
| Candidate Profile | Optional path to an existing profile for sharper fit scoring |
| Tracked Companies | The explicit watchlist, optional careers URL + notes per company |
| Topics | Used to *discover* companies not on the watchlist — specificity matters |
| Target Roles | Priority-ordered titles; reasonable synonyms allowed |
| Match Filter | Locations, work model, salary floor, employment type, language, must-haves, deal-breakers |
| Discovery Settings | `max_suggested_companies`, `max_topics_per_run`, exclusion list |
| Source Settings | Per-board on/off toggles |
| Output Settings | Report dir, filename pattern, timezone, `state_retention_days` |

The skill **never edits `CONFIG.md`**. If the config is malformed (e.g. no topics), it says so and continues with what is there.

---

## 5. Run flow

```
0. Load CONFIG.md  (+ profile if configured)   → abort with instructions if missing
1. Load state/seen-jobs.json                   → missing = first run, say so in header
2. Scan tracked companies      (parallel)      → careers page, Greenhouse/Lever/Ashby,
                                                  LinkedIn, enabled regional boards
3. Discover suggested companies per topic      → then scan each the same way;
                                                  drop those with no matching opening
4. Apply match filter                          → target-role map, location/model,
                                                  salary floor, deal-breakers
5. Render HTML from templates/report.html      → reports/YYYY-MM-DD-job-tracker.html
                                                  + reports/latest.html
6. Update state                                → first_seen / last_seen / retention prune
7. Print short chat summary                    → counts + new postings only
```

### Job identity

`<stable-job-id>` = lowercase slug of `company|title|location`, canonical apply URL as tiebreaker. Must be computed identically every run or the diff breaks.

### State lifecycle

- New job → `first_seen` = today, badge 🆕.
- Still present → `last_seen` updated, no badge.
- Disappeared → **retained**, not deleted, so a reappearing posting is not re-announced as new. Pruned after `state_retention_days` (default 90).
- A posting is only "closed" when a source confirms it; otherwise `not seen this run`.

---

## 6. Report structure

- **Header** — run timestamp, scan scope, first-run notice; chips for `new / matching / suggested / filtered out`.
- **📌 Tracked Companies** — one card per company, ordered: new postings → has matches → none. Table: Title / Location / Model / Salary / Posted / Fit / Link. Companies with nothing still show a one-line "no matching openings — N sources checked" instead of being hidden.
- **💡 Suggested Companies** — same table plus a `Why suggested:` line naming the matched topic with a source link, and a 🆕 badge on first-time suggestions.
- **🔄 Changes since last run** — new postings, no-longer-visible postings, new suggestions. Omitted entirely on a first run.
- **🔗 Coverage & sources** — every source queried and whether it returned results.

Fit is `✅ / ⚠️ / ❌`. `⚠️` is used whenever data is missing — never `✅` on an assumption.

---

## 7. Cost model

Tavily MCP at basic search depth: roughly **10–20 credits per company per run**.
A 7-company watchlist + 6 suggested companies ≈ **150–250 credits/run**.
Free tier is 1,000 credits/month → every-other-day runs are tight; `max_suggested_companies` is the throttle. Built-in `WebSearch`/`WebFetch` work as a free fallback with lower precision.

---

## 8. Open questions for review

1. **Report retention** — keep every dated report forever, or prune after N days like the state file?
2. **Suggested → tracked promotion** — should the skill offer to append a repeatedly-suggested company to the watchlist, or stay strictly read-only on `CONFIG.md`? (Current: strictly read-only.)
3. **Fit scoring depth** — currently a per-criterion ✅/⚠️/❌. Worth adding a single 0–100 score to sort the tables by?
4. **`job-evaluator` handoff** — should the report add a "deep-dive this company" link/action per row, so a hit flows straight into `job-evaluator`?
5. **Topic drift** — should discovered-but-rejected companies be remembered so they are not re-proposed every run? (Adds a `rejected` list to state.)
6. **Multi-region** — the match filter assumes one location set. Do you need per-role location rules (e.g. remote-only for IC roles, hybrid acceptable for EM)?
7. **Location of this plan folder** — `skills/job-tracker/plans/` vs. a top-level `skills/plans/`. Say the word and I'll move it.

---

## 9. Out of scope for v1

- Email / Slack / push delivery of the report
- Scheduled or background execution (cron, `/loop`)
- Application tracking (applied / rejected / interviewing status)
- Recruiter-message parsing
- Salary negotiation or interview prep — that is `job-evaluator`'s job
