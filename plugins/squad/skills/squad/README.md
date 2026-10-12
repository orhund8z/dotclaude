# Squad Skill

Runs a full software development lifecycle — **Analyze → Plan → Dev → Monitor** — as a small,
opinionated software company. The skill is the **orchestrator**; the real work is done by six
persona **subagents** it delegates to.

![Squad — a software company that happens to be six AI agents: CEO, Product Manager, Architect, Developer, Reviewer +QA, and SecOps](./images/squad-hero.png)

## What it does

You give it product context and requirements. It asks **everything up front in one batch** —
clarifying questions, the **effort** level (see below), and which **model / reasoning** each
persona runs on — then drafts a plan for your approval. Once you approve the plan it **runs to
completion without asking you anything else**: implementing with tests and gating the result
through a quality + security review before "go live". Everything is documented as versioned artifacts under `docs/squad/`, and new
requirements loop back into Analyze rather than restarting.

## Effort modes

One knob controls how much gets built and how heavy the process is. You pick it in the kickoff
batch (it preselects what your request implies, otherwise recommends **medium**).

| Effort | What ships | Process weight |
|---|---|---|
| **low** | Working code that meets the requirements — no tests, no extras. | Short plan → approval → Dev, inline sanity check, `README.md` only. Fast; good for spikes, interviews, throwaways. |
| **medium** *(default)* | Code + tests for the major functionality; minimal extras. | Lean Analyze/Plan → Dev → one Reviewer pass. `README.md` + `SPEC.md`. |
| **high** | Everything — ≥90% coverage on critical logic, edge cases, ADRs, full docs. | All six personas, Reviewer + SecOps in parallel, up to 3 review rounds. |

Say *"low effort"*, *"quick"*, or *"the works / production-grade"* in your request to preselect
it; high-risk work (auth, payments, data loss) prompts a recommendation to bump up regardless.

![The effort dial — low, medium (default), high — scaling the depth of tests, docs, and review](./images/squad-effort.png)

Separately from the internal `docs/squad/` trail, once the code works the Developer writes durable
docs at the project root: a **`README.md`** (what it is, how to run, how-tos) always, plus a
**`SPEC.md`** (architecture, components, data model, interfaces, decisions, failure modes) at
medium and high.

It is **stack-agnostic** — it builds backend, frontend, CLI, service, or library projects in any
language (Java/Kotlin, Python, Go, TypeScript, …). The Architect picks the tech per problem. In a
repo that already has code, the team **explores the existing patterns first** (layout, naming,
error format, test style) and builds with the grain rather than inventing a new pattern.

## Architecture

The system is a **single orchestrator plus six cold-start subagents**. Responsibilities are split
so that one component owns *control flow* and the others own *domain thinking* — they never mix.

![Architecture — the squad orchestrator skill delegates via the Agent tool to six cold-start subagents (CEO, Product Manager, Architect, Developer, Reviewer +QA, SecOps), all reading and writing a shared docs/squad/ store](./images/squad-architecture.png)

### The two roles

- **Orchestrator (the skill).** Runs on the main thread. It does **not** do deep design or write
  production code. It sequences the phases, invokes the right persona at the right time, asks the
  kickoff questions, runs the plan approval gate, makes (and logs) every decision after it, bumps
  artifact versions, updates `STATE.md`, and handles hard stops.
- **Personas (the subagents).** Each is a specialist invoked via the **Agent tool**. It does the
  domain work for its phase, writes its own artifact, and returns a compact structured handoff.

### Why it is built this way

- **Cold-start isolation.** Subagents share no memory with the orchestrator or with each other.
  That is deliberate: each persona reasons from a clean, focused context instead of inheriting the
  whole conversation. The orchestrator compensates by passing inputs **by artifact path** (e.g.
  *"read `docs/squad/plan-v2.md` and `docs/squad/STATE.md`"*) so every persona reads the source of
  truth rather than re-deriving it. Context stays lean and pointer-based.
- **Least-privilege tooling.** Each persona gets only the tools its role needs — CEO/PM/Architect
  write docs but **cannot edit code**; the Developer is the only persona with edit + Bash;
  Reviewer/SecOps can read and run tests/scanners but **cannot edit source** (they report findings
  back). This keeps roles honest and prevents a review agent from silently "fixing" what it should
  be flagging.
- **Reasoning where the leverage is.** Each persona runs on its own model and reasoning effort,
  whatever model the session was started with (see [Model roster](#model-roster)). The strongest
  model sits on the **CEO (direction)**, **Product Manager (Analyze)** and **Architect (Plan)** —
  direction, scope and architecture are the costliest things to get wrong. Execution and review
  roles run a capable coding model.
- **Parallelism where it is safe.** Independent personas run concurrently. In Review, `squad-reviewer`
  and `squad-secops` are invoked in the same turn (two Agent calls, one message); phases with a real
  dependency stay sequential.

### Model roster

| Persona | Model | Reasoning |
|---|---|---|
| CEO | `opus` | `medium` |
| Product Manager | `opus` | `high` |
| Architect | `opus` | `high` |
| Developer | `sonnet` | `medium` |
| Reviewer | `sonnet` | `high` |
| SecOps | `sonnet` | `high` |

These are the personas' frontmatter defaults. The kickoff batch shows the roster and asks you to
confirm it (use defaults / everyone on the session model / everyone on `opus` / customise), stores
it in `STATE.md`, and passes `model` + `effort` explicitly on every Agent call, so an Architect on
`opus` is followed by a Developer on `sonnet` no matter which model you started the session with.
You can change any row at kickoff or at the plan gate — not after.

*Reasoning* (`low`…`max`) is how hard one model thinks; it is separate from the run's **effort**
(low/medium/high), which scales what gets built.

Caveats: the orchestrator itself runs on your session model (it suggests `/model opus` if you're on
something else); and `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` or an `availableModels` allowlist will
override the roster.

### The handoff contract

Every persona returns the same structured block, which is what makes the chain reliable:

```
PHASE:      <analyze | plan | dev | review | security>
ARTIFACT:   <path written>
STATUS:     <ok | needs-user-decision | blocked | changes-requested>
SUMMARY:    <2–4 sentences>
DECISIONS:  <choices made, 1-line rationale each>
OPEN:       <questions for the user, if needs-user-decision>
FINDINGS:   <review/security only: {severity, area, issue, fix}>
NEXT:       <recommended next action>
```

The orchestrator routes on `STATUS`: `ok` → advance; `needs-user-decision` → folded into the plan
before approval, decided by the orchestrator (and logged) after it — never a mid-run question;
`changes-requested` → loop back to the Developer; `blocked` → worked around, or a hard stop.

### State & versioning

All lifecycle artifacts live under `docs/squad/`:

```
docs/squad/
├── STATE.md            # effort, model roster, kickoff answers, current phase, artifact versions, decisions taken — the resume point
├── analyze-vN.md       # scope, acceptance criteria, success metrics
├── plan-vN.md          # the plan you approve: goal, FR/NFR, definition of success, architecture, stack, work plan
├── dev-vN.md           # implementation notes
├── review-vN.md        # quality review outcomes + findings
├── security-vN.md      # security review outcomes + findings
└── adr/                # architecture decision records
```

The version is **bumped on every loop iteration and never overwritten**, so history stays
auditable. `STATE.md` is read on entry and updated after each phase — an interrupted run resumes
from it instead of restarting.

## How it works (the lifecycle)

You are asked things at exactly two points:

1. **Kickoff** — one question batch: clarifying questions that change scope or design, the effort
   level, and the model / reasoning roster.
2. **Plan approval** — you approve `plan-vN.md` (or change it) before any code is written.

After that the orchestrator runs to completion on its own: each phase invokes its owner persona,
collects the handoff, updates `STATE.md`, and clears its gate. Choices that come up mid-run are
made by the orchestrator (the persona's recommendation, or the most conservative option), logged
under *Decisions taken*, and listed in the final report. It stops early only on a **hard stop** —
a missing credential/access, an irreversible action the plan didn't cover, or a security blocker
with no fix inside the approved scope.

![The lifecycle — Analyze → Plan → Dev → Review → Monitor, a loop not a line, with findings looping back to Dev and new requirements back to Analyze](./images/squad-lifecycle.png)

1. **Kickoff** — one question batch (clarifications, effort, roster). Effort scales both what gets
   built and which personas run: low collapses to Plan → Dev with an inline check; medium runs one
   Reviewer pass; high runs the full parallel Reviewer + SecOps loop.
2. **Analyze** (`squad-product-manager`, direction from `squad-ceo`). Scope, acceptance criteria,
   success metrics, assumptions → `analyze-vN.md`. No separate gate — scope is approved with the plan.
3. **Plan** (`squad-architect`, with Developer/PM input). Tech stack + architecture, the options
   weighed with pros/cons/cost and the recommended one, ADRs → `plan-vN.md` + `docs/adr/*`. On security/data-sensitive designs it
   **shifts left**, consulting SecOps (threat model) and Reviewer (testability) here.
   **Gate (every effort, before any code):** you approve `plan-vN.md` — a short document covering
   the goal, scope, functional and non-functional requirements, definition of success,
   architecture, tech stack and why, **assumptions & decisions taken**, test & verification
   strategy, risks, and a **work plan** table:

   | # | Work item | Persona | Model | Reasoning | Output | How it's verified |
   |---|---|---|---|---|---|---|

   Approve it, change who does what (persona, model, reasoning), or send scope/design back. Every
   change writes a new plan version. **This is the last question you're asked.**
4. **Dev** (`squad-developer`). Implement to the approved plan; tests per effort (≥90% on critical
   logic at high); durable `README.md`/`SPEC.md` + `dev-vN.md`. **Gate:** build + tests pass locally.
5. **Review** (`squad-reviewer` + `squad-secops`, in parallel). Findings tagged by severity go back to
   the Developer. **Bounded loop: at most 3 Dev↔Review rounds**; anything still open is reported,
   not asked about. **Gate:** Definition
   of Done — build green, coverage met, zero open blocker/major findings, docs updated, acceptance
   criteria satisfied.
6. **Monitor** (`squad-ceo` + PM). Verify the output against goals and deliver the **final report**:
   what was built, how to run it, test/coverage results, decisions taken during the run, open items.
   New requirements you raise afterwards loop back into **Analyze** — artifacts and product are
   revised, not restarted.

Consequential choices are surfaced **in the plan** — options with trade-offs and the recommended
one — so you decide them once, at approval. After that, the orchestrator decides and logs.

## Personas (subagents)

| subagent | Role | Owns / produces |
|---|---|---|
| `squad-ceo` | CEO | Direction, value/cost/ROI, go/no-go |
| `squad-product-manager` | Product Manager | Scope, requirements, acceptance criteria → `analyze-vN.md` |
| `squad-architect` | Architect | Tech stack, architecture, ADRs → `plan-vN.md` + `adr/` |
| `squad-developer` | Developer | Implementation, tests, docs (`README.md`/`SPEC.md`) → code + `dev-vN.md` |
| `squad-reviewer` | Reviewer (+ QA) | Quality/correctness/perf gate **and QA** — runs the tests, builds an edge-case matrix → `review-vN.md` |
| `squad-secops` | SecOps | Security review gate → `security-vN.md` |

![The squad — six specialists (CEO, Product Manager, Architect, Developer, Reviewer +QA, SecOps), colour-coded by tool privilege: plan/no-code, builds, and reviews](./images/squad-personas.png)

## Install

Install the `squad` plugin — it bundles this skill and the six `squad-*` personas (`../../agents/`):

```
/plugin marketplace add orhund8z/dotclaude      # once
/plugin install squad@orhund8z
/reload-plugins                                 # or restart Claude Code
```

Verify with `/plugin list --enabled`, then try:

```
Assemble the squad to build a URL shortener service
```

Only want it in one repo? `claude plugin install squad@orhund8z --scope project` (shared with the team) or `--scope local` (just you).
The personas are invoked as `squad:squad-ceo`, `squad:squad-architect`, and so on. If you previously symlinked the old standalone
files into `~/.claude/skills/squad` or `~/.claude/agents/`, remove them so nothing shows up twice.

See the repo root [README](../../../../README.md#installation) for details.

## Design

The full specification this skill and its agents are generated from lives at
[`prompts/squad.md`](../../../../prompts/squad.md) — keep that as the source of truth and regenerate the
files when the process changes.

## Kickoff

Just describe what you want built, e.g. *"build me a URL-shortener service"* or *"run the squad on
this feature"*. The team opens with one batch of questions (clarifications, effort, models &
reasoning), comes back once with the plan for approval, then runs to completion.
