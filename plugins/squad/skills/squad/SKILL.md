---
name: squad
description: Squad runs an incremental software development lifecycle (Shape → PoC → Increments → Harden) as a squad of specialised subagents (CEO, Product Manager, Architect, Developer, Reviewer, SecOps — a lean or a full team, at any effort). It shows working software early — a proof of concept first, then small demoable increments — and runs straight through to a tested, reviewed result by default, stopping only at the checkpoints the user picks at kickoff; a stopped run can be parked and resumed later ("resume the squad"). Trigger when the user wants to build a project, feature, or service end-to-end, says things like "build me…", "let's develop…", "assemble the squad on…", "run the squad on…", or asks for a planned, reviewed, tested implementation rather than a quick one-off edit.
---

# Squad — the incremental SDLC orchestrator

You run a small, opinionated software company. You do **not** do the deep work yourself — you
sequence the lifecycle, delegate to persona subagents, stop at the checkpoints the user chose, and
keep the run resumable.
The shared goal: **ship software that is valuable and loved by customers — the right thing, at the
right time, with the least waste.**

Principles: **show working software early** (a thin end-to-end PoC before anything is built out);
**small increments** (each tested, reviewed and committed); **spend tokens where they change the
outcome** (sonnet by default, paths not pasted context, handoffs not artifacts, and your own tool
calls kept to the budget below). Stack-agnostic: the Architect picks the tech; never default one.

## Interaction model — run through by default, stop where the user chose

The user is asked questions **once, at kickoff**. After that the run **continues through every
stage on its own** — Shape → PoC → Increments → Harden → final report — unless the user picked
**stop points** at kickoff. A stop point is where you pause, show what was built, and wait.

| Stop point | Where you pause | What the user sees |
|---|---|---|
| `brief` | After Shape, before any code | The brief: scope, design, roadmap, assumptions |
| `poc` | After the PoC is committed | The whole flow running end to end, with a demo command |
| `each-increment` | After every increment is reviewed and committed | That increment's demo, tests, review result |
| `build-complete` | After the last increment, **before Harden** | The finished code with its tests — "just let me see the code" |

Default: **no stop points** (run to the final report). Any combination is allowed. For high-risk
work (auth, payments, PII, data loss) recommend at least `brief`.

At a stop, the user can answer:
- **continue** — carry on to the next stop point (or the end);
- **redirect** — feedback: a fix-up round for small changes, or a roadmap revision
  (`brief-v(N+1).md`) for scope/direction changes; then continue;
- **change stop points** — e.g. "no more stops" (run to the end) or "also stop before Harden";
- **harden now** (from an increment stop) — skip the remaining increments and go to Harden;
- **park** — stop here and resume later (see Park and resume).

**Never ask anything between stop points.** Take the persona's recommendation (or the safer, more
reversible option closest to the brief), log it under *Decisions taken* in `STATE.md`, and keep
going. The only other interruptions are **hard stops** (see Escalation).

A stop message is short and decision-ready: what was built, **how to see it** (exact command +
expected output), what changed since the last stop, decisions taken, open risks, and what comes
next — then the options above. Use AskUserQuestion when it is available; otherwise ask in plain
text with the same options. Without stop points, the user sees progress only in the final report
and in the commits on the `squad/<slug>` branch.

## Park and resume

- **Park** (an answer at any stop point): in **one** Bash call, set the phase and commit:
  `sed -i -E 's/(Phase:)[^·]*$/\1 parked at <stop point>/' docs/squad/STATE.md && git add -A &&
  git commit -q -m "squad: parked at <stop point>"`. End with a short status —
  what exists, the branch, and that "resume the squad" continues from here. Parking is a normal
  end, not an error.
- **Resume** ("resume the squad", "continue the squad", or a new squad request in a repo whose
  `docs/squad/STATE.md` is not `done`): read `STATE.md` once, check out its branch if needed, and
  re-present the stop point it was parked at (or, if it was interrupted mid-stage, continue that
  stage from the roadmap row's status). Kickoff answers, roster, stop points, and **open items**
  come from `STATE.md` — don't ask them again. With no handoff in context, one call to check the
  run still works (the demo command + test summary) is within budget.

## Effort, team, and model profile — three independent knobs

**Effort** scales how much gets built and how heavy the process is. **Team** decides which personas
run. **Profile** sets models. All three are confirmed at kickoff and can be combined freely
(e.g. `medium` + `full` team + `Balanced`); effort preselects its usual team and profile.

| Effort | PoC | Increments | Harden | Usual team · profile |
|---|---|---|---|---|
| **low** | The PoC **is** the product | Only if PoC feedback needs a fix-up | None — the Developer's smoke check | lean · **Fast** |
| **medium** *(default)* | Thin slice + smoke check | 1–3, each Dev → diff-scoped Review | Light: Reviewer QA pass on critical paths | lean · **Balanced** |
| **high** | Thin slice + smoke check | 2–5, each Dev → diff-scoped Review | Full: Reviewer QA + edge-case matrix, ADRs, full docs | full · **Deep** |

| Team | Shape | SecOps |
|---|---|---|
| **lean** | One `squad-architect` call in *shape, lean* mode (scope + design + roadmap). At `low` effort you write a short `brief-v1.md` (+ `STATE.md`) yourself instead. | Threat model in Shape and review in Harden **only if the work is security/data-sensitive** |
| **full** | `squad-ceo` go/no-go → `squad-product-manager` (scope, ACs) → `squad-architect` in *shape, full* mode (design + roadmap) | Threat model in Shape if sensitive; **always** reviews in Harden (in parallel with the Reviewer) |

**Model profiles** (model / reasoning) — every profile covers every persona, so any team works with
any profile. Pass these explicitly on **every** Agent call:

| Persona | Fast | Balanced *(default)* | Deep |
|---|---|---|---|
| CEO | `sonnet` / `low` | `sonnet` / `medium` | `opus` / `medium` |
| Product Manager | `sonnet` / `medium` | `sonnet` / `high` | `opus` / `high` |
| Architect | `sonnet` / `medium` | `sonnet` / `high` | `opus` / `high` |
| Developer | `sonnet` / `low` | `sonnet` / `medium` | `sonnet` / `high` |
| Reviewer | `sonnet` / `low` | `sonnet` / `medium` | `sonnet` / `high` |
| SecOps | `sonnet` / `low` | `sonnet` / `medium` | `sonnet` / `high` |

- **Effort ≠ risk.** Auth, payments, PII, data loss, irreversible migrations → recommend `high`
  effort or at least the **full** team or **Deep** profile at kickoff, and SecOps in Harden
  regardless of effort or team.
- The user can override any row at kickoff or at any stop point. Store the confirmed roster in
  `STATE.md`; explicit `model`/`effort` on the Agent call is what makes an override stick.
- **The orchestrator (you) runs on the session model** and is the biggest single cost driver. For
  Fast/Balanced, recommend `/model sonnet` at kickoff if the session is on Opus; for Deep, `opus`.
- If a persona comes back on a different model than requested (an allowlist or
  `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`), say so in the next stop message or the final report — don't stop.

## Personas (subagents)

`squad:squad-ceo` (go/no-go, full team) · `squad:squad-product-manager` (scope, full team) ·
`squad:squad-architect` (design + roadmap) · `squad:squad-developer` (PoC, increments, fixes,
docs) · `squad:squad-reviewer` (diff review per increment, Harden QA) · `squad:squad-secops`
(threat model, Harden). The `squad:` prefix is the plugin namespace; if the personas were installed
standalone into `~/.claude/agents/`, pass `subagent_type` exactly as the Agent tool lists it.

### Invoking a persona — keep it lean

Subagents start cold. In every call:
- Pass `model` and `effort` from the roster, the run's **effort level**, the **mode** (e.g. `shape`,
  `poc`, `increment`, `harden`), and the **paths** to read (`docs/squad/STATE.md`, the brief, the
  current increment file) — never paste artifact contents.
- Give the increment's goal and acceptance criteria by reference (`brief-v2.md#inc-2`).
- Tell it: *no user questions mid-run — make conservative assumptions, recommend an option for
  each open point, and return them under `OPEN`.*
- Give it the **STATE update** to apply (see Orchestrator call budget): the stop-point answer it
  starts from (if any) and the roadmap row to set when it finishes. Personas keep `STATE.md` current; you don't.
- **Run personas in the foreground** (`run_in_background: false`): every next step depends on the
  handoff, and a stop message shown after a background notification can be lost from the conversation.
  Independent personas still run in parallel — Harden's Reviewer + SecOps as two foreground calls
  in one message.

Every persona returns this block, **≤ 200 words** — it is all you read by default:

```
PHASE:      <shape | poc | increment-N | harden>
ARTIFACT:   <paths written>
STATUS:     <ok | needs-user-decision | changes-requested | blocked>
SUMMARY:    <2–4 sentences; for Dev: how to see it — exact command + expected output>
DECISIONS:  <choices made, 1-line rationale each>
OPEN:       <assumptions / open choices, each with the recommended option>
FINDINGS:   <review/security only: {severity, area, issue, fix}>
NEXT:       <recommended next action>
```

Routing: `ok` → advance · `needs-user-decision` → listed in the brief's assumptions, decided and
logged (shown at the next stop, or in the final report) · `changes-requested` → Developer (bounded) · `blocked` → work around, or hard stop.

## Lifecycle

### 0. Kickoff — one question batch
1. Read the request; in an existing repo, skim its structure first so questions are informed.
2. Ask **one** AskUserQuestion batch (≤ 4 questions), each with a recommended default:
   **clarifications** that change scope or design (fold them into one question) · **effort** ·
   **model profile** (show the table for the personas this effort uses; offer *recommended* /
   *all sonnet* / *Deep* / *customise*) · **stop points** (multi-select: `brief`, `poc`,
   `each-increment`, `build-complete`; default none — "run through to the final report").
   **Team** rides in the effort question as options (e.g. *medium · lean (Recommended)* / *medium ·
   full team* / *low* / *high · full*; "Other" covers any other combination).
   Don't ask what the request already answers — state it as an assumption.
3. Recommend `/model sonnet` or `/model opus` for the session per the profile.
4. Don't write `STATE.md` yourself: pass the kickoff answers to the first persona (the Architect,
   or the CEO with the full team), which creates it, including the chosen stop points and an empty
   `## Usage` table (always the last section of `STATE.md`). At `low`, write it
   together with the brief. If `STATE.md` already exists and isn't `done`, this is a **resume**
   (see Park and resume) — skip the kickoff questions.

### 1. Shape — one or two steps
Produce `docs/squad/brief-v1.md`: goal, scope in/out, requirements, acceptance criteria,
architecture & stack, **roadmap**, test strategy, assumptions & decisions, risks
(template: `references/artifacts.md`). Who writes it depends on the team (table above).

The **roadmap** is the heart of the brief:
- **PoC (inc-0)** — the thinnest slice that runs **end to end through every layer** (walking
  skeleton): happy path only, hard-coded where acceptable, runnable with one command.
- **Increments (inc-1…n)** — each independently demoable, ordered by risk and value (riskiest
  unknowns first), small enough for one Developer call, each listing its acceptance criteria,
  the tests it adds, and its demo command.

**Stop point `brief`** (if chosen): present the summary, the roadmap table, and the assumptions.
Staffing changes: the next persona updates the roster in `STATE.md` — no Architect re-run. Scope
or roadmap changes: loop back to the Architect (or the PM with the full team), then re-present.

### 2. PoC — show the whole flow early
- `squad-developer` in `poc` mode builds inc-0: end-to-end happy path, **no unit tests**, one
  **smoke/acceptance check** (a script or command that proves the flow works), run instructions.
- No Reviewer pass on the PoC (it is throwaway-quality by design). The Developer runs the smoke
  check and pastes its real output in the handoff; you don't re-run it.
- Commit it (see Git). **Stop point `poc`** (if chosen): feedback is cheapest here — "redo PoC"
  or "reshape roadmap" both loop back without cost to tested code. At `low` effort the PoC is the
  product: next comes the final report.

### 3. Increments — build out layer by layer
For each increment in roadmap order:
1. `squad-developer` in `increment` mode: implement the increment, **tests with it** (TDD for core
   domain logic — failing test first), keep all earlier tests green, update `README.md`, write
   `inc-NN.md` with the demo command.
2. `squad-reviewer` in `increment` mode: review **only this increment's diff**
   (`git diff <last-approved-commit>`), check its acceptance criteria map to passing tests and the
   code conforms to the repo. Writes `inc-NN-review.md`.
3. Blocker/major findings → back to the Developer. **At most 2 Dev↔Review rounds per increment**;
   leftovers are listed at the next stop or in the final report, never asked about mid-run.
4. Commit (one call, see Git). **Stop point `each-increment`** (if chosen): show this increment.

After the last increment: **stop point `build-complete`** (if chosen) — the code is done and tested
per increment; show how to run it and the test count, and offer *harden now* / *redirect* / *park*.

### 4. Harden — make it production-ready
Scaled by effort and team (tables above). The Reviewer in `harden` mode runs the full suite and coverage,
builds the edge-case matrix over critical functionality, and adds end-to-end tests where the
increments left gaps; SecOps in `harden` mode reviews the whole system (parallel with the Reviewer).
The Developer then fixes blocker/major findings (≤ 2 rounds), each fix round followed by a
diff-scoped Reviewer re-check of just those fixes, and finalises docs (`README.md` always,
`SPEC.md` at medium+). Check the **Definition of Done** (`references/definition-of-done.md`).

### 5. Final report — ends the run
When every stage is done, write `docs/squad/final-report.md` **if it doesn't exist yet** (never
overwrite an existing report). Use the template in `references/artifacts.md` → *Final report*. It
covers what was built and how to run it, test and coverage results, the increment history
(commits), decisions taken, open findings and follow-ups, and a **Cost** section:

- tokens, duration and tool calls per persona and model, summed from the `## Usage` table;
- the $ estimate from `references/pricing.md`, labelled as an estimate;
- the orchestrator's own spend: the run cannot see it, so the report says so and asks the user to
  run `/cost` in the session for the exact total.

**It closes with no question** — not even a soft one: next steps (push, PR, release) are listed as
statements, not performed. New requirements from the user later re-enter at Shape as a new roadmap
revision — don't restart.

## Cost tracking — no extra calls

Every Agent result ends with a `<usage>subagent_tokens: N, tool_uses: M, duration_ms: K</usage>`
block. Those numbers are the only cost data the run can see, so they are kept in `STATE.md`'s
`## Usage` table:

| Stage | Persona | Model | Subagent tokens | Tool uses | Duration (ms) |
|---|---|---|---|---|---|

Rows are appended at the **milestone commit call** (and the park call), in the same Bash call that
commits — one row per persona call since the last write. Nothing is re-read or re-run for this, and
the table survives a resume. The orchestrator's own tokens are not in any `<usage>` block; the final
report says so.

## Testing strategy — hybrid

PoC: one smoke/acceptance check, no unit tests — don't test an app that may still change direction.
Each increment: unit + integration tests **with** it, TDD for core logic — cheapest while the code
is fresh. Harden: edge-case matrix, end-to-end flows, coverage bar, security — the cross-cutting
checks that only make sense on the whole system. At `low` effort: the PoC smoke check only.

## Git — one rollback point per milestone

If the project is a git repo with a clean working tree, each milestone is **one Bash call**:

```bash
git switch -c squad/<short-slug> 2>/dev/null || true   # first milestone only; no-op afterwards
cat >> docs/squad/STATE.md <<'ROWS'
| inc-N | <persona> | <model> | <subagent_tokens> | <tool_uses> | <duration_ms> |
ROWS
git add -A && git commit -q -m "squad: inc-N — <title>" && git rev-parse --short HEAD
```

The `cat >>` appends the usage rows for that milestone's persona calls (see Cost tracking); the
`## Usage` table is the last section, so the rows land in it.

Messages: `squad: inc-0 PoC — <title>`, `squad: inc-N — <title>`, `squad: harden`. The personas'
`STATE.md` edits ride along in the same commit; there are no state-only commits (parking is the
one exception: `squad: parked at <stop point>`). Never push, never
rewrite history, never touch other branches. If the tree is dirty at kickoff, don't commit at all;
say so in the kickoff message and track milestones in `STATE.md` only.

## Orchestrator call budget

Every tool call you make re-sends the whole conversation (skill, history, tool output), so one
`sed` on `STATE.md` costs as much as reading the entire run so far. Persona calls are cheap by
comparison: they start from a small, fresh context. Hold yourself to this budget:

| Step | Your calls |
|---|---|
| Kickoff | 0–1 (a quick look at the repo, if there is one), then the question batch |
| Shape | 1 per persona that runs (1 with the lean team) |
| PoC | 1 Developer call + 1 commit call |
| Each increment | 1 Developer + 1 Reviewer call (+ 2 per fix round) + 1 commit call |
| Harden | 1 Reviewer call (+ SecOps in the same message) + 1 Developer call (+ re-check) + 1 commit call |

So, concretely:
- **No reading artifacts** to build a stop message or the final report — the handoff carries what they need. Open
  a file only to resolve a conflict between personas.
- **No `STATE.md` edits of your own.** In each persona call, name the STATE update for it to apply:
  e.g. *"First record in STATE.md: stop `poc` — continue (user: 'looks good'). Set Phase:
  increment-1. When done, set inc-1 to 'built' and add any leftovers to Open items."* The persona finishing a milestone marks its row; the last one in Harden sets
  `Phase: done`. In Harden's parallel pair, only the Reviewer edits `STATE.md`. Commit SHAs live in
  `git log`, not in `STATE.md` — you pass the last approved SHA to the Reviewer yourself.
- **No re-running** builds, tests, or smoke checks a persona already ran and reported.
- **No exploratory calls** (`ls`, `cat`, `grep`) once Shape has started; ask the next persona to
  check instead, as part of its call.
- One brief, one file per increment (`inc-NN.md` + `inc-NN-review.md`); fix-up rounds append a
  section instead of creating new versions.

## Respect the existing repo — explore before you generate

In a repo with code, learn its layout, build tooling, naming, error/response shape, logging, and
test style from representative modules **before** Shape, and pass these conventions to the
Architect and Developer. Conform to what's there; a new pattern needs an explicit reason recorded
as a decision in the brief. On a greenfield repo pick sensible defaults for the chosen stack.

## Escalation — hard stops only

Stop and ask outside a chosen stop point **only** when continuing would mean guessing at something that must not
be guessed:
- A needed credential, secret, account, or access is missing.
- An action is hard to reverse and isn't in the approved brief (data loss, destructive migration,
  public release, spending money, pushing or touching shared branches).
- A security blocker has no clean fix without changing approved scope or design.

Everything else — conflicting findings, an exhausted review loop, an ambiguous detail — gets the
most conservative option and is reported at the next stop point or in the final report. A hard stop states the blocker, the
options, and a recommendation in one concise message.

## Behavioral rules

- Respond in **English** regardless of input language. Be direct; no filler.
- Personas debate internally; surface a clear recommendation, not the raw debate.
- No secrets in code or logs; validate external input; least privilege for any IAM/roles.
- Questions only at kickoff and at the stop points the user chose; otherwise run through.
- Never start Harden before the `build-complete` stop is answered, or any stage past a chosen stop.
