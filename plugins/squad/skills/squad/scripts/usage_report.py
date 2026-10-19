#!/usr/bin/env python3
"""Print the final report's Duration and Cost sections from docs/squad/STATE.md.

Usage:  python3 usage_report.py docs/squad/STATE.md >> docs/squad/final-report.md

Reads `Started:` and the `## Usage` table (rows end with a `Finished (UTC)` timestamp) and prices
from ../references/pricing.md. Standard library only. The sections are generated, not hand-written,
so the total elapsed time and the totals can't be left out or mis-added.
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def parse_ts(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def fmt(seconds):
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


def read_prices(pricing_md):
    prices, date = {}, "unknown date"
    if not pricing_md.exists():
        return prices, date
    text = pricing_md.read_text(encoding="utf-8")
    m = re.search(r"cached (\d{4}-\d{2}-\d{2})", text)
    if m:
        date = m.group(1)
    for model_id, p_in, p_out in re.findall(r"`(claude-[a-z0-9-]+)`\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)", text):
        prices[model_id] = (float(p_in), float(p_out))
    return prices, date


def price_for(model, prices):
    for model_id, pr in prices.items():
        if model == model_id or f"-{model}-" in model_id:
            return pr
    return None


def parse_state(text):
    started = None
    m = re.search(r"Started:\s*(" + TS.pattern + ")", text)
    if m:
        started = parse_ts(m.group(1))
    rows = []
    in_usage = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_usage = line.strip() == "## Usage"
            continue
        if not in_usage or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or cells[0] in ("Stage", "") or set(cells[0]) <= {"-"}:
            continue
        try:
            tokens, tools, dur_ms = (int(re.sub(r"[^\d]", "", cells[i]) or 0) for i in (3, 4, 5))
        except ValueError:
            continue
        finished = parse_ts(cells[6]) if len(cells) > 6 and TS.fullmatch(cells[6]) else None
        rows.append({"stage": cells[0], "persona": cells[1], "model": cells[2].lower(),
                     "tokens": tokens, "tools": tools, "dur": dur_ms / 1000, "finished": finished})
    return started, rows


def build(state_text, pricing_md):
    started, rows = parse_state(state_text)
    prices, price_date = read_prices(pricing_md)
    out = []
    if not rows:
        return "## Duration\nNo usage rows were recorded in `STATE.md`, so no time or cost can be reported.\n"

    stages = []
    for r in rows:
        if not stages or stages[-1]["stage"] != r["stage"]:
            stages.append({"stage": r["stage"], "dur": 0.0, "finished": None})
        stages[-1]["dur"] += r["dur"]
        if r["finished"] and (stages[-1]["finished"] is None or r["finished"] > stages[-1]["finished"]):
            stages[-1]["finished"] = r["finished"]

    finishes = [s["finished"] for s in stages if s["finished"]]
    last = max(finishes) if finishes else None
    work = sum(r["dur"] for r in rows)

    out += ["## Duration", ""]
    if started and last:
        total = (last - started).total_seconds()
        headline = f"**Total elapsed, all work (kickoff → done): {fmt(total)}**"
        basis = f"Started `{started:%Y-%m-%dT%H:%M:%SZ}`, finished `{last:%Y-%m-%dT%H:%M:%SZ}`."
    elif last and len(finishes) > 1:
        total = (last - min(finishes)).total_seconds()
        headline = f"**Total elapsed (first milestone → done): {fmt(total)}**"
        basis = "No `Started:` time was recorded, so this runs from the first milestone and is a lower bound."
    else:
        total = None
        headline = "**Total elapsed: not recorded**"
        basis = "Neither a `Started:` time nor enough finish times were recorded."
    out += [headline, "", basis, "",
            "| Stage | Subagent work | Elapsed since previous | Finished (UTC) |", "|---|---|---|---|"]
    prev = started
    for s in stages:
        if s["finished"] and prev:
            el = fmt((s["finished"] - prev).total_seconds())
        else:
            el = "—"
        if s["finished"]:
            prev = s["finished"]
        fin = f"{s['finished']:%Y-%m-%dT%H:%M:%SZ}" if s["finished"] else "—"
        out.append(f"| {s['stage']} | {fmt(s['dur'])} | {el} | {fin} |")
    tot_fin = f"{last:%Y-%m-%dT%H:%M:%SZ}" if last else "—"
    out.append(f"| **Total — all work** | **{fmt(work)}** | **{fmt(total) if total is not None else '—'}** | **{tot_fin}** |")
    out += ["", "- *Elapsed* includes the orchestrator's own time and any time spent waiting at a stop point or "
            "parked. *Subagent work* is the sum of the personas' own durations; parallel calls overlap, so the "
            "sum can exceed the elapsed time of a stage.", ""]

    out += ["## Cost", "", "Tokens from the run's own `<usage>` figures (subagents only):", "",
            "| Stage | Persona | Model | Subagent tokens | Tool uses |", "|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['stage']} | {r['persona']} | {r['model']} | {r['tokens']:,} | {r['tools']} |")
    out.append(f"| **Total** | | | **{sum(r['tokens'] for r in rows):,}** | **{sum(r['tools'] for r in rows)}** |")
    out.append("")
    est_total, priced_all = 0.0, True
    for model in sorted({r["model"] for r in rows}):
        tok = sum(r["tokens"] for r in rows if r["model"] == model)
        pr = price_for(model, prices)
        if pr:
            blended = 0.9 * pr[0] + 0.1 * pr[1]
            usd = tok * blended / 1e6
            est_total += usd
            out.append(f"- {model}: {tok:,} tokens — est. ${usd:.2f}")
        else:
            priced_all = False
            out.append(f"- {model}: {tok:,} tokens — no price on file")
    note = "" if priced_all else " (models without a price are excluded)"
    out += [f"- **Estimated subagent total: ${est_total:.2f}**{note} — rough (±50%): the harness gives one token "
            f"total per subagent, not an input/output split. Blend 0.9 × input + 0.1 × output price; "
            f"prices from `references/pricing.md` ({price_date}).",
            "- **Orchestrator (this session): not measured by the run.** For the exact total, run `/cost` in the "
            "Claude Code session and add the figure here.", ""]
    return "\n".join(out)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: usage_report.py <path to docs/squad/STATE.md>")
    state = Path(sys.argv[1])
    pricing = Path(__file__).resolve().parent.parent / "references" / "pricing.md"
    sys.stdout.write("\n" + build(state.read_text(encoding="utf-8"), pricing))


if __name__ == "__main__":
    main()
