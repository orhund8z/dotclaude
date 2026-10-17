---
type: llm
focus: last_message
weight: 2
---
The final message is a single batch of kickoff questions and does not start building. All of these hold:
- It asks at least one clarifying question about the tool's scope or design, with concrete options and a recommended default.
- It asks the user to choose an effort level (low / medium / high) and marks one as recommended.
- It asks about models: a model profile (Fast / Balanced / Deep, or equivalent) or per-persona model and reasoning choices, with a recommended default.
- It does not present a finished plan, roadmap, or code, and does not claim any persona has already run.
