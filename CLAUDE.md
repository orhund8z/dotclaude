# dotclaude — working rules

- **Every change to a published plugin gets a release-notes entry.** Add a bullet to the plugin's
  `CHANGELOG.md` under the next version: `- **What changed** — why (evidence or problem solved).`
  Bump `version` in its `.claude-plugin/plugin.json` when you start a new version section.
  The notes are the record of how the plugin evolved; a change without a "why" is incomplete.
- Larger design decisions also get a short entry in the plugin's `docs/DESIGN.md`.
- Before pushing plugin changes, run `python3 scripts/check_plugins.py` and
  `claude plugin validate plugins/<name>` (CI runs both).
