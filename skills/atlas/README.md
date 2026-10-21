# atlas

A **personal** Claude Code skill (not published as a plugin) that answers questions about a child's
health, nutrition, sleep and development with a **five-role advisory-board protocol**, grounded in
the child's own profile. Replies are in **Turkish**; the guidance assumes Germany/Bavaria (Kinderarzt,
U-Untersuchungen, STIKO, 112 / 116117).

It is a structured pre-assessment to help parents talk to their doctor — **not** a diagnosis, a
prescription, or a substitute for an examination.

## What it does

For each question it:

1. **Red-flag gate first** — scans for emergency signs (fever in a baby under 3 months, breathing
   trouble, dehydration, non-blanching rash, seizure, green vomit, head injury, poisoning…). If one is
   present it skips the board and gives a short instruction with the right number (112 / 116117 /
   poison control).
2. **Reads the child's profile** — computes today's age (and corrected age for preterm births) and
   uses feeding stage and known findings. If critical information is missing it asks at most three
   questions instead of guessing.
3. **Convenes the board** — Chair (senior paediatrician), Developmental Paediatrician, Paediatric
   Nutritionist, an **Auditor** whose job is to challenge the answer (no silent approval), and an
   Experience Pool of "senior mothers" (clearly labelled anecdote, with safety warnings for risky
   folk practices).
4. **Answers in a fixed template** — question as understood, current status, the board's
   recommendation with a **confidence level** (high / medium / low — low produces a list of questions
   for the doctor instead of advice), rationale per member, alternatives, how to monitor, when to see a
   doctor, and what to clarify.

Evidence is ranked (AWMF/DGKJ, STIKO, ESPGHAN, WHO, Netzwerk Gesund ins Leben, then AAP/NHS), sources
are never invented, and "I'm not sure" is an accepted answer.

## Install

Personal skills live in `~/.claude/skills/`. From a clone of this repo:

```
ln -s "$PWD/skills/atlas" ~/.claude/skills/atlas     # or: cp -r skills/atlas ~/.claude/skills/
```

Restart Claude Code, then create the profile (below).

## Set up the child's profile

```
cp ~/.claude/skills/atlas/PROFILE.example.md ~/.claude/skills/atlas/profile.md
```

Fill in `profile.md` (name, date of birth, birth details, measurements with date, feeding, allergies,
health notes). Mark uncertain values `[doğrulanmalı]` (needs verification) — the board will not build
conclusions on them. Unknown fields stay `bilinmiyor`. The skill may *suggest* profile updates (new
weight, new diagnosis, starting solids) but never edits the file without your approval.

`profile.md` contains health data and is git-ignored — never commit or share it.

## Use it

It triggers on its own for child-health wording — no slash command needed:

```
Kızım ne kadar uyumalı?
Ek gıdaya nasıl başlayalım, ilk hangi besin?
3 gündür hafif ateşi var, bu normal mi?
```

(Or invoke explicitly with `/atlas`.)

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Protocol: red-flag gate, profile rules, board roles, evidence, template, hard limits |
| `PROFILE.example.md` | Profile template — copy to `profile.md` |
| `profile.md` | Your child's data (git-ignored, not in the repo) |

## Hard limits

No diagnosis, no medication doses, no deciding on vaccines/screenings/prescriptions — those stay with
the Kinderarzt. In an emergency, call **112**.
