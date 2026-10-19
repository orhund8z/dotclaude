# Squad — release notes

Every change to the `squad` plugin, **what** changed and **why**, newest first. Read top to
bottom backwards to see how Squad evolved and what each step taught us. Versions follow
[Semantic Versioning](https://semver.org/); the longer reasoning behind the bigger decisions is in
[`docs/DESIGN.md`](./docs/DESIGN.md).

**How to add an entry:** every change to the plugin (skill, agents, references, evals, docs) adds a
bullet under the next version: `- **What changed** — why (evidence or the problem it solves).`
Keep it to one or two lines; link a DESIGN.md decision for anything larger.

## Evolution at a glance

| Version | Theme | Lifecycle | User checkpoints | Default models | Measured run* |
|---|---|---|---|---|---|
| 1.0.0 | Six-persona SDLC | Analyze → Plan → Dev → Review → Monitor | Many ad-hoc questions | PM/Architect opus, rest sonnet | — |
| 1.1.0 | Ask once, then run | same | 2 (kickoff, plan) | CEO + PM + Architect opus | $3.50, 91% Opus, 12 tests |
| 2.0.0 | Incremental delivery | Shape → PoC → Increments → Harden | kickoff + Brief + PoC + each increment | sonnet; opus only in Deep profile | $4.23 all Sonnet, 58 tests, 6 commits |
| 2.3.0 | Team is its own knob | same | same | every profile covers all six personas | medium + full team + Balanced: Shape $0.49 |
| 2.2.0 | Run through, stop where chosen | same | kickoff + only the stop points you pick (default none); park & resume | same | $2.24 all Sonnet, 28 tests, 97% coverage — incl. park + resume in a new session |
| 2.1.0 | Lean orchestrator | same | same | same | $2.97 all Sonnet, 46 tests, 3 commits; orchestrator calls −43% |

\* Same task each time: a small Celsius ↔ Fahrenheit CLI, medium effort, headless run.

## 2.4.1

- **Total elapsed time in the final report's Duration table** — the 2.4.0 template had only a
  blank "Wall-clock" bullet, and nothing recorded the start time, so a real run left it out. The
  report now has a Duration table whose last row is **Total — all work** (Started → last finish),
  beside per-stage elapsed and the personas' summed work time.
- **Times come from real timestamps** — one `date -u` call right after the kickoff answers (it also
  does the dirty-tree check) sets `Started:` in `STATE.md`; each milestone (and park) commit call
  adds a `Finished (UTC)` column value in the same call, so no extra calls beyond that one.
- **Duration and Cost are generated, not written** — in the first test run the model compressed the
  report (low effort, Fast profile) and left the table out; asking harder in the prompt is
  unreliable. `scripts/usage_report.py` now computes both sections from `STATE.md` and the final
  report appends its output, so the **Total — all work** row is always there and the arithmetic
  (elapsed, sums, per-model $) isn't done by the model. It has unit tests, run in CI.
- **Three durations, labelled** — elapsed includes orchestrator time and waits at stop points;
  subagent work is the sum of the personas' own durations (parallel calls overlap).
- Park call now also appends the usage rows (the cost section already said it did).

Tested: low-effort run — `STATE.md` got `Started:` and a `Finished (UTC)` per row, and the final
report carried the generated Duration table (**Total elapsed, all work: 0m 23s**, subagent work
0m 12s) and Cost section. `test_usage_report.py`: 7 tests pass. A first run without the script
had dropped the table.

## 2.4.0

- **Final report with the AI cost** — the run now ends by writing `docs/squad/final-report.md`
  (once, never overwritten): what was built and how to run it, results, decisions, open items, and a
  Cost section with tokens, models, duration and an estimated $ total.
- **What the run can and can't measure** — each subagent's result carries its tokens, tool uses and
  duration, so those are exact per persona. The harness gives one token total per subagent, not an
  input/output split, so the $ is an estimate with a stated blend (`references/pricing.md`). The
  orchestrator's own spend is not visible to the run; the report says so and points to `/cost`.
- **No extra calls** — usage rows are appended to `STATE.md`'s `## Usage` table in the commit call
  that already happens at each milestone, so they survive a park and resume.
- Pricing: claude-api pricing table dated 2026-10-06; the report names the date it used.

Tested: low-effort run — `final-report.md` written with the Cost section and a `## Usage` row;
the run's own harness total was $0.29 over 38 s, of which the one Developer call was 9,006 subagent
tokens (about $0.03 by the estimate). Most of the cost was the orchestrator, which the report flags.

## 2.3.0

- **Team is a third knob, independent of effort and profile** — which personas ran was tied to
  effort (CEO and PM only at `high`), so "the whole SDLC company on Balanced models" wasn't
  possible. Now `lean` (Architect plans alone; SecOps only if sensitive) or `full` (CEO → PM →
  Architect; SecOps always in Harden) can be combined with any effort and any profile. Effort still
  preselects: low/medium → lean, high → full. Kickoff asks it inside the effort question, so the
  batch stays at four questions.
- **Every profile now covers every persona** — Fast and Balanced had "—" for the CEO and PM (and
  Fast for the Architect, Reviewer, SecOps), so a full team on those profiles had no defined
  models. Fast: all Sonnet with low/medium reasoning; Balanced: all Sonnet, CEO medium, PM and
  Architect high.
- **Persona depth follows effort, not team** — a full team at medium effort writes lean acceptance
  criteria and one recommended design option; ADRs, option matrices and the non-functional plan
  stay at high.
- **README explains why reasoning differs per persona** — reasoning follows how expensive a
  persona's mistake is: PM and Architect (everything builds on their output) one notch up, the CEO
  (short go/no-go, correctable downstream) one notch down, the checked-downstream roles at base.
- **README explains the model/reasoning split** — the profiles are often read as "Fast = haiku,
  Balanced = sonnet, Deep = opus"; the README now shows the full persona × profile table and that
  Deep puts Opus only on planning personas.

- **Eval 02 checks models deterministically** — its LLM judge read the whole trace and failed on
  a correct run (it only saw the start of a long trace). Three `tool_used` regex graders now check
  the Architect call is `sonnet`/`high` and that no CEO or PM ran on the default lean team.

Tested: medium effort + full team + Balanced, stop at `brief` — CEO (sonnet/medium), PM
(sonnet/high), Architect (sonnet/high) ran in order and the run stopped at the brief; $0.49.

## 2.2.1

- **README "How to use — every option"** — the options (effort, model profile, per-persona
  overrides, stop points, clarifications, session model), the answers at a stop, park/resume, and
  the behaviours that change without asking were spread across the README and only discoverable by
  reading the skill. One section now lists every choice with its values, default, and when it's
  decided, plus copy-paste recipes. Clarifies that there is no config file.

## 2.2.0

- **Runs straight through by default** — 2.0.0/2.1.0 stopped at every milestone (Brief, PoC, each
  increment), which suits close supervision but not "just build it and show me the code". The
  user now chooses at kickoff; the default is no stops, run to the final report.
- **Stop points chosen at kickoff** (`brief`, `poc`, `each-increment`, `build-complete`, any
  combination) — the user wanted to decide up front where to look, instead of the skill deciding
  for them. Kickoff asks it as the fourth question of the same batch, so it costs no extra turn.
- **`build-complete` stop** (after the last increment, before Harden) — "write the code, let me see
  it, then decide on hardening" had no place in the flow: "approve the rest" ran Harden too.
- **Park and resume** — at any stop the user can park; `STATE.md` records `Phase: parked at <stop>`
  and a `squad: parked at …` commit marks the spot. "Resume the squad" (same session or days later)
  reads `STATE.md` and returns to the same stop without re-asking the kickoff questions. Before,
  `STATE.md` held enough to resume but nothing told the skill how, or let the user choose to pause.
- **Stop-point answers replace gate options** — *continue · redirect · change stop points · harden
  now · park*; "approve the rest" became "change stop points → none".
- **Personas keep `Phase:` and *Open items* in `STATE.md`** — found in the 2.2.0 test run: `Phase:`
  was never updated after Shape, so parking took two calls to find the line; and the open items
  shown at the `build-complete` stop were lost on resume ("no open items logged"). Personas now set
  `Phase:` and maintain an *Open items* section; the park command is a single fixed `sed` + commit.
- **One check call allowed on resume** — a resumed session has no handoff in context, so one
  call to run the demo command and tests is within budget.
- **Docs** — README, lifecycle diagram (optional ⏸ stops and a Parked node), hero/persona images,
  STATE template (`Stops:`), evals (case 01 checks the stop-point question; case 02 now chooses the
  `brief` stop explicitly, since the default no longer stops there).

**Tested** (same task, medium/Balanced, sonnet session, stop point `build-complete` only): kickoff →
Shape → PoC → inc-1 → inc-2 ran without stopping and paused before Harden ($0.75, 3 milestone
commits) → **park** → **"resume the squad" in a new session** re-presented the same stop without
the kickoff questions → continue → Harden → final report, `Phase: done`. Total $2.24, 28 tests,
97% coverage. Evals: 01 — 1.0 on 3 runs (its clarification check now accepts stated assumptions,
which is how the skill is told to handle them); 02 — 1.0.

## 2.1.0

**Measured** (same task and answers as the 2.0.0 run, sonnet session, medium/Balanced):

| | 2.0.0 | 2.1.0 | Change |
|---|---|---|---|
| Orchestrator API calls | 30 | 17 | −43% |
| Tokens re-read by the orchestrator | 2.52M | 1.18M | −53% |
| Total cost | $3.62 | $2.97 | −18% |

The Architect planned one increment instead of two this time, so part of the cost drop is less
work; the per-call figures are the like-for-like comparison.

- **Orchestrator call budget** — a measured 2.0.0 run showed ~87% of all tokens read were the
  orchestrator re-reading its own conversation: 31 calls × ~80K tokens. Persona calls start from a
  small fresh context and are cheap. The skill now caps the orchestrator's own calls per step
  (one call per persona + one commit call per milestone).
- **Personas maintain `STATE.md`** — the orchestrator used to edit it with separate `sed` calls,
  each re-reading ~80K tokens for a one-line change. The orchestrator now names the update in the
  persona's prompt; the persona applies it as part of its own (cheap) work. The Architect (or the
  CEO at high) creates the file from the kickoff answers.
- **Branch + commit in one call** — creating the branch, staging, committing, and reading the SHA
  was spread over several calls; it is now a single command per milestone.
- **No re-running a persona's checks** — the orchestrator re-ran the PoC smoke check the
  Developer had just run. The Developer now pastes the real smoke-check output into its handoff.
- **No artifact reads for gate messages** — gates are built from the ≤ 200-word handoff, not by
  `cat`/`grep` of the brief or increment files.
- **Shorter skill text** — duplicated tables and lists folded into one-liners so the extra budget
  rules don't grow the text that is re-read on every call (2,481 words vs 2,385 before the budget
  was added).
- **`STATE.md` no longer tracks commit SHAs** — in the 2.1.0 test run the SHA column stayed empty
  because only the orchestrator learns the SHA, after the personas finish. `git log` is the source
  of truth; the persona finishing a milestone marks its row, and the last Harden persona sets
  `Phase: done`.
- **README diagrams styled** — the Mermaid diagrams were plain and the lifecycle was too wide to
  read at README width. They now share a theme with the hero/persona images, the lifecycle runs
  top-down, and labels keep their full wording. Mermaid stays (instead of PNGs) because it is
  editable in a few lines and diffable.
- **Release notes record what *and* why** — this file now explains the reason for every change so
  the project's evolution can be summarised later.

## 2.0.0

**Problem:** 1.1.0 delivered big-bang — one plan approval, then the whole build — so a wrong
direction was found only after it was fully built, tested and reviewed. Opus was 91% of the cost.

### Changed (breaking)
- **Incremental lifecycle: Shape → PoC → Increments → Harden** — show working software early and
  let feedback reshape the plan while change is still cheap (DESIGN D1).
- **Gates at every milestone** (Brief, PoC, each increment) with *approve / redirect / approve the
  rest / stop and harden* — control at the moments that matter; "approve the rest" turns on
  autopilot when the direction is trusted (D2).
- **Sonnet by default; Fast / Balanced / Deep profiles tied to effort** — the building and
  reviewing on Sonnet cost $0.31 of $3.50 in 1.1.0; Opus is kept for Deep, where scope and
  architecture mistakes cost most (D4).
- **One Architect call for Shape at medium; PM and CEO only at high** — every cold-start persona
  re-reads the same context; two calls for a medium job doubled that cost (D5).
- **New artifact set** (`brief-vN`, `inc-NN`, `inc-NN-review`, `harden-*`) — one file per
  milestone matches the incremental flow; the old analyze/plan/dev/review/security versions did not.

### Added
- **Hybrid testing** (PoC smoke check → tests with each increment, TDD for core logic → Harden
  QA) — never write tests for an app whose direction isn't validated; never let defects pile up
  across increments (D3).
- **Diff-scoped increment reviews** — reviewing the whole repo every round repeated work.
- **One local commit per milestone** on `squad/<slug>` — a rollback point at every gate and a
  precise diff for the Reviewer (D6).
- **Personas run in the foreground** — in the 2.0.0 test run a background persona's completion
  notice lost a gate from the conversation and wasted a $0.62 turn.
- **≤ 200-word handoffs; session-model recommendation at kickoff** — the orchestrator was the
  biggest cost driver and can't switch its own model.
- **`references/` (templates, Definition of Done)** — keeps `SKILL.md` focused on control flow.
- **Evals, CI, version, design doc** — the skill had no regression tests and a hand-synced
  375-line spec that drifted (D8).
- **Mermaid diagrams + regenerable images** — the PNG diagrams were out of date and had no
  sources.

### Fixed
- **Reviewer and SecOps had no `Write` tool** although they were told to write reports, so they
  wrote through Bash — which also meant the "never edits source" rule wasn't even nominally
  enforced (D7).
- **State-only commits** and **a soft closing question in the final report** — both seen in the
  2.0.0 test run; one commit per milestone and a report that ends with statements only.

### Removed
- **`prompts/squad.md`** — the hand-synced spec drifted from the skill; replaced by
  `docs/DESIGN.md` (rationale only). The original prompt is kept as `docs/original-prompt.txt`.
- **Monitor phase** — replaced by the final report and roadmap revisions.

## 1.1.0

- **Ask once up front, approve the plan, then run to completion** — 1.0.0 asked the user
  questions throughout the run; the user wanted one question batch and one approval.
- **Final report ends without a question** — the first test run closed with "Should I commit
  this?", a question after approval.
- **CEO on opus** — requested to strengthen the direction call (reverted to the profile model in
  2.0.0 once cost data showed where Opus mattered).

## 1.0.0

- **Initial plugin** — six personas (CEO, PM, Architect, Developer, Reviewer + QA, SecOps), low /
  medium / high effort, per-persona model roster, Analyze → Plan → Dev → Monitor lifecycle,
  versioned artifacts under `docs/squad/`.
