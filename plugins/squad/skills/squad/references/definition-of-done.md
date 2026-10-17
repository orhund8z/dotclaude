# Definition of Done

Acceptance criteria from the approved brief must be satisfied at **every** effort.

## Per milestone

| Milestone | Done when |
|---|---|
| **PoC (inc-0)** | The end-to-end happy path runs with one command; the smoke check passes; run instructions exist. No unit tests required. |
| **Increment N** | Its acceptance criteria each map to a passing test; all earlier tests still green; Reviewer reports zero open blocker/major findings for this diff (or the 2-round bound was hit and leftovers are listed at the gate); `README.md` updated; committed. |
| **Harden** | As below, by effort. |

## Release, by effort

- **low** — The PoC/product builds and runs and meets the requirements; `README.md` present; your
  smoke check done. No test or review gate.
- **medium** — Build passes; tests for the major/critical functionality green; Harden QA pass on
  critical paths done; **zero open blocker/major findings** (SecOps too, if it ran);
  `README.md` + concise `SPEC.md` present.
- **high** — Build passes; all tests green; **≥ 90% coverage on critical logic** with the edge-case
  matrix covered; end-to-end tests for the main flows; **zero open blocker/major findings** from
  Reviewer *and* SecOps (minors may be deferred with a logged follow-up); full docs (`README.md`,
  `SPEC.md`, code structure & domain model, contributing/run/test guide, ADRs, end-user docs when
  relevant).

## Severity scale (Reviewer and SecOps)

| Severity | Meaning | Blocks the milestone? |
|---|---|---|
| **blocker** | Wrong result, data loss, exploitable vulnerability, build/test broken | Yes |
| **major** | Missing acceptance criterion, untested critical path, significant perf/security weakness | Yes |
| **minor** | Maintainability, naming, small gaps with low impact | No — log as follow-up |
| **nit** | Style | No |
