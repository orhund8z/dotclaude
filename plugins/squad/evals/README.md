# squad evals

Behavioural checks for the squad skill, run with [`claude plugin eval`](https://code.claude.com/docs):

```
claude plugin eval plugins/squad --allow-tools Write Edit --no-publish         # all cases, with/without-plugin arms
claude plugin eval plugins/squad --case '01-*' --runs 1 --ablation none        # one case, one run, no baseline
```

Case 02 needs `--allow-tools Write Edit` (the Architect writes the brief). Bash is deliberately not
in its `allowed_tools`: granting a shell needs the eval sandbox (bubblewrap + socat on Linux).
Last run (2.0.0, sonnet, 1 run each): 01 — 1.0 ($0.06), 02 — 1.0 ($0.18).

Each case starts a real squad run, so it spends tokens (case 02 runs the Architect). `runs` is set
to 1 per case to keep cost down; raise it with `--runs 3` before trusting a score change.

| Case | Checks |
|---|---|
| `01-kickoff-single-batch` | First turn is one question batch (clarifications + effort + model profile); no persona runs and no code is written before answers |
| `02-brief-gate-poc-roadmap` | With kickoff answers given, Shape runs one Architect call on the Balanced profile, writes `brief-v1.md` with a PoC-first roadmap, writes no code, and stops at the Brief gate |
