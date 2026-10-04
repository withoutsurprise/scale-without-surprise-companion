"""Meaningful checks of temporal, physical, and financial boundaries."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from model import (
    adjust_forecast, ai_examples, event_snapshot, forecast, make_report,
    read_observations, reconcile_components, rolling_backtest,
    service_capacity, supply_cases, worker_cost_cents,
)
from run import markdown


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((FIXTURES / "portfolio.json").read_text())
        self.events = json.loads((FIXTURES / "events.json").read_text())
        self.rows = read_observations(FIXTURES / "observations.csv")
        self.baseline = forecast(self.rows, "2026-06-28", "2026-07-06", "seasonal_naive")

    def test_canonical_baseline_and_separate_event_scenarios(self):
        self.assertEqual(self.baseline["estimate"], 10000)
        self.assertEqual(adjust_forecast(self.baseline, self.events, "stage")["estimate"], 12000)
        self.assertEqual(adjust_forecast(self.baseline, self.events, "full")["estimate"], 14000)
        self.assertEqual(self.baseline["estimate"], 10000)  # never overwritten

    def test_future_observations_cannot_change_a_historical_forecast(self):
        added = dict(self.rows[-1], date="2026-07-06", available_on="2026-07-06", value=999999)
        got = forecast(self.rows + [added], "2026-06-28", "2026-07-06", "seasonal_naive")
        self.assertEqual(got, self.baseline)

    def test_late_arriving_historical_data_is_not_available_early(self):
        changed = copy.deepcopy(self.rows)
        next(r for r in changed if r["date"] == "2026-06-22")["available_on"] = "2026-06-29"
        with self.assertRaisesRegex(ValueError, "Missing"):
            forecast(changed, "2026-06-28", "2026-07-06", "seasonal_naive")

    def test_missing_week_is_not_silently_imputed_from_older_week(self):
        changed = [r for r in self.rows if r["date"] != "2026-06-15"]
        with self.assertRaisesRegex(ValueError, "Missing"):
            forecast(changed, "2026-06-28", "2026-07-06", "weekday_mean_4")

    def test_backtests_train_only_on_evidence_available_at_each_origin(self):
        records, summary = rolling_backtest(self.rows, "2026-06-28")
        self.assertTrue(records and summary)
        self.assertEqual({r["horizon_days"] for r in records}, {1, 7, 8, 14, 42})
        for row in records:
            self.assertLess(row["origin"], row["target"])
            self.assertTrue(all(d <= row["origin"] for d in row["evidence_dates"]))
            self.assertTrue(all(d <= row["origin"] for d in row["evidence_available_on"]))
            self.assertLessEqual(row["target"], "2026-06-28")
            self.assertEqual(row["error_actual_minus_forecast"], row["actual"] - row["estimate"])

    def test_backtest_before_late_data_arrives_does_not_score_it(self):
        changed = copy.deepcopy(self.rows)
        next(r for r in changed if r["date"] == "2026-06-28")["available_on"] = "2026-07-01"
        records, _ = rolling_backtest(changed, "2026-06-28")
        self.assertNotIn("2026-06-28", [r["target"] for r in records])

    def test_backtest_cannot_score_an_outcome_in_a_different_unit_or_pool(self):
        for field, value in (("unit", "requests/minute"), ("pool", "replacement-pool")):
            changed = copy.deepcopy(self.rows)
            changed[-1][field] = value
            with self.assertRaisesRegex(ValueError, "different resource"):
                rolling_backtest(changed, "2026-06-28", horizons=(7,))

    def test_event_revision_is_selected_as_of_evidence_date(self):
        self.assertEqual(event_snapshot(self.events, "2026-06-28")[0]["revision"], 1)
        self.assertEqual(event_snapshot(self.events, "2026-07-08")[0]["revision"], 2)
        future = copy.deepcopy(self.events)
        future[1]["gross_increment"]["stage"] = 999999
        self.assertEqual(adjust_forecast(self.baseline, future, "stage")["estimate"], 12000)

    def test_duplicate_event_revision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            event_snapshot(self.events + [self.events[0]], "2026-06-28")

    def test_same_cause_under_different_event_ids_cannot_be_counted_twice(self):
        duplicate = copy.deepcopy(self.events[0])
        duplicate["id"] = "E-SALES-RETELLING"
        with self.assertRaisesRegex(ValueError, "same demand cause"):
            adjust_forecast(self.baseline, self.events + [duplicate], "stage")

    def test_known_baseline_overlap_is_subtracted(self):
        events = copy.deepcopy(self.events)
        events[0]["already_in_baseline"]["stage"] = 500
        result = adjust_forecast(self.baseline, events, "stage")
        self.assertEqual(result["estimate"], 11500)
        self.assertEqual(result["events"][0]["net_increment"], 1500)

    def test_incompatible_units_or_pools_cannot_be_added(self):
        for field, value in (("unit", "tokens/minute"), ("pool", "accelerators")):
            events = copy.deepcopy(self.events)
            events[0][field] = value
            with self.assertRaisesRegex(ValueError, "different resource"):
                adjust_forecast(self.baseline, events, "stage")

    def test_expired_intelligence_cannot_be_silently_applied(self):
        events = copy.deepcopy(self.events)
        events[0]["valid_until"] = "2026-06-26"
        with self.assertRaisesRegex(ValueError, "Expired"):
            adjust_forecast(self.baseline, events, "stage")

    def test_group_failure_uses_actual_largest_group_after_transfer(self):
        self.assertEqual(service_capacity([16] * 4, 250)["degraded_rps"], 12000)
        self.assertEqual(service_capacity([18] * 4, 250)["degraded_rps"], 13500)
        self.assertEqual(service_capacity([16] * 5, 250)["degraded_rps"], 16000)
        self.assertEqual(service_capacity([20, 12, 16, 16], 250)["degraded_rps"], 11000)
        self.assertEqual(service_capacity([18] * 4, 250, lost_groups=2)["degraded_rps"], 9000)

    def test_future_supply_does_not_make_near_launch_feasible(self):
        cases, _ = supply_cases(self.config, 12000, 14000)
        future = next(r for r in cases if r["choice"] == "new-group-full")
        self.assertFalse(future["ready_by_launch_peak"])
        self.assertEqual(future["degraded_headroom_rps"], 2000)
        self.assertEqual(next(r for r in cases if r["choice"] == "transfer-full")["degraded_headroom_rps"], -500)
        self.assertEqual(next(r for r in cases if r["choice"] == "existing-full")["degraded_headroom_rps"], -2000)

    def test_peak_must_fall_inside_transfer_agreement(self):
        for peak, available in (("2026-06-29", False), ("2026-06-30", True),
                                ("2026-07-29", True), ("2026-07-30", False)):
            with self.subTest(peak=peak):
                self.config["peak_date"] = peak
                cases, _ = supply_cases(self.config, 12000, 14000)
                for case in cases:
                    if case["choice"].startswith("transfer-"):
                        self.assertEqual(case["available_at_launch_peak"], available)
                        self.assertEqual(case["available_until_exclusive"], "2026-07-30")

    def test_supply_ready_before_transfer_needs_no_bridge(self):
        self.config["web"]["new_supply_ready_days"] = 1
        _, costs = supply_cases(self.config, 12000, 14000)
        self.assertEqual(costs["transfer_attribution_through_expected_supply"], 0)
        self.assertEqual(costs["gap_to_expected_supply_days"], 0)

    def test_removing_transfer_preserves_existing_batch_inventory_and_cost(self):
        self.config["web"]["transfer_per_group"] = [0, 0, 0, 0]
        cases, costs = supply_cases(self.config, 12000, 14000)
        self.assertEqual(next(r for r in cases if r["choice"] == "transfer-stage")["degraded_rps"], 12000)
        self.assertEqual(costs["transfer_attribution_web_increase"], 0)
        self.assertEqual(costs["existing_web_plus_batch_period"], 8640000)

    def test_rendered_report_tracks_a_changed_rate_and_delivery_date(self):
        self.config["web"]["tested_requests_per_worker_second"] = 200
        self.config["web"]["new_supply_ready_days"] = 49
        result = make_report(self.config, self.events, self.rows)
        rendered = markdown(result)
        self.assertIn("200 completed requests/s", rendered)
        self.assertIn("47 transfer days", rendered)
        self.assertIn("9,600 requests/s of degraded web capacity", rendered)

    def test_rendered_report_uses_changed_tail_and_rebuild_inputs(self):
        self.config["tail"].update(head_projects=10, head_total=700, tail_projects=500,
                                   supply=900, common_increase_per_project=0.04,
                                   head_growth=0.01, illustrative_pairwise_correlation=0.02)
        self.config["index_rebuild"].update(records=8_000_000, records_per_worker_minute=10_000,
                                            compute_minutes=10)
        rendered = markdown(make_report(self.config, self.events, self.rows))
        self.assertIn("top 10 projects use 700 units; 500 other projects use 100", rendered)
        self.assertIn("Supply is 900", rendered)
        self.assertIn("correlation 0.02", rendered)
        self.assertIn("8,000,000 records / (10,000 records per worker-minute × 10 compute minutes)", rendered)
        self.assertIn("requires 80 qualified workers", rendered)

    def test_transfer_attribution_reconciles_without_enterprise_cash_change(self):
        _, costs = supply_cases(self.config, 12000, 14000)
        self.assertEqual(costs["transfer_attribution_web_increase"], 960000)
        self.assertEqual(costs["transfer_attribution_web_increase"] + costs["transfer_attribution_batch_decrease"], 0)
        self.assertEqual(costs["transfer_enterprise_cash_increment"], 0)
        self.assertEqual(costs["new_workers_period_quote"], 1920000)

    def test_transfer_intervals_are_start_inclusive_end_exclusive(self):
        _, costs = supply_cases(self.config, 12000, 14000)
        self.assertEqual(costs["transfer_start_inclusive"], "2026-06-30")
        self.assertEqual(costs["transfer_end_exclusive"], "2026-07-30")
        self.assertEqual(costs["gap_to_expected_supply_days"], 10)
        self.assertEqual(costs["gap_to_delayed_supply_days"], 38)
        self.assertEqual(costs["transfer_attribution_through_expected_supply"], 1280000)
        self.assertEqual(costs["transfer_attribution_through_delayed_supply"], 2176000)

    def test_effective_price_boundary_bills_each_day_once(self):
        prices = [{"effective_from": "2026-06-01", "usd_per_worker_day": "40.00"},
                  {"effective_from": "2026-07-01", "usd_per_worker_day": "50.00"}]
        self.assertEqual(worker_cost_cents(prices, "2026-06-30", 2, 8), 72000)
        self.assertEqual(worker_cost_cents(prices, "2026-07-01", 0, 8), 0)
        with self.assertRaisesRegex(ValueError, "No applicable"):
            worker_cost_cents(prices, "2026-05-31", 2, 8)

    def test_components_reconcile_only_when_aligned_unique_and_compatible(self):
        components = [{"id": "head", "pool": "tail", "unit": "units/interval", "interval": "peak", "value": 800},
                      {"id": "tail", "pool": "tail", "unit": "units/interval", "interval": "peak", "value": 200}]
        self.assertEqual(reconcile_components(components, 1000, "tail", "units/interval"), 1000)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            reconcile_components(components + [components[1]], 1200, "tail", "units/interval")
        with self.assertRaisesRegex(ValueError, "reconcile"):
            reconcile_components(components, 999, "tail", "units/interval")
        components[1]["interval"] = "other-peak"
        with self.assertRaisesRegex(ValueError, "aligned"):
            reconcile_components(components, 1000, "tail", "units/interval")

    def test_ai_affordability_and_rate_are_separate_from_worker_capacity(self):
        result = ai_examples(self.config["ai"], self.config["index_rebuild"])
        self.assertEqual(result["token_ledger"]["token_cost_cents"], 1200000)
        self.assertEqual(result["token_ledger"]["full_cost_cents"], 10000000)
        self.assertEqual(result["token_ledger"]["cost_per_accepted_task_usd"], "1.25")
        self.assertEqual(result["token_ledger"]["input_limit_gap_per_minute"], -600000)
        self.assertEqual(result["index_rebuild"]["required_workers"], 30)
        self.assertEqual(result["index_rebuild"]["records_completed_in_window"], 6400000)

    def test_ai_cost_does_not_silently_discard_fractional_cents(self):
        self.config["ai"]["usd_per_million_input"] = "3.000001"
        with self.assertRaisesRegex(ValueError, "Fractional-cent"):
            ai_examples(self.config["ai"], self.config["index_rebuild"])

    def test_retrospective_does_not_hide_when_intelligence_hurts(self):
        result = make_report(self.config, self.events, self.rows)
        helped, hurt = result["retrospective_alternative_outcomes"]
        self.assertEqual((helped["baseline_error"], helped["adjusted_error"]), (2800, 800))
        self.assertEqual(helped["degraded_headroom_rps"], 700)
        self.assertEqual((hurt["baseline_error"], hurt["adjusted_error"]), (200, -1800))
        self.assertEqual(hurt["absolute_error_improvement"], -1600)
        rendered = markdown(result)
        self.assertIn("not an approval", rendered)
        self.assertIn("gap before expected new supply is 10 days", rendered.replace("**", ""))

    def test_duplicate_observation_cannot_silently_replace_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            original = (FIXTURES / "observations.csv").read_text()
            path.write_text(original + original.splitlines()[1] + "\n")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                read_observations(path)


if __name__ == "__main__":
    unittest.main()
