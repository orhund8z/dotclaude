# dotclaude

Personal AI toolkit — Claude skills, prompts, and automation workflows.

## Structure

```
dotclaude/
├── skills/          # Claude Code skills (~/.claude/skills/)
│   ├── job-evaluator/
│   │   └── SKILL.md
│   ├── job-tracker/
│   │   └── SKILL.md
│   ├── mcp-builder/
│   │   └── SKILL.md
│   ├── squad/
│   │   └── SKILL.md
│   └── storm-analyzer/
│       └── SKILL.md
├── agents/          # Claude Code subagents (~/.claude/agents/)
│   └── squad-*.md
├── prompts/         # Reusable prompt templates
└── docs/            # Notes, setup guides, decisions
```

## Skills

Skills are modular instruction packages for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview). Drop them into `~/.claude/skills/` and they trigger automatically from natural language.

| Skill | Description | Language |
|-------|-------------|----------|
| [job-evaluator](./skills/job-evaluator/) | Evaluates companies and offers against a personal career profile using Glassdoor, Kununu, Levels.fyi, Comprehensive.io, LinkedIn, Xing, Indeed.de, Monster.de, Remotely.de, Layoffs.fyi. Scores each opportunity with a **Career Value Index (CVI)** — total compensation, Fair Share Ratio (pay vs. what the company can afford), equity upside, career capital, and stability. | 🇬🇧 English |
| [job-tracker](./skills/job-tracker/) | Watches a configured company list for openings that match your profile, and discovers other companies working on your topics that are hiring. Produces a self-contained HTML report in two groups — **Tracked** and **Suggested** — with `🆕` badges for postings new since the previous run. | 🇬🇧 English |
| [mcp-builder](./skills/mcp-builder/) | Scaffolds and implements TypeScript MCP servers — shared repo layout, tool-surface design, idempotency/conflict gating, tool annotations, resilience/cost guardrails, low/medium/high effort modes, existing-convention matching, and mandatory smoke-test verification (+ committed test suite at medium/high). Can delegate implementation/review to the `squad-*` subagents. | 🇬🇧 English |
| [squad](./skills/squad/) | Runs a full software development lifecycle (Analyze → Plan → Dev → Monitor) as a six-persona software company; orchestrates the `squad-*` subagents. Stack-agnostic, with low/medium/high effort modes, explore-the-existing-repo-first discipline, and durable `README.md`/`SPEC.md` deliverables. | 🇬🇧 English |
| [storm-analyzer](./skills/storm-analyzer/) | Turns any topic into a structured, STORM-style analysis by simulating five expert perspectives, mapping contradictions, and synthesizing an executive-ready briefing with a role-tailored peer review. | 🇬🇧 English |

## Agents

Subagents are specialised personas that skills (or you) delegate to. Drop them into
`~/.claude/agents/`. The `squad-*` agents power the [squad](./skills/squad/) skill.

| Agent | Role |
|-------|------|
| `squad-ceo` | Direction, value/cost/ROI, go/no-go |
| `squad-product-manager` | Scope, requirements, acceptance criteria |
| `squad-architect` | Tech stack, architecture, ADRs |
| `squad-developer` | Implementation, tests, docs (`README.md`/`SPEC.md`) |
| `squad-reviewer` | Quality / correctness / performance review gate **+ QA** (test-plan review, edge-case matrix) |
| `squad-secops` | Security review gate |

The specification these are generated from lives at [`prompts/squad.md`](./prompts/squad.md).

## Installation

### Install a skill globally (available in all projects)

```bash
# Clone the repo
git clone https://github.com/odalabasmaz/dotclaude.git ~/dotclaude

# Symlink a skill into Claude Code's skills directory
mkdir -p ~/.claude/skills

mkdir -p ~/.claude/skills/job-evaluator
ln -s ~/dotclaude/skills/job-evaluator/SKILL.md ~/.claude/skills/job-evaluator/SKILL.md
```

Or copy manually:

```bash
cp -r ~/dotclaude/skills/job-evaluator ~/.claude/skills/
```

Then restart Claude Code — the skill auto-loads on session start.

### Install agents globally

Some skills delegate to subagents. Install them into `~/.claude/agents/`:

```bash
mkdir -p ~/.claude/agents

# Symlink all squad-* persona agents (used by the squad skill)
for f in ~/dotclaude/agents/squad-*.md; do
  ln -s "$f" ~/.claude/agents/"$(basename "$f")"
done
```

The `squad` skill needs both its skill directory and the `squad-*` agents installed.

### Install a skill per-project

```bash
mkdir -p .claude/skills
ln -s ~/dotclaude/skills/job-evaluator .claude/skills/job-evaluator
```

## Dependencies

Some skills require external tools or API keys. See each skill's README for details.

| Skill | Requires |
|-------|----------|
| job-evaluator | Tavily MCP for web search (see [setup guide](./docs/tavily-mcp-setup.md)) |
| job-tracker | Tavily MCP for web search (see [setup guide](./docs/tavily-mcp-setup.md)); local `CONFIG.md` copied from `CONFIG.example.md` |
| mcp-builder | Node.js (v22+ recommended), `@modelcontextprotocol/sdk` + `zod` + `tsx`/`typescript`/`vitest` (scaffolded automatically); TypeScript only |
| squad | The `squad-*` subagents installed (see [Agents](#agents) below) |
| storm-analyzer | None — self-contained prompt template |

## Adding a New Skill

```
skills/
└── your-skill-name/
    ├── SKILL.md       # required — frontmatter + instructions
    ├── README.md      # optional — usage notes, examples
    └── scripts/       # optional — helper scripts
```

Refer to the [Claude Code skill authoring docs](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) for the full spec.
