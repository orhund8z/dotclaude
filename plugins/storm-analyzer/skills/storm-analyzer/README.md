# storm-analyzer

A Claude Code skill that turns any topic into a structured, multi-perspective research briefing using the Stanford **STORM** method (Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking).

Given a topic (and optionally a professional role), it simulates five expert perspectives, maps where they contradict each other, synthesizes the findings into an executive-ready briefing, and finishes with a self-critical peer review — all in a single response.

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

1. **Multi-perspective scan** — simulates 5 expert viewpoints: Practitioner, Academic, Skeptic, Economist, Historian. Each gets a core position, supporting evidence, and one unique insight.
2. **Contradiction map** — identifies direct clashes between perspectives, evaluates evidence strength, proposes one key resolution question, lists shared ground, and flags blind spots.
3. **Synthesis briefing** — a one-paragraph executive summary, 5 key findings ranked by reliability, one hidden cross-perspective connection, actionable recommendations tailored to the given role, and one frontier (open) question.
4. **Peer review & self-critique** — confidence scores (1–10) for each finding, the weakest link and what would strengthen it, a bias check across perspectives, a proposed 6th missing perspective, and an overall letter grade with concrete improvements.

## Output

A single structured response in English with clearly labeled sections (`PHASE 1` – `PHASE 4`). No follow-up questions are asked — the skill works from the topic and role provided upfront.

## Requirements

None beyond Claude Code itself — this skill is a self-contained prompt template with no external tools, MCP servers, or API keys required.

## Installation

```bash
cp -r skills/storm-analyzer ~/.claude/skills/
# or symlink:
ln -s $(pwd)/skills/storm-analyzer ~/.claude/skills/storm-analyzer
```

Restart Claude Code after installation.

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | The prompt template and instructions |
| `README.md` | This file |

## License

MIT
