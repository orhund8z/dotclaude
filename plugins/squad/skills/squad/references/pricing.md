# Pricing reference — for the final report's $ estimate

USD per million tokens (MTok), Claude API first-party rates. Source: the `claude-api` skill's
pricing table (cached 2026-10-06). **Check it before each report** — prices change, and the report
should say which date it used.

| Model | Model ID | Input $/MTok | Output $/MTok | Cache read $/MTok |
|---|---|---|---|---|
| Claude Opus 5.5 | `claude-opus-5-5` | 4.00 | 20.00 | 0.20 |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | 2.00 | 10.00 | 0.20 |
| Claude Haiku 5.5 | `claude-haiku-5-5` | 0.10 | 0.50 | not listed — assume input rate |

- Haiku 5.5 is $0.50 / $2.50 for prompts above 100K tokens.
- Cache **write** prices are not in this table; the report does not model them.

## How the report estimates $

The harness reports each subagent's `subagent_tokens` as **one total** (input + output together), so
the split is unknown. The estimate uses a blended rate per model:

    blended = 0.9 × input price + 0.1 × output price

    cost ≈ subagent_tokens × blended / 1,000,000

Label it "estimate". It can be off in either direction: cached input is far cheaper than the blend
assumes, and long outputs cost more than it assumes. The **exact** session total is `/cost` in Claude
Code; the report points there for the orchestrator's own spend, which the run cannot see.
