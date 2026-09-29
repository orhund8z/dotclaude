# Profile Setup Flow

Run this flow when `PROFILE.md` is missing, is still the untouched template, or the user asks to set up or
update their profile. Goal: end with a complete, specific `PROFILE.md` — not a vague one — in as few rounds as
possible.

## Where the profile is written

`~/.claude/job-evaluator/PROFILE.md` (create the directory if needed). This is outside the plugin directory so
plugin updates never overwrite it. Never write it inside the plugin install/cache directory, and never commit it.

## Rules

- **Existing profile:** read it first. Show a 3–4 line summary of what it currently says, then ask which sections
  to change. Never overwrite it wholesale — confirm before replacing any section, and keep a backup copy as
  `PROFILE.md.bak` next to it before writing.
- **Ask in rounds** using the `AskUserQuestion` tool (up to 4 questions per round, multiple-choice with sensible
  options; the user can always pick "Other" to type free text). Use plain prompts only for genuinely open answers
  (names, numbers, employer).
- **Prefill from context.** If the user's message, git config, CLAUDE.md, or a CV/LinkedIn URL/file they
  provide already answers something, don't ask it again — confirm it in the summary instead. If they give a CV
  or LinkedIn profile, read it to draft Identity, Career History, Education, Certifications, and Tech Stack, and
  only ask about what is missing.
- **Make expectations concrete.** Push vague answers toward something scoreable: a number for salary, a ranked
  list for priorities, named industries for preferences, hard yes/no for dealbreakers. If the user says "I don't
  know yet" for a field, write `Not decided` and move on — do not invent a value.
- **Never fabricate.** Only write what the user said or what a document they supplied states.

## Interview

### Round 1 — Who you are and what you want next
1. Current role/title and years of experience? (open)
2. Target roles, in priority order? (multi-select: e.g. Senior/Staff/Principal Engineer, Engineering Manager,
   SRE/Platform, Architect, Other)
3. Location and where you can work? (single-select: Remote only / Hybrid in my city / On-site OK / Open to
   relocation — then ask city/countries in the follow-up if needed)
4. What is the single main reason you're looking (or evaluating)? (single-select: growth/scope, compensation,
   domain/mission, stability, culture/happiness, leaving something behind)

### Round 2 — Priorities and money
1. Rank what matters most when comparing offers (pick top 3, in order): business domain, tech stack, employee
   happiness/culture, value of the work, compensation, career growth/title, work-life balance, stability.
   These become the CVI weights, so ask the user to order them.
2. Minimum base salary (annual, currency) that makes an offer acceptable? Is it a hard floor or a target?
3. Equity: required / preferred / nice to have / don't care? Bonus expectations?
4. Employment type and contract constraints (full-time only, contractor OK, notice period, visa/work-permit
   needs)?

### Round 3 — Tech and domain
1. Primary languages and frameworks? (multi-select from common ones + Other)
2. Cloud, infrastructure, data, observability, CI/CD tools you're strongest in? (open)
3. Which of these is your *core strength* — the thing a role must let you use, not just list? (open)
4. Domain expertise areas (e.g. distributed systems, payments, data/ML, security)? (open)

### Round 4 — Preferences, dealbreakers, constraints
1. Industries: preferred / open to / avoid? (three short lists)
2. On-call, travel, people management: acceptable or not? (single-select each)
3. Dealbreakers (hard no's): e.g. recent layoffs, no equity, on-site 5 days, specific industries. (open)
4. Life-stage or capacity constraints the evaluation must weigh (family, caregiving, health, side commitments)?
   Keep it optional and respect "prefer not to say". Record only what the user chooses to share.

### Round 5 — Background (optional, offer to skip)
Ask once whether they want to add career history, education, certifications, personal links, and languages
spoken. If they paste a CV/LinkedIn text or path, extract from it instead of asking field by field. Working
language requirement is asked here too.

## Writing the profile

1. Use `PROFILE.example.md` (same directory as this skill) as the structure. Keep all its section headings so the
   evaluator can rely on them: Identity, Career History, Education, Certifications, Target Roles, Priorities,
   Tech Stack, Domain Expertise, Work Preferences, Compensation Requirements, Industry Preferences, Language
   Requirements, Notes / Other Requirements.
2. Replace every placeholder with the user's answers. Delete sections the user skipped rather than leaving
   `[e.g. …]` placeholders (a leftover placeholder makes the evaluator treat the profile as untouched).
3. Put dealbreakers and life-stage constraints under **Notes / Other Requirements**, each as a labelled bullet
   (`Dealbreaker: …`, `Life-stage / capacity constraint: …`) — the evaluator reads them from there.
4. Show the user the finished profile (or a concise summary if long) and ask for a final "looks right / change
   something" confirmation before saving. Apply requested changes, then write the file.
5. Tell them the path it was saved to, that it is stored outside the plugin and never committed, and that they can
   update it any time with "update my profile".
6. If setup was triggered by an evaluation request, continue with that evaluation now.
