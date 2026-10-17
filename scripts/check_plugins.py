#!/usr/bin/env python3
"""Static checks for the plugins in this repo (run by CI and locally).

Manifests are checked for every plugin; the stricter checks below cover the plugins listed in
STRICT_PLUGINS (add a plugin once its files pass). `claude plugin validate` in CI covers all.

- JSON manifests parse (marketplace + every plugin.json); plugin.json has name + version.
- Every SKILL.md and agent file has YAML frontmatter with the required keys and sane values.
- Every eval case (prompt.md + graders/*.md) has parseable frontmatter.
- Relative Markdown links and images resolve to files in the repo.

Usage: python3 scripts/check_plugins.py   (exit 1 on any error)
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STRICT_PLUGINS = ["squad"]
MODELS = {"sonnet", "opus", "haiku", "inherit"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
GRADER_TYPES = {"regex", "file_exists", "llm", "tool_used", "tool_order"}
errors = []


def err(path, msg):
    errors.append(f"{path.relative_to(ROOT)}: {msg}")


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        err(path, "missing YAML frontmatter")
        return None
    try:
        return yaml.safe_load(text.split("---\n", 2)[1]) or {}
    except yaml.YAMLError as e:
        err(path, f"invalid frontmatter: {e}")
        return None


def strict_glob(pattern):
    return [p for name in STRICT_PLUGINS for p in (ROOT / "plugins" / name).glob(pattern)]


def check_manifests():
    json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    for manifest in ROOT.glob("plugins/*/.claude-plugin/plugin.json"):
        data = json.loads(manifest.read_text())
        for key in ("name", "description"):
            if not data.get(key):
                err(manifest, f"missing '{key}'")
        if manifest.parent.parent.name in STRICT_PLUGINS and not data.get("version"):
            err(manifest, "missing 'version'")


def check_skills_and_agents():
    for skill in strict_glob("skills/*/SKILL.md"):
        fm = frontmatter(skill)
        if fm is None:
            continue
        for key in ("name", "description"):
            if not fm.get(key):
                err(skill, f"frontmatter missing '{key}'")
    for agent in strict_glob("agents/*.md"):
        fm = frontmatter(agent)
        if fm is None:
            continue
        for key in ("name", "description", "tools"):
            if not fm.get(key):
                err(agent, f"frontmatter missing '{key}'")
        if fm.get("name") and fm["name"] != agent.stem:
            err(agent, f"name '{fm['name']}' does not match file name")
        if "model" in fm and fm["model"] not in MODELS:
            err(agent, f"unknown model '{fm['model']}'")
        if "effort" in fm and fm["effort"] not in EFFORTS:
            err(agent, f"unknown effort '{fm['effort']}'")


def check_evals():
    for prompt in strict_glob("evals/*/prompt.md"):
        fm = frontmatter(prompt)
        if fm is not None and not isinstance(fm.get("allowed_tools", []), list):
            err(prompt, "allowed_tools must be a list")
        graders = list((prompt.parent / "graders").glob("*.md"))
        if not graders:
            err(prompt, "case has no graders")
        for grader in graders:
            gfm = frontmatter(grader)
            if gfm is not None and gfm.get("type") not in GRADER_TYPES:
                err(grader, f"unknown grader type '{gfm.get('type')}'")


LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")


def check_links():
    md_files = [ROOT / "README.md"] + strict_glob("**/*.md")
    for md in md_files:
        if not md.exists() or "results" in md.parts:
            continue
        text = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.S)
        for target in LINK.findall(text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#", 1)[0]
            if path and not (md.parent / path).exists():
                err(md, f"broken link: {target}")


def main():
    check_manifests()
    check_skills_and_agents()
    check_evals()
    check_links()
    if errors:
        print("\n".join(errors))
        print(f"\n{len(errors)} problem(s) found")
        return 1
    print("All plugin checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
