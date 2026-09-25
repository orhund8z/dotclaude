# mcp-builder

A Claude Code skill for building TypeScript **MCP (Model Context Protocol)**
servers. Not generic best practice — it encodes the exact conventions and
war stories from building and debugging four real servers (`infra`,
`calendar`, `books`, `weather`) in a shared multi-server repo, including a
real correctness bug (a silently-broken conflict gate) that was only caught
because the skill's own verification step wasn't skipped.

## Usage

Just describe the server you want in normal language — the skill triggers on
requests like:

```
add an MCP server for <thing>
build an MCP tool that does <X>
create an MCP server exposing <API/service>
```

The skill asks a **focused batch of clarifying questions up front** (goal,
read-only vs mutating, what backs it, whether the upstream API actually
covers everything you asked for) rather than guessing and building the wrong
shape, then **restates the resolved scope and waits for confirmation**
before writing any code — the same "confirm scope before you build" gate the
`squad` skill uses before Analyze → Plan.

## Effort modes

Like the `squad` skill, this build has an **effort** knob that scales the test
suite and docs (never the correctness essentials). It **defaults to medium**
and states which it's running.

| Effort | Ships | Verification |
|---|---|---|
| **low** | Working server, minimal README, no committed test suite. | Clean build **+** one real end-to-end call (the floor — never skipped). |
| **medium** *(default)* | Server + a focused Vitest suite on the major functionality + a proper README. | Build + focused `npm test` + one real call; one Reviewer pass if available. |
| **high** | Full test suite, resilience/rate-limit/bounds, full docs. | Everything, plus Reviewer + SecOps in parallel. |

Logs-to-stderr, structured `isError` returns, `AbortController` timeouts, zod
validation, and the conflict/idempotency correctness for mutating tools hold
at **every** effort — the knob only moves the test/doc depth.

## How it works

The skill walks through a fixed sequence and won't skip the last step even
if everything looks fine:

1. **Find or scaffold the repo** — detects the shared-repo layout (one root
   `package.json`/`tsconfig.json`, servers under `src/<name>/`, one build) or
   creates it if this is the first server. When servers already exist, it
   **explores a sibling server first and mirrors its conventions** (helper
   shape, error format, logging, test style) instead of inventing a new one.
2. **Gather requirements and confirm scope** — one batch of clarifying
   questions covering the actual goal, read-only vs mutating, what backs it
   (keyless public API / API-key / OAuth), and whether the request implies
   capability the backend doesn't actually have (the "search
   books/weather/countries" via a books-only API case this was built from) —
   then a short restatement of what's about to be built, confirmed before
   moving on. For multi-server or unfamiliar-domain requests, this can be
   **delegated to the `squad-product-manager` subagent** instead of
   improvising (see "Squad integration" below).
3. **Design the tool surface** — one responsibility per tool (composable,
   chainable), a prompt to chain them when there's a common workflow, trimmed
   API responses, passthrough pagination.
4. **Implement** — the McpServer/zod/stdio boilerplate, structured
   `isError` responses instead of throws, `AbortController` timeouts on
   external calls, the conflict-detection + idempotency pattern for
   mutating tools (with the exact bug to avoid, verbatim), and the
   pluggable-backend pattern for servers that might later point at a real
   integration. **Delegated to the `squad-developer` subagent** when it's
   installed (see "Squad integration" below), so implementation gets a fresh,
   focused pass and the same coding discipline as any squad-built project.
5. **Wire up scripts and docs** — `package.json` bin/scripts, per-server
   README template, root README table + layout update.
6. **Build and verify — never skipped** — `npm run build` plus a one-time
   real-API smoke test are the floor at *every* effort. At medium/high it also
   commits a Vitest suite alongside the server (happy paths, validation errors,
   and edge cases — especially the optional-field-omitted case, where the real
   bug hid) and uses the MCP Inspector for interactive checks. Only reports done
   after this passes.
   Review of the result (correctness + security) is **delegated to
   `squad-reviewer` and `squad-secops` in parallel** when installed.
7. **Optional OAuth setup** — for servers that need to authenticate against
   a real user account (e.g. a real calendar), a one-time local
   refresh-token helper script, not interactive auth inside the server
   itself.

## Requirements

- Node.js (used with v22 in the source repo; anything with native `fetch`
  and top-level ESM works).
- `@modelcontextprotocol/sdk`, `zod`, and (dev) `tsx`/`typescript` — the
  skill scaffolds these into `package.json` if the repo doesn't exist yet.
- The MCP Inspector (`@modelcontextprotocol/inspector`) is used via `npx`,
  no separate install needed.
- Scope: **TypeScript only.** Python MCP SDK (FastMCP) conventions are not
  covered — this skill only encodes patterns that were actually built and
  tested.

## Squad integration

This skill doesn't merge with the `squad` skill — it keeps owning MCP-specific
judgment (scope, tool-surface design, docs, OAuth) and only *borrows* its
questioning discipline and two of its persona subagents for the generic
parts of the work:

- **Requirements gathering** (Step 2) always asks one focused question batch
  and confirms scope before design, same as squad's kickoff/Analyze gate; for
  multi-server or unfamiliar-domain requests it can hand off to
  **`squad-product-manager`** instead of improvising the scope.
- **`squad-developer`** implements the server (Step 4) — given the resolved
  tool surface plus this skill's `SKILL.md` as the spec.
- **`squad-reviewer`** + **`squad-secops`** review it in parallel (Step 6) —
  correctness against the edge cases above, and security (secrets, injection,
  timeout surface). Findings loop back to `squad-developer`, bounded to 3
  rounds before escalating.

This is a lightweight borrow: no `docs/squad/` artifact trail or `STATE.md` is
created. If those subagents aren't installed (see
[`plugins/squad/skills/squad/README.md#install`](../../plugins/squad/skills/squad/README.md#install)), the skill
falls back to doing Steps 4 and 6 inline.

## Installation

```bash
cp -r skills/mcp-builder ~/.claude/skills/
# or symlink:
ln -s $(pwd)/skills/mcp-builder ~/.claude/skills/mcp-builder
```

Restart Claude Code after installation.

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | The step-by-step build instructions, code templates, and the concrete bug this skill was written to prevent repeating |
| `README.md` | This file |

## Source

Derived from a live session building and hardening the `mcp-servers` repo:
`infra` (read-only starter), `calendar` (mutating, conflict-gated,
idempotent, with an optional Google Calendar backend), `books` (OpenLibrary
search, correctly scoped after an initial over-broad request), and `weather`
(Open-Meteo, geocode-then-forecast).
