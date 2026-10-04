"""Checks that the standalone arithmetic reproduces the book's constructed figures."""

import copy
import importlib.util
from pathlib import Path
import unittest

_spec = importlib.util.spec_from_file_location(
    "portfolio_math", Path(__file__).resolve().parents[1] / "portfolio_math.py")
portfolio_math = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(portfolio_math)


class LedgerTests(unittest.TestCase):
    def test_five_views_reconcile_to_one_total(self):
        views = portfolio_math.ledger_views()
        for name, view in views.items():
            self.assertEqual(sum(view.values()), 448_000, name)
        self.assertEqual(views["location"], {
            "Provider A": 142_800, "Provider B": 208_000, "Private data center": 97_200})
        self.assertEqual(views["charge"], {
            "Committed or fixed floor": 281_500, "Usage-sensitive amount": 166_500})
        self.assertEqual(views["funding"]["Central engineering and IT"], 219_600)

    def test_shares_and_scaled_figures_match_the_chapter(self):
        summary = portfolio_math.ledger_summary()
        self.assertEqual(summary["three_largest_workloads"], 296_800)
        self.assertAlmostEqual(summary["three_largest_teams_share"], 0.62, places=2)
        self.assertAlmostEqual(summary["two_provider_share"], 0.78, places=2)
        self.assertAlmostEqual(summary["floor_share"], 0.63, places=2)
        self.assertAlmostEqual(summary["annualized_at_constant_daily_rate"] / 1e6, 5.45, places=2)
        self.assertAlmostEqual(summary["ten_times"]["annualized_at_constant_daily_rate"] / 1e6, 54.5, places=1)

    def test_charge_split_that_does_not_match_its_line_is_rejected(self):
        work = copy.deepcopy(portfolio_math.LEDGER_WORK)
        locations, _, source = work["Shared platform hosting many small applications"]
        work["Shared platform hosting many small applications"] = (locations, (42_000, 17_000), source)
        with self.assertRaisesRegex(ValueError, "Shared platform"):
            portfolio_math.ledger_views(work=work)

    def test_every_work_line_must_be_fully_attributed(self):
        teams = copy.deepcopy(portfolio_math.LEDGER_TEAMS)
        del teams["Observation team"]
        with self.assertRaisesRegex(ValueError, "Shared network"):
            portfolio_math.ledger_views(teams=teams)

    def test_batch_transfer_moves_attribution_not_the_enterprise_total(self):
        transfer = portfolio_math.ledger_summary()["batch_transfer_30_days"]
        self.assertEqual(transfer["web_service_team_after"], 76_800 + 9_600)
        self.assertEqual(transfer["batch_workers_team_after"], 0)
        self.assertEqual(transfer["enterprise_total_after"], 448_000)


class SearchMixTests(unittest.TestCase):
    def test_shift_to_seven_percent_searches_exhausts_the_transfer_margin(self):
        mix = portfolio_math.search_mix_example()
        self.assertAlmostEqual(mix["transfer_margin"], 0.125)
        self.assertAlmostEqual(mix["tested_mean_cpu_ms"], 3.0)
        self.assertAlmostEqual(mix["shifted_mean_cpu_ms"], 3.4)
        self.assertGreater(mix["cpu_growth"], mix["transfer_margin"])
        self.assertEqual(round(mix["qualified_requests_per_worker_second"]), 221)
        self.assertEqual(round(mix["degraded_capacity_after_group_loss"], -2), 11_900)
        self.assertLess(mix["degraded_capacity_after_group_loss"], mix["staged_demand"])


if __name__ == "__main__":
    unittest.main()
