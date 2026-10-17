---
type: llm
focus: trace
weight: 1
---
Every Agent (subagent) call in the trace passes an explicit `model` and an explicit `effort`/reasoning value. The Architect call uses `sonnet` with `high` effort (the Balanced profile). No Product Manager or CEO persona is invoked (medium effort uses a single Architect call for Shape).
