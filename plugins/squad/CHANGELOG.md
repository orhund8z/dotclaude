# Changelog — squad

All notable changes to the `squad` plugin. Versions follow [Semantic Versioning](https://semver.org/).
The reasons behind each change are in [`docs/DESIGN.md`](./docs/DESIGN.md).

## 2.0.0

### Changed (breaking)
- **Lifecycle is incremental:** Shape → PoC → Increments → Harden replaces
  Analyze → Plan → Dev → Review → Monitor.
- **Gates at every milestone:** Brief, PoC, and each increment — approve, redirect, "approve the
  rest" (autopilot), or stop and harden. Still no questions between gates.
- **Default models are sonnet.** New model profiles — Fast, Balanced (default), Deep — tied to
  effort; opus only in Deep (PM, Architect, CEO). Persona frontmatter defaults are now the
  Balanced profile.
- **Artifacts:** `brief-vN.md` + `inc-NN.md` / `inc-NN-review.md` + `harden-*.md` replace
  `analyze-vN` / `plan-vN` / `dev-vN` / `review-vN` / `security-vN`.
- At medium effort one Architect call writes scope, design, and roadmap; PM and CEO run only at
  high effort (CEO also on request).

### Added
- **Hybrid testing:** PoC smoke check only; tests with each increment (TDD for core logic); edge
  cases, end-to-end, coverage, and security in Harden.
- Diff-scoped increment reviews; Reviewer `harden` mode for the full QA pass.
- One local commit per approved milestone on a `squad/<slug>` branch (never pushed).
- Personas run in the foreground so a gate is never lost after a background notification.
- Cost discipline: ≤ 200-word handoffs, orchestrator reads handoffs not artifacts, session-model
  recommendation at kickoff.
- `references/artifacts.md` (templates) and `references/definition-of-done.md`.
- Behavioural evals (`evals/`), CI validation, `docs/DESIGN.md`, Mermaid diagrams, regenerable
  images (`images/src/`).

### Fixed
- Reviewer and SecOps were told to write their reports but had no `Write` tool.

### Removed
- `prompts/squad.md` (hand-synced spec) — replaced by `docs/DESIGN.md`; the original prompt is kept
  as `docs/original-prompt.txt`.
- Separate Monitor phase — replaced by the final report and roadmap revisions.

## 1.1.0
- Ask once up front (clarifications, effort, model roster), approve the plan, then run to
  completion without further questions; the final report ends without a question.
- CEO default model switched to opus.

## 1.0.0
- Initial plugin: six personas (CEO, PM, Architect, Developer, Reviewer + QA, SecOps), effort modes,
  per-persona model roster, Analyze → Plan → Dev → Monitor lifecycle.
