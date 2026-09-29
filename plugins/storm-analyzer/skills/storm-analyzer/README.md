# storm-analyzer

A Claude Code skill that turns any topic into a structured, multi-perspective research briefing using the Stanford **STORM** method (Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking).

Given a topic (and optionally a professional role), it acts as a research coordinator: it splits the topic into five independent research areas, has each one researched in parallel, merges the results (deduplicating, flagging contradictions and weak evidence), ranks the five findings that change the answer most, and finishes with a self-critical peer review — all in a single response.

Credits to Nav Toor: https://x.com/heynavtoor/status/2067194761446920264

## Usage

```
/storm-analyzer <topic>
```

```
/storm-analyzer <topic> | <role>
```

If no role is given, or the role string is empty/generic, the skill infers a reasonable professional role from the topic.

Examples:

```
/storm-analyzer Should we adopt a service mesh for our Kubernetes clusters?
```

```
/storm-analyzer LLM-based code review tools | Principal Engineer
```

## How it works

The skill runs through 4 internal phases in one pass:

1. **Decompose & dispatch** — splits the topic into 5 independent research areas (at least one dedicated to counter-evidence) and researches them in parallel, one subagent per area. Each area returns only: claim, evidence, caveat, source link, and confidence.
2. **Merge & cross-check** — deduplicates claims, flags every contradiction with both sides shown, lists weak evidence (single/no source, stale, biased), and notes shared ground and blind spots. Disagreements are never silently resolved.
3. **Synthesis briefing** — a one-paragraph executive summary, the top 5 findings ranked by how much they would change the answer (not by reliability), one hidden cross-area connection, role-tailored recommendations, and one frontier (open) question.
4. **Peer review & self-critique** — confidence scores (1–10) for each finding, the weakest link and what would strengthen it, a bias check, a proposed 6th missing perspective, and an overall letter grade with concrete improvements.

## Output

A single structured response in English with clearly labeled sections (`PHASE 1` – `PHASE 4`). Every claim carries a source link or is marked "no source". No follow-up questions are asked — the skill works from the topic and role provided upfront.

## Requirements

Works with Claude Code alone, but is much better with:

- **Subagent tool** (Agent/Task) — runs the 5 research areas in parallel. Without it, the skill researches the areas sequentially and keeps them separate.
- **Web search / fetch** — needed for real source links. Without it, claims come from model knowledge and are marked "no source" with low confidence.

No MCP servers or API keys are required.

## Installation

```
/plugin marketplace add orhund8z/dotclaude      # once
/plugin install storm-analyzer@orhund8z
/reload-plugins                                 # or restart Claude Code
```

Verify with `/plugin list --enabled`, then try (installed as a plugin, the slash command is namespaced):

```
/storm-analyzer:storm-analyzer LLM-based code review tools | Principal Engineer
```

From a shell: `claude plugin install storm-analyzer@orhund8z` (add `--scope project` to share it with a repo's team).
Update later with `claude plugin marketplace update orhund8z` and `claude plugin update storm-analyzer@orhund8z`.

Manual alternative (no plugin): `cp -r plugins/storm-analyzer/skills/storm-analyzer ~/.claude/skills/`, then restart Claude Code.
Don't do both — the skill would show up twice.

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | The prompt template and instructions |
| `README.md` | This file |

## License

MIT
