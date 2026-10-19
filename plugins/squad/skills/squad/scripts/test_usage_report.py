#!/usr/bin/env python3
"""Tests for usage_report.py — run: python3 scripts/test_usage_report.py"""
import unittest
from pathlib import Path

import usage_report as u

PRICING = Path(__file__).resolve().parent.parent / "references" / "pricing.md"

STATE = """# Squad STATE
- Request: x
- Started: 2026-10-19T10:00:00Z
- Phase: done

## Usage
| Stage | Persona | Model | Subagent tokens | Tool uses | Duration (ms) | Finished (UTC) |
|---|---|---|---|---|---|---|
| inc-0 | architect | sonnet | 10000 | 5 | 60000 | 2026-10-19T10:05:00Z |
| inc-0 | developer | sonnet | 20000 | 8 | 120000 | 2026-10-19T10:05:00Z |
| harden | reviewer | sonnet | 5000 | 3 | 30000 | 2026-10-19T11:15:05Z |
| harden | secops | opus | 5000 | 2 | 30000 | 2026-10-19T11:15:05Z |
"""


class UsageReport(unittest.TestCase):
    def setUp(self):
        self.out = u.build(STATE, PRICING)

    def test_total_elapsed_is_explicit(self):
        self.assertIn("**Total elapsed, all work (kickoff → done): 1h 15m 05s**", self.out)
        self.assertIn("| **Total — all work** |", self.out)

    def test_subagent_work_sums_durations(self):
        self.assertIn("**4m 00s**", self.out)  # 60+120+30+30 s

    def test_stage_rows_group_and_chain(self):
        self.assertIn("| inc-0 | 3m 00s | 5m 00s | 2026-10-19T10:05:00Z |", self.out)
        self.assertIn("| harden | 1m 00s | 1h 10m 05s | 2026-10-19T11:15:05Z |", self.out)

    def test_tokens_and_price(self):
        self.assertIn("**40,000**", self.out)
        self.assertIn("sonnet: 35,000 tokens — est. $0.10", self.out)  # 35k * 2.8 / 1e6
        self.assertIn("opus: 5,000 tokens — est. $0.03", self.out)     # 5k * 5.6 / 1e6

    def test_orchestrator_not_measured_is_stated(self):
        self.assertIn("not measured by the run", self.out)
        self.assertIn("`/cost`", self.out)

    def test_missing_started_is_a_labelled_lower_bound(self):
        out = u.build(STATE.replace("- Started: 2026-10-19T10:00:00Z\n", ""), PRICING)
        self.assertIn("lower bound", out)
        self.assertNotIn("kickoff → done", out)

    def test_no_rows(self):
        self.assertIn("No usage rows", u.build("# Squad STATE\n## Usage\n", PRICING))


if __name__ == "__main__":
    unittest.main()
