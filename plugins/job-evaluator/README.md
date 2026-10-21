# job-evaluator

A Claude Code plugin that evaluates **companies, job postings and offers** against *your* career
profile and scores them with a **Career Value Index (CVI)** — a 0–100 estimate of long-term career
value rather than headline salary.

> Full guide (report sections, CVI maths, search tools, Tavily setup): [`skills/job-evaluator/README.md`](./skills/job-evaluator/README.md).
> First-run interview: [`skills/job-evaluator/SETUP.md`](./skills/job-evaluator/SETUP.md).

## What it does

Give it a company name, URL, or two offers. It searches Glassdoor, Kununu, Levels.fyi, LinkedIn,
Xing, StepStone, de.indeed.com, Layoffs.fyi and more, and writes a sourced English report:

- quick overview (ratings, layoffs), research checklist, pros/cons;
- **expected salary range** for this role/level/location, triangulated from weighted sources, with
  the arithmetic shown;
- total compensation breakdown, **candidate fit** against your profile, open positions with links;
- the **CVI** (pillar breakdown, Fair Share Ratio, 2–5 year market-value projection);
- a decision — 🟢 Apply / 🟡 Research more / 🔴 Skip.

It also compares offers side by side, and runs a lightweight **salary check** if you only ask what a
role pays.

## Install

```
/plugin marketplace add orhund8z/dotclaude      # once
/plugin install job-evaluator@orhund8z
/reload-plugins                                 # or restart Claude Code
```

Verify with `/plugin list --enabled`. Single repo: add `--scope project` or `--scope local`. Update
with `claude plugin marketplace update orhund8z` and `claude plugin update job-evaluator@orhund8z`.
If you used the old symlink in `~/.claude/skills/job-evaluator`, remove it so the skill doesn't show
up twice.

## Use it

No slash command needed — just ask:

```
Evaluate Zalando
Prepare a report for N26, Celonis, and HelloFresh
https://www.personio.com — should I apply here?
I have two offers: N26 €130k base + 10% bonus, and Celonis €120k + VSOP. Which one?
```

## Your profile (first run)

The skill is **profile-driven**: every fit score and salary threshold comes from
`~/.claude/job-evaluator/PROFILE.md`. On first use there is none, so it runs a short guided interview
(role, ranked priorities, salary floor, equity, tech, dealbreakers), writes the profile, then
continues with your request. The file lives outside the plugin, so updates never overwrite it and it is
never committed. Re-run any time with `setup job-evaluator` or `update my profile`; to edit by hand,
copy `PROFILE.example.md` to that path.

## Requirements

Built-in `WebSearch`/`WebFetch` work out of the box. The **Tavily MCP server** is optional (paid, deeper
and more reliable research) — setup and credit costs are in the skill README. No other keys needed.

## What's inside

| Path | Purpose |
|---|---|
| `skills/job-evaluator/SKILL.md` | The evaluation instructions, CVI definition, data-integrity rules |
| `skills/job-evaluator/SETUP.md` | Profile interview flow |
| `skills/job-evaluator/PROFILE.example.md` | Profile template |
| `skills/job-evaluator/README.md` | Detailed guide |

## License

MIT
