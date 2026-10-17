---
type: llm
focus: last_message
weight: 2
---
The final message is a single batch of kickoff questions and does not start building. All of these hold:
- It covers scope/design clarifications: either asks at least one clarifying question with concrete options, or states its scope/design assumptions explicitly and invites the user to change them.
- It asks the user to choose an effort level (low / medium / high) and marks one as recommended.
- It asks about models: a model profile (Fast / Balanced / Deep, or equivalent) or per-persona model and reasoning choices, with a recommended default.
- It asks where (if anywhere) the run should stop and wait — stop points such as after the brief, after the PoC, after each increment, or before Harden — and says that by default it runs straight through.
- It does not present a finished plan, roadmap, or code, and does not claim any persona has already run.
