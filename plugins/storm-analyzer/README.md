# storm-analyzer

A Claude Code plugin that turns **any topic** into a structured, multi-perspective research briefing
using the Stanford **STORM** method (Synthesis of Topic Outlines through Retrieval and
Multi-perspective Question Asking).

> Skill-level details (phases, output format, requirements): [`skills/storm-analyzer/README.md`](./skills/storm-analyzer/README.md).

## What it does

Given a topic — and optionally a professional role — it acts as a research coordinator:

1. splits the topic into **five independent research areas** (at least one hunts counter-evidence)
   and researches them **in parallel**;
2. **merges** the results: deduplicates, flags every contradiction with both sides shown, lists weak
   evidence;
3. writes a **synthesis briefing**: executive summary, the five findings ranked by how much they
   would change the answer, a hidden cross-area connection, role-tailored recommendations, an open
   question;
4. closes with a **self-critical peer review**: confidence scores, weakest link, bias check, a
   missing perspective, and a letter grade.

Every claim carries a source link or is marked "no source". It never asks follow-up questions.

## Install

```
/plugin marketplace add orhund8z/dotclaude      # once
/plugin install storm-analyzer@orhund8z
/reload-plugins                                 # or restart Claude Code
```

Verify with `/plugin list --enabled`. For a single repo add `--scope project` (shared) or
`--scope local` (just you) to `claude plugin install storm-analyzer@orhund8z`. Update with
`claude plugin marketplace update orhund8z` and `claude plugin update storm-analyzer@orhund8z`.

## Use it

```
/storm-analyzer:storm-analyzer <topic>
/storm-analyzer:storm-analyzer <topic> | <role>
```

Examples:

```
/storm-analyzer:storm-analyzer Should we adopt a service mesh for our Kubernetes clusters?
/storm-analyzer:storm-analyzer LLM-based code review tools | Principal Engineer
```

If the role is empty or generic, a suitable professional role is inferred from the topic. (Installed
as a plugin the slash command is namespaced; copied manually into `~/.claude/skills/` it is plain
`/storm-analyzer`.)

## Requirements

Works with Claude Code alone, better with:

- **Subagent tool** — runs the five areas in parallel (otherwise sequentially, kept separate).
- **Web search / fetch** — real source links (otherwise claims come from model knowledge, marked
  "no source" with low confidence).

No MCP servers or API keys. The run is token-heavy (five parallel researchers plus synthesis), so use
it for questions worth a briefing, not quick lookups.

## What's inside

| Path | Purpose |
|---|---|
| `skills/storm-analyzer/SKILL.md` | The prompt template and instructions |
| `skills/storm-analyzer/README.md` | Skill-level guide |

Credits to Nav Toor: https://x.com/heynavtoor/status/2067194761446920264

## License

MIT
