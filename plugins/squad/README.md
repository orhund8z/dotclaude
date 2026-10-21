# squad

A Claude Code plugin that builds software the way a small, disciplined product company would: a
**six-persona squad** (CEO, Product Manager, Architect, Developer, Reviewer, SecOps) delivers your
idea **incrementally** — a working end-to-end proof of concept first, then small demoable
increments, each tested, reviewed and committed locally.

> Full usage guide with every option, diagrams and recipes: [`skills/squad/README.md`](./skills/squad/README.md).
> Release notes: [`CHANGELOG.md`](./CHANGELOG.md) · design rationale: [`docs/DESIGN.md`](./docs/DESIGN.md).

## What it does

You describe what to build. Squad asks **one batch of kickoff questions** (clarifications, effort,
team, model profile, where you want it to stop), then runs on its own:

```
Shape ──► PoC ──► Increments ──► Harden ──► Final report
brief     thin    1…n, each      QA matrix,   what was built, decisions,
+ roadmap e2e     tested +       e2e, cover-  open items, duration and
          slice   reviewed       age, SecOps  AI cost
```

- **Shape** — the Architect (with PM/CEO on the full team) writes a brief: scope, acceptance
  criteria, stack, roadmap.
- **PoC** — the thinnest slice that runs through every layer, so you can judge the flow early.
- **Increments** — small, demoable steps; tests are written with each one, core logic test-first;
  the Reviewer checks only the new diff; each increment is a local commit.
- **Harden** — QA edge-case matrix, end-to-end tests, coverage, security review.
- **Final report** — `docs/squad/final-report.md` with results, decisions, open items, total elapsed
  time and an estimated AI cost (tokens, models, $).

It **never pushes**: all commits are local, on a `squad/<slug>` branch.

## Install

```
/plugin marketplace add orhund8z/dotclaude      # once
/plugin install squad@orhund8z
/reload-plugins                                 # or restart Claude Code
```

Verify with `/plugin list --enabled`. Only for one repo: `claude plugin install squad@orhund8z --scope project`
(shared with the team) or `--scope local` (just you). Update later with
`claude plugin marketplace update orhund8z` and `claude plugin update squad@orhund8z`.

If you previously symlinked standalone copies into `~/.claude/skills/squad` or `~/.claude/agents/`,
remove them so nothing shows up twice.

## Use it

Just ask, in a project directory:

```
Assemble the squad to build a URL shortener service
```

or `/squad:squad <what to build>`. The kickoff batch then asks for:

| Knob | Choices | Effect |
|---|---|---|
| **Effort** | low · medium · high | Depth: low = build and run; medium = tests for the major functionality + QA pass; high = exhaustive tests, ≥ 90% coverage on critical logic, full docs |
| **Team** | lean · full | lean = Architect plans alone (SecOps only if sensitive); full = CEO → PM → Architect, SecOps always in Harden |
| **Model profile** | Fast · Balanced · Deep | Which model each persona runs on (sonnet by default; Deep puts opus on CEO/PM/Architect) |
| **Stop points** | `brief` · `poc` · `each-increment` · `build-complete` · none | Where it pauses for your answer: continue · redirect · change stop points · harden now · park |

The default is **no stops** — it runs to the end. A run you **park** resumes later with
`resume the squad` (state lives in `docs/squad/STATE.md`).

## What gets created in your project

```
docs/squad/   STATE.md, brief-v1.md, inc-NN.md (+ -review), harden-*.md, final-report.md, adr/
README.md     how to run the thing that was built
SPEC.md       (medium/high) what it does and the decisions behind it
```

## What's inside the plugin

| Path | Purpose |
|---|---|
| `skills/squad/SKILL.md` | The orchestrator: kickoff, lifecycle, stop points, park/resume, cost tracking |
| `skills/squad/references/` | Artifact templates, definition of done per effort, model pricing |
| `skills/squad/scripts/usage_report.py` | Generates the final report's Duration and Cost sections from `STATE.md` |
| `agents/squad-*.md` | The six personas: `squad-ceo`, `-product-manager`, `-architect`, `-developer`, `-reviewer`, `-secops` |
| `evals/` | Behavioural checks for `claude plugin eval plugins/squad` |
| `docs/DESIGN.md`, `CHANGELOG.md` | Why it is built this way; what changed in each version |

Other skills can reuse the personas directly — for example `mcp-builder` delegates implementation and
review to `squad:squad-developer` and `squad:squad-reviewer`.

## Cost and requirements

No API keys or MCP servers are needed. A run spends tokens on the orchestrator and every persona:
typical low-effort runs cost well under $0.30, medium/high runs a few dollars. The final report gives
the subagent total; run `/cost` for the orchestrator's own share.

## License

MIT
