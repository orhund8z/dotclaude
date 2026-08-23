# Job Tracker Configuration — Example

> Copy this file to `CONFIG.md` and edit it.
> `CONFIG.md` is gitignored — your watchlist and preferences stay local.

---

## Candidate Profile

Optional. Point at an existing profile file to sharpen the fit assessment.
Leave as `none` to rely only on the filters in this file.

- **Profile file:** `~/.claude/skills/job-evaluator/PROFILE.md`

---

## Tracked Companies

The explicit watchlist. Every run scans each of these for matching openings.

| Company | Careers URL (optional) | Notes |
|---------|------------------------|-------|
| Zalando | https://jobs.zalando.com | platform / SRE org |
| N26 | https://n26.com/en/careers | |
| Celonis | | process mining |
| Personio | | |

---

## Topics

Used to **discover** companies that are not on the watchlist.
Be specific — "distributed systems" is too broad, "event-driven payment infrastructure" is useful.

1. Event-driven / streaming platforms (Kafka, Flink)
2. Developer platform & internal tooling (platform engineering)
3. Cloud reliability / SRE at scale
4. FinTech payment infrastructure

---

## Target Roles

In priority order. Reasonable synonyms are allowed.

1. Principal Engineer
2. Staff Engineer
3. Senior Site Reliability Engineer
4. Engineering Manager (Platform / Infrastructure)

---

## Match Filter

- **Locations:** Germany (Berlin, Munich, Hamburg) — or fully remote within EU
- **Work model:** Remote or Hybrid. On-site only → exclude.
- **Minimum base salary:** €120,000 / year (postings below this are kept but marked ❌)
- **Employment type:** Full-time only
- **Working language:** English

### Must have

- Backend / infrastructure focus (JVM, Kotlin/Java, Python, Go)
- Cloud: AWS preferred; GCP/Azure acceptable

### Deal-breakers (exclude the posting)

- On-site only, no remote option
- Contract / freelance / internship
- Industries: gambling, adtech

---

## Discovery Settings

- **Max suggested companies per run:** 6
- **Max topics explored per run:** 4
- **Exclude from suggestions:** (companies you never want proposed)
  - [Current employer]
  - [Company you already rejected]

---

## Source Settings

Enable or disable individual job sources.

| Source | Enabled |
|--------|---------|
| Company careers page | yes |
| Greenhouse / Lever / Ashby | yes |
| LinkedIn Jobs | yes |
| Xing | yes |
| Indeed.de | yes |
| Hiring.cafe | yes |
| Builtin.com | yes |
| Wellfound.com | yes |
| Remotely.de | yes |

---

## Output Settings

- **Report directory:** `reports/`
- **Filename pattern:** `YYYY-MM-DD-job-tracker.html`
- **Also write `latest.html`:** yes
- **Timezone:** Europe/Berlin
- **State retention (days):** 90
