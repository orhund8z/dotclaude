# Squad — design rationale

This document explains **why** Squad works the way it does. It is not a spec: the behaviour is
defined by [`skills/squad/SKILL.md`](../skills/squad/SKILL.md), its
[`references/`](../skills/squad/references/), and the persona files in [`agents/`](../agents/).
Change those; update this file only when a decision below changes.

The original idea, as first written, is kept in [`original-prompt.txt`](./original-prompt.txt).

## Goals

1. **Build the right thing** — validate direction with working software before investing in it.
2. **Progress with caution** — the user sees the outcome at each milestone and approves it.
3. **Finish fast and cheaply** — no wasted tokens, no rework from late feedback.
4. **Safe by default** — reviewed, tested, least-privilege, rollback points, no irreversible
   actions without approval.

## Decisions

### D1 — Incremental delivery with a proof of concept first (2.0.0)

**Problem.** Version 1.x ran Analyze → Plan → Dev → Review as one big batch after a single plan
approval. The first working software appeared at the very end, so a wrong direction was discovered
after it had been fully built, tested, and reviewed — the most expensive point to learn it.

**Decision.** Shape → **PoC** → **Increments** → Harden. The PoC is a *walking skeleton*: the
thinnest slice through every layer, runnable with one command. Increments are independently
demoable, ordered risk-first, and each ends at a gate.

**Why.** Standard practice in iterative delivery (walking skeleton, vertical slices, short feedback
loops): the cost of a change grows with how much is built on top of the wrong assumption.

### D2 — Gates at milestones, no questions between them (2.0.0, refines 1.1.0)

**Decision.** The user is asked only at kickoff (one batch) and at gates (Brief, PoC, each
increment). Between gates the orchestrator decides, logs the decision, and reports it at the next
gate. "Approve the rest" turns on autopilot.

**Why.** 1.1.0 removed mid-run questions but left one gate, which meant no visibility during the
build. Gates at milestones give control at the moments that matter without the interruption cost
of ad-hoc questions.

### D3 — Hybrid testing (2.0.0)

**Decision.** PoC: one smoke/acceptance check. Increments: tests written with the increment, TDD
for core domain logic. Harden: edge-case matrix, end-to-end, coverage bar, security.

**Alternatives.**
- *All tests at the end* — defects accumulate across increments and are expensive to localise; the
  final QA pass becomes a big-bang.
- *Full QA after every phase* — repeats cross-cutting work (edge-case matrices, coverage, security)
  on an incomplete system.

**Why.** Tests are cheapest while the code is fresh, but writing them before the direction is
validated wastes them. The PoC gate is the point where direction is validated, so TDD starts
right after it.

### D4 — Sonnet by default, model profiles tied to effort (2.0.0)

**Evidence.** A measured medium-effort run of 1.1.0 (small Python CLI, ~6.5 minutes, $3.50 total):

| Turn | Time | Cost | By model |
|---|---|---|---|
| Kickoff | 17 s | $0.40 | Opus $0.40 |
| Analyze + Plan (PM, Architect on Opus) | 197 s | $1.22 | Opus $1.22 |
| Dev + Review + fix round | 180 s | $1.88 | Opus $1.57 (orchestrator), Sonnet $0.31 |

Opus was ~91% of the cost; the actual building and reviewing on Sonnet cost $0.31. The orchestrator
alone read ~1M cached input tokens in the build turn.

**Decision.** Three profiles — Fast, Balanced (default), Deep — selected by effort and overridable.
Opus only in Deep, for PM, Architect, and CEO. The orchestrator recommends the session model
(`/model sonnet` or `/model opus`) at kickoff, since it can't switch its own.

**Measured on 2.0.0** (same task, medium effort, Balanced profile, sonnet session): kickoff →
Brief gate → PoC gate → inc-1 gate → "approve the rest" → inc-2 → Harden → final report.

| | 1.1.0 | 2.0.0 |
|---|---|---|
| Total cost | $3.50 (91% Opus) | $4.23, all Sonnet ($3.61 excluding one turn lost to a since-fixed background-agent issue) |
| User checkpoints | 2 (kickoff, plan) | 5 (kickoff, brief, PoC, inc-1, autopilot) |
| First working software | at the end | after the PoC (~3rd turn) |
| Tests at the end | 12 | 58, coverage 93/94 lines |
| Rollback points | none | one commit per milestone |

So the total spend is about the same, but it buys far more: earlier feedback, more gates, more
tests, rollback points. Each extra gate re-reads the orchestrator's conversation, which is why the
saving from Sonnet does not show up as a lower total; "approve the rest" is the lever for runs
where the user trusts the direction.

**Plus context discipline:** the orchestrator reads ≤ 200-word handoffs, not artifacts; personas
get paths, not pasted content; the Reviewer reviews only the increment's diff; the orchestrator no
longer re-runs checks the Reviewer already ran.

### D5 — Fewer cold starts at medium (2.0.0)

**Decision.** At medium effort a single Architect call writes scope, design, and roadmap. PM and
CEO run only at high effort (CEO also on request).

**Why.** Each subagent starts cold and re-reads the same context; two calls for a medium-sized job
doubled that cost without a matching gain. The CEO's value/ROI framing overlapped with the PM's.

### D6 — One local commit per milestone (2.0.0)

**Decision.** On a clean git tree, work on a local `squad/<slug>` branch and commit once per
approved milestone. Never push.

**Why.** Every gate gets a rollback point, and the Reviewer gets a precise diff to review.

### D7 — Least privilege, honestly stated (2.0.0)

Reviewer and SecOps now have `Write` for their reports (1.x told them to write reports but gave
them no `Write`, so they used `Bash`). Any persona with `Bash` can technically modify files, so
"reviewers never edit source" is enforced by instructions; the docs say so explicitly instead of
implying a tool-level guarantee.

### D8 — The skill is tested like code (2.0.0)

- Behavioural evals in [`evals/`](../evals/) for `claude plugin eval`: one kickoff batch, no code
  before the Brief gate, explicit model/effort on every persona call, a roadmap that starts with a
  PoC.
- CI validates the plugin and marketplace manifests, agent frontmatter, and doc links.
- Semantic versioning in `plugin.json`, history in [`CHANGELOG.md`](../CHANGELOG.md).
- A single source of truth: the old 375-line `prompts/squad.md` spec, which had to be kept in sync
  by hand, is replaced by this rationale document.

## Review scorecard (2.0.0 review)

| Area | 1.1.0 | 2.0.0 target |
|---|---|---|
| Incremental delivery (PoC, milestones) | 3 | 9 |
| Feedback loop & gates | 5 | 9 |
| Testing / QA strategy | 5 | 8.5 |
| Cost & speed | 4 | 8 |
| Role design & least privilege | 6 | 8.5 |
| Model configuration | 7 | 9 |
| State, traceability, rollback | 7 | 8.5 |
| Skill engineering (evals, CI, versioning) | 2 | 8 |
| Docs & diagrams | 7 | 8.5 |
| **Overall (weighted)** | **5.4** | **≈ 8.7** |
