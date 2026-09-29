# dotclaude

Personal AI toolkit — Claude skills, prompts, and automation workflows.

## Structure

```
dotclaude/
├── .claude-plugin/
│   └── marketplace.json        # the `orhund8z` marketplace — catalog only
├── plugins/                    # published plugins, one self-contained package each
│   ├── job-evaluator/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/job-evaluator/   # SKILL.md, SETUP.md, PROFILE.example.md
│   ├── squad/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/squad/       # orchestrator skill
│   │   └── agents/squad-*.md   # the six personas
│   └── storm-analyzer/
│       ├── .claude-plugin/plugin.json
│       └── skills/storm-analyzer/
├── skills/          # personal, unpublished skills (~/.claude/skills/)
│   ├── ats-job-scan/
│   ├── atlas/
│   ├── job-tracker/
│   └── mcp-builder/
├── prompts/         # Reusable prompt templates
└── docs/            # Notes, setup guides, decisions
```

## Skills

Skills are modular instruction packages for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) that trigger automatically from natural language. `job-evaluator`, `squad` and `storm-analyzer` are published as [plugins](#install-as-plugins-marketplace); the rest are personal skills you drop into `~/.claude/skills/`.

| Skill | Description | Language |
|-------|-------------|----------|
| [job-evaluator](./plugins/job-evaluator/skills/job-evaluator/) | Evaluates companies and offers against a personal career profile using Glassdoor, Kununu, Levels.fyi, Comprehensive.io, LinkedIn, Xing, Indeed.de, Monster.de, Remotely.de, Layoffs.fyi. Scores each opportunity with a **Career Value Index (CVI)** — total compensation, Fair Share Ratio (pay vs. what the company can afford), equity upside, career capital, and stability. | 🇬🇧 English |
| [job-tracker](./skills/job-tracker/) | Watches a configured company list for openings that match your profile, and discovers other companies working on your topics that are hiring. Produces a self-contained HTML report in two groups — **Tracked** and **Suggested** — with `🆕` badges for postings new since the previous run. | 🇬🇧 English |
| [ats-job-scan](./skills/ats-job-scan/) | Company-agnostic job radar: discovers thousands of Ashby and Greenhouse job boards (Common Crawl + local seeds), fetches them through the public APIs with per-host rate limiting, keeps Munich (any work model) or remote-Germany/Europe/worldwide roles, scores fit (title, skills, stated pay vs. threshold, freshness, penalties) and writes a **dated markdown report** with `🆕` for postings new since the last scan. Standard-library Python; `--rescore` re-tunes filters in seconds. | 🇬🇧 English |
| [mcp-builder](./skills/mcp-builder/) | Scaffolds and implements TypeScript MCP servers — shared repo layout, tool-surface design, idempotency/conflict gating, tool annotations, resilience/cost guardrails, low/medium/high effort modes, existing-convention matching, and mandatory smoke-test verification (+ committed test suite at medium/high). Can delegate implementation/review to the `squad-*` subagents. | 🇬🇧 English |
| [squad](./plugins/squad/skills/squad/) | Runs a full software development lifecycle (Analyze → Plan → Dev → Monitor) as a six-persona software company; orchestrates the `squad-*` subagents. Stack-agnostic, with low/medium/high effort modes, explore-the-existing-repo-first discipline, and durable `README.md`/`SPEC.md` deliverables. | 🇬🇧 English |
| [storm-analyzer](./plugins/storm-analyzer/skills/storm-analyzer/) | Turns any topic into a structured, STORM-style analysis by simulating five expert perspectives, mapping contradictions, and synthesizing an executive-ready briefing with a role-tailored peer review. | 🇬🇧 English |

## Agents

Subagents are specialised personas that skills (or you) delegate to. The `squad-*` agents ship
inside the `squad` plugin (`plugins/squad/agents/`) and power the [squad](./plugins/squad/skills/squad/) skill.

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

### Install as plugins (marketplace)

Three plugins are published through the `orhund8z` marketplace, defined in
[`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json):

| Plugin | What you get | Try it after installing |
|--------|--------------|-------------------------|
| `job-evaluator` | Company / offer evaluation with a Career Value Index; guided profile setup on first use | `Evaluate Zalando` |
| `squad` | The `squad` skill plus its six `squad:squad-*` persona agents | `Assemble the squad to build a URL shortener service` |
| `storm-analyzer` | Multi-area research briefing with contradictions and ranked findings | `/storm-analyzer:storm-analyzer Should we adopt a service mesh? \| Principal Engineer` |

**1. Add the marketplace (once)**

```
/plugin marketplace add orhund8z/dotclaude
```

Same thing from a shell: `claude plugin marketplace add orhund8z/dotclaude`.
`orhund8z/dotclaude` is the GitHub `owner/repo`; a full git URL or a local path also works
(handy for testing unpushed changes: `/plugin marketplace add ~/dotclaude`).

**2. Install the plugins you want**

```
/plugin install job-evaluator@orhund8z
/plugin install squad@orhund8z
/plugin install storm-analyzer@orhund8z
```

Or from a shell: `claude plugin install squad@orhund8z`. Prefer a menu? Run `/plugin`, open **Discover**,
pick a plugin, and choose an install scope.

**3. Activate**

Run `/reload-plugins` (or restart Claude Code). Plugin skills are namespaced, so `squad:squad` and
`storm-analyzer:storm-analyzer` are their full names (use them for slash commands); natural-language triggers work as before.

**4. Verify**

```
/plugin list --enabled
```

You should see `job-evaluator@orhund8z`, `squad@orhund8z`, `storm-analyzer@orhund8z`, each marked enabled.

**Install scopes**

| Scope | Flag | Where it applies | Example |
|-------|------|------------------|---------|
| user (default) | `--scope user` | All your projects | `claude plugin install storm-analyzer@orhund8z` |
| project | `--scope project` | This repo only, shared with the team via `.claude/settings.json` | `claude plugin install squad@orhund8z --scope project` |
| local | `--scope local` | This repo only, just you (not committed) | `claude plugin install squad@orhund8z --scope local` |

**Update, disable, remove**

```
claude plugin marketplace update orhund8z     # pull the latest catalog
claude plugin update squad@orhund8z           # then restart Claude Code to apply
claude plugin disable squad@orhund8z          # keep installed, turn off
claude plugin uninstall squad@orhund8z
claude plugin marketplace list                # registered marketplaces
```

**Per-plugin notes**

- **job-evaluator** — On first use there is no profile yet, so it interviews you (roles, priorities, salary floor, tech, dealbreakers) and saves it to `~/.claude/job-evaluator/PROFILE.md`, outside the plugin, so updates never overwrite it. Re-run it any time with `update my profile`. Web search works out of the box; the Tavily MCP server ([setup guide](./docs/tavily-mcp-setup.md)) is optional but more thorough.
- **squad** — Nothing else to set up; the personas ship inside the plugin and are invoked as `squad:squad-ceo`, `squad:squad-architect`, and so on.
- **storm-analyzer** — Runs the 5 research areas as parallel subagents and uses web search for source links, so it works best with both available.
- **Already installed the old standalone copies?** If you previously symlinked these into `~/.claude/skills/` or `~/.claude/agents/`, remove them after installing the plugin, otherwise each skill shows up twice.

Validate the marketplace after editing it: `claude plugin validate .`

### Install a personal skill globally (available in all projects)

```bash
# Clone the repo
git clone https://github.com/orhund8z/dotclaude.git ~/dotclaude

# Symlink a skill into Claude Code's skills directory
mkdir -p ~/.claude/skills

mkdir -p ~/.claude/skills/mcp-builder
ln -s ~/dotclaude/skills/mcp-builder/SKILL.md ~/.claude/skills/mcp-builder/SKILL.md
```

Or copy manually:

```bash
cp -r ~/dotclaude/skills/mcp-builder ~/.claude/skills/
```

Then restart Claude Code — the skill auto-loads on session start.

### Install a skill per-project

```bash
mkdir -p .claude/skills
ln -s ~/dotclaude/skills/mcp-builder .claude/skills/mcp-builder
```

## Dependencies

Some skills require external tools or API keys. See each skill's README for details.

| Skill | Requires |
|-------|----------|
| job-evaluator | Tavily MCP for web search (see [setup guide](./docs/tavily-mcp-setup.md)); a personal profile at `~/.claude/job-evaluator/PROFILE.md`, created by the guided setup on first run |
| job-tracker | Tavily MCP for web search (see [setup guide](./docs/tavily-mcp-setup.md)); local `CONFIG.md` copied from `CONFIG.example.md` |
| ats-job-scan | Python 3.9+ (standard library only) and network access; local `config.json` and `local.json` copied from the `*.example.json` templates |
| mcp-builder | Node.js (v22+ recommended), `@modelcontextprotocol/sdk` + `zod` + `tsx`/`typescript`/`vitest` (scaffolded automatically); TypeScript only |
| squad | Nothing extra — the `squad-*` subagents ship inside the plugin |
| storm-analyzer | None — self-contained prompt template |

## Adding a New Skill

**Personal skill** (not published) — add it under `skills/`:

```
skills/
└── your-skill-name/
    ├── SKILL.md       # required — frontmatter + instructions
    ├── README.md      # optional — usage notes, examples
    └── scripts/       # optional — helper scripts
```

**Published plugin** — add a self-contained package under `plugins/` and one line to the marketplace:

```
plugins/
└── your-plugin/
    ├── .claude-plugin/plugin.json   # name, description, author, license
    ├── skills/<skill>/SKILL.md      # and/or agents/, hooks/, .mcp.json
    └── README.md
```

```json
{ "name": "your-plugin", "source": "./plugins/your-plugin" }
```

Never put plugin components at the repo root, and run `claude plugin validate .` before pushing.

Refer to the [Claude Code skill authoring docs](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) for the full spec.
