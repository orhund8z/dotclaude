# Squad artifacts — layout and templates

All lifecycle artifacts live under `docs/squad/` in the project being built. Durable project docs
(`README.md`, `SPEC.md`) live at the project root.

```
docs/squad/
├── STATE.md               # the resume point: effort, roster, roadmap status, stop log, decisions
├── direction.md           # full team only: CEO go/no-go
├── brief-v1.md            # scope + design + roadmap — the plan of record (shown at the `brief` stop, if chosen)
├── brief-v2.md            # only when scope/roadmap changes; never overwrite an approved version
├── threat-model.md        # Shape, security/data-sensitive designs only (SecOps)
├── inc-00.md              # PoC: what was built, how to run it, smoke check result
├── inc-01.md              # increment 1: Developer notes + demo command
├── inc-01-review.md       # increment 1: Reviewer verdict + findings
├── …
├── harden-review.md       # Harden: QA edge-case matrix, coverage, findings
├── harden-security.md     # Harden: security findings (when SecOps ran)
├── final-report.md        # written once when the run is done: results + cost (never overwritten)
└── adr/                   # architecture decision records (high effort, or a genuine fork)
```

Fix-up rounds **append** a `## Round 2` section to the same `inc-NN.md` / `inc-NN-review.md`.

## STATE.md

Keep it short — it is read on every resume. Personas maintain it (the orchestrator doesn't edit
it): the persona that finishes a milestone sets that row's status (`built`, `reviewed`), and the
next persona records the stop-point answer it starts from (`continue`, with the user's words). The
last persona in Harden sets `Phase: done`; a park sets `Phase: parked at <stop point>`. Each
persona also sets `Phase:` to the stage it is working in, and adds leftover findings to **Open
items** (removing them when fixed) — a resumed run has no handoff to read them from.

```markdown
# Squad STATE
- Request: <one line>
- Started: <UTC timestamp from the kickoff call>
- Effort: medium · Team: lean · Profile: Balanced · Stops: brief, build-complete (or none)
- Branch: squad/<slug> (or "none (dirty tree)") — commit history lives in `git log`, not here
- Phase: increment-2 (in review)

## Roster
| Persona | Model | Reasoning |
|---|---|---|

## Roadmap
| Inc | Title | Status |
|---|---|---|
| 0 | PoC — <title> | approved |
| 1 | <title> | approved |
| 2 | <title> | in review |

## Open items
- <leftover finding or follow-up> (inc-N, severity) — removed when fixed

## Kickoff answers & assumptions
- …

## Stop log
- brief — continue (user: "…")
- build-complete — parked; resumed (user: "…") → harden

## Decisions taken
- <decision> — <one-line why> (inc-N)

## Usage
| Stage | Persona | Model | Subagent tokens | Tool uses | Duration (ms) | Finished (UTC) |
|---|---|---|---|---|---|---|
```

`## Usage` must stay the last section: milestone commits append rows to it.

## brief-vN.md

Short, self-contained, bullets and tables. Sections in this order:

1. **Goal** — what and for whom, 2–3 lines.
2. **Scope** — in / out (explicit non-goals).
3. **Requirements** — functional; non-functional with numbers where they exist.
4. **Acceptance criteria** — testable (Given/When/Then or checklists), each with an ID (`AC-1`…).
5. **Architecture & stack** — components, data model, key flows; each stack choice with why and
   the options considered.
6. **Roadmap**

   | Inc | Title | Delivers (user-visible) | ACs | Tests added | Demo command | Persona · model / reasoning |
   |---|---|---|---|---|---|---|
   | 0 | PoC | end-to-end happy path | AC-1 (happy path) | smoke check | `…` | Developer · sonnet / medium |
   | 1 | … | … | AC-2, AC-3 | unit: …; integration: … | `…` | Developer · … |

   Plus one row per review pass and the Harden step (Reviewer, SecOps) as the effort calls for.
7. **Test strategy** — what each stage tests (PoC smoke → per-increment → Harden), coverage bar.
8. **Assumptions & decisions taken** — every open point from Shape with the option chosen.
9. **Risks** — and, at high effort, the non-functional plan (observability, failure modes, single
   points of failure, cost profile at ~10x) and rollout/rollback.

## inc-NN.md (Developer)

```markdown
# inc-NN — <title>
- Delivers: <user-visible change>
- How to see it: `<exact command>` → <expected output>
- ACs covered: AC-…  (each → test name)
- Tests: <added / total, all green>; coverage on touched core logic: <n%> (medium+)
- Decisions: …
- Known limitations: …
```

## Stop message (orchestrator → user)

```markdown
**<Milestone> ready — <one-line outcome>**
See it: `<command>` → <expected output>
Since last stop: <what changed>
Tests: <n passing> · Review: <no blockers | n minors deferred>
Decisions taken: <bullets>
Risks / open: <bullets>
Next: <next increment title and what it delivers>
Options: continue · redirect (tell me what to change) · change stop points · harden now · park
```

## Final report (docs/squad/final-report.md)

```markdown
# <Project> — final report
- Effort: <e> · Team: <t> · Profile: <p> · Stops: <none | list>
- Branch: <squad/slug> · Commits: <n> (see `git log`)
- Status: done · Tests: <n passing, coverage x%> · Review: <no open blocker/major>

## What was built
<2–4 sentences> · How to run it: `<command>` → <expected output>

## Increments
| Inc | Title | Commit | Result |
|---|---|---|---|

## Decisions taken
- <decision> — <one-line why>

## Open items and follow-ups
- <item> (severity) — not performed; listed for you

<!-- Duration and Cost below are NOT hand-written: scripts/usage_report.py generates them from
     STATE.md and they are appended to the report. Example output: -->

## Duration

**Total elapsed, all work (kickoff → done): 1h 15m 05s**

Started `2026-10-19T10:00:00Z`, finished `2026-10-19T11:15:05Z`.

| Stage | Subagent work | Elapsed since previous | Finished (UTC) |
|---|---|---|---|
| inc-0 | 3m 00s | 5m 00s | 2026-10-19T10:05:00Z |
| harden | 1m 00s | 1h 10m 05s | 2026-10-19T11:15:05Z |
| **Total — all work** | **4m 00s** | **1h 15m 05s** | **2026-10-19T11:15:05Z** |

- *Elapsed* includes the orchestrator's own time and any time spent waiting at a stop point or parked. *Subagent work* is the sum of the personas' own durations; parallel calls overlap, so the sum can exceed the elapsed time of a stage.

## Cost

Tokens from the run's own `<usage>` figures (subagents only):

| Stage | Persona | Model | Subagent tokens | Tool uses |
|---|---|---|---|---|
| inc-0 | architect | sonnet | 10,000 | 5 |
| inc-0 | developer | sonnet | 20,000 | 8 |
| harden | reviewer | sonnet | 5,000 | 3 |
| harden | secops | opus | 5,000 | 2 |
| **Total** | | | **40,000** | **18** |

- opus: 5,000 tokens — est. $0.03
- sonnet: 35,000 tokens — est. $0.10
- **Estimated subagent total: $0.13** — rough (±50%): the harness gives one token total per subagent, not an input/output split. Blend 0.9 × input + 0.1 × output price; prices from `references/pricing.md` (2026-10-06).
- **Orchestrator (this session): not measured by the run.** For the exact total, run `/cost` in the Claude Code session and add the figure here.
```
