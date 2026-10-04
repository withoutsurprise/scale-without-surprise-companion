#!/usr/bin/env python3
"""Run the book's synthetic portfolio without packages, credentials, or APIs."""

import argparse
import csv
import json
from pathlib import Path

from model import make_report, read_observations


ROOT = Path(__file__).resolve().parent


def usd(cents):
    return f"${cents / 100:,.2f}"


def number(value):
    return f"{value:,.0f}"


def markdown(report):
    baseline = report["baseline"]
    costs = report["costs"]
    web = report["web_assumptions"]
    original = next(c for c in report["supply_cases"] if c["choice"] == "existing-stage")
    transfer_workers = sum(web["transfer_per_group"])
    ordinary_bridge_days = max(0, web["new_supply_ready_days"] - web["transfer_ready_days"])
    delayed_bridge_days = max(0, web["delayed_supply_ready_days"] - web["transfer_ready_days"])
    lines = [
        "# Synthetic capacity and cost review", "",
        report["description"], "",
        f"**Forecast origin:** {report['as_of']}. **Peak date:** {report['peak_date']}. Dates are UTC calendar dates.", "",
        f"Day 0 is the forecast origin. The transfer starts on day {web['transfer_ready_days']}. Durations use a start-inclusive, end-exclusive interval; {web['transfer_days']} days therefore ends on day {web['transfer_ready_days'] + web['transfer_days']}.", "",
        "## The decision", "",
        report["decision"]["choice"], "",
        "**Status:** " + report["decision"]["status"] + ".", "",
        "The decision text is a declared proposal from the fixture, not an optimizer's recommendation. If you change inputs, recheck the supply table and revise that proposal; the code does not turn an infeasible choice into an approved action.", "",
        "The arithmetic does not authorize deployment, spending, a batch delay, or relaxed service promises. The named roles below must make those decisions.", "",
        "| Owner | Required action | Due |", "|---|---|---|",
    ]
    for item in report["decision"]["conditions"]:
        lines.append(f"| {item['owner']} | {item['action']} | {item['due']} |")
    lines += ["", "## What was known", "",
              f"The seasonal-naive baseline is **{number(baseline['estimate'])} requests/s**. Its evidence dates are {', '.join(baseline['evidence_dates'])}; only observations and event revisions available at the forecast origin enter that view.", "",
              f"Staged-rollout scenario: {number(report['stage']['baseline'])} + {number(report['stage']['estimate'] - report['stage']['baseline'])} = **{number(report['stage']['estimate'])} requests/s**.", "",
              f"Full-rollout scenario: {number(report['full']['baseline'])} + {number(report['full']['estimate'] - report['full']['baseline'])} = **{number(report['full']['estimate'])} requests/s**.", "",
              "These are conditional alternatives. They are not three quantities to add together and have no probability weights. The event requires review before the target date. Later evidence remains visible in the fixture but cannot improve the historical forecast retroactively.", "",
              "## Usable web capacity", "",
              f"{number(web['tested_requests_per_worker_second'])} completed requests/s per worker at the stated request mix, p95 latency <= 200 ms, and errors <= 0.1% is a constructed measurement assumption. Checks at all modeled configurations are assumed, not run. The failure scope is loss of one of the listed independent groups; it does not represent region failure.", "",
              "| Choice | Groups | Demand requests/s | After one group lost | Margin | Ready date assumption | Return date (exclusive) | Available at peak? |",
              "|---|---|---:|---:|---:|---|---|---|"]
    for case in report["supply_cases"]:
        groups = "+".join(str(g) for g in case["groups"])
        lines.append(f"| {case['choice']} | {groups} | {number(case['demand_rps'])} | {number(case['degraded_rps'])} | {number(case['degraded_headroom_rps'])} | {case['ready_date_assumption']} | {case['available_until_exclusive'] or '—'} | {'yes' if case['available_at_launch_peak'] else 'no'} |")
    lines += ["", "A nonnegative margin only passes the stated arithmetic constraint. Availability at the peak additionally requires that the ready date has arrived and any transfer agreement has not expired. Both are conditional assumptions; neither certifies workload behavior, approvals, or downstream dependencies. New supply still requires delivery and qualification.", "",
              "## Cost and attribution", "",
              f"Current {original['workers']}-worker service: **{usd(costs['existing_web_per_day'])}/day**, or **{usd(costs['existing_web_period'])} for {costs['period_days']} days**.", "",
              f"The {web['transfer_days']}-day, {transfer_workers}-worker transfer increases service attribution by **{usd(costs['transfer_attribution_web_increase'])}** and decreases batch attribution by the same amount. Incremental enterprise cash from moving already-paid workers: **{usd(costs['transfer_enterprise_cash_increment'])}**. Batch opportunity cost remains unpriced and requires an agreement.", "",
              f"New {web['new_group_workers']}-worker quote: **{usd(costs['new_workers_daily_quote'])}/day**, or **{usd(costs['new_workers_period_quote'])} per {costs['period_days']} days**. Realized cash effect requires the actual commercial obligations; no canceled commitment is assumed.", "",
              f"The transfer interval is [{costs['transfer_start_inclusive']}, {costs['transfer_end_exclusive']}). If the workers return on that date, the gap before expected new supply is **{costs['gap_to_expected_supply_days']} days**, or **{costs['gap_to_delayed_supply_days']} days** under the delayed alternative.", "",
              f"Bridging expected delivery would require {ordinary_bridge_days} transfer days and **{usd(costs['transfer_attribution_through_expected_supply'])}** attributed to the service. Bridging delayed delivery would require {delayed_bridge_days} transfer days and **{usd(costs['transfer_attribution_through_delayed_supply'])}**. Neither extension is approved by this report. Returning workers restores {number(original['degraded_rps'])} requests/s of degraded web capacity; the staged estimate then has {number(original['degraded_headroom_rps'])} requests/s of margin.", "",
              "## Forecast method comparison", "",
              "Weekly rolling origins, at least four initial weeks, fixed methods. Positive bias means underforecasting. All errors are requests/s. These synthetic results do not establish a production winner.", "",
              "| Method | Horizon days | Cases | Bias | MAE | RMSE |", "|---|---:|---:|---:|---:|---:|"]
    for row in report["backtest_summary"]:
        lines.append(f"| {row['method']} | {row['horizon_days']} | {row['count']} | {row['bias']:.2f} | {row['mae']:.2f} | {row['rmse']:.2f} |")
    lines += ["", "Seasonal naive repeats the latest matching weekday. The alternative averages the latest four matching weekdays. The baseline is retained as the book's declared benchmark, not selected retrospectively to flatter the launch outcome. No calibrated prediction interval is claimed.", "",
              "## Retrospective: intelligence helped and hurt", "",
              "The rows are alternative constructed outcomes, not two observations to pool into an accuracy claim. Error is actual minus forecast.", "",
              "| Alternative outcome | Actual | Baseline error | Adjusted error | Absolute error improvement | Margin under transfer configuration |",
              "|---|---:|---:|---:|---:|---:|"]
    for row in report["retrospective_alternative_outcomes"]:
        lines.append(f"| {row['id']} | {number(row['actual_peak_rps'])} | {number(row['baseline_error'])} | {number(row['adjusted_error'])} | {number(row['absolute_error_improvement'])} | {number(row['degraded_headroom_rps'])} |")
    tail = report["tail"]
    ai = report["ai"]["token_ledger"]
    rebuild = report["ai"]["index_rebuild"]
    lines += ["", "## Separate pools: do not add these to the web total", "",
              f"**Long tail illustration:** top {number(tail['head_projects'])} projects use {number(tail['head'])} units; {number(tail['tail_projects'])} other projects use {number(tail['tail'])}. Supply is {number(tail['supply'])}. A shared change of {tail['common_increase_per_project']:g} per small project adds {number(tail['common_tail_increase'])} units and leaves {number(tail['tail_only_headroom'])}; another {tail['head_growth']:.0%} growth in the head produces {number(tail['combined_demand'])} demand and a {number(tail['combined_headroom'])} margin. Illustrative aggregate error standard deviations are {tail['independent_error_sd']:.2f} with zero covariance and {tail['correlated_error_sd']:.2f} with pairwise correlation {tail['illustrative_pairwise_correlation']:g}. Neither is a probability guarantee.", "",
              f"**AI ledger:** {number(ai['input_tokens'])} input tokens and {number(ai['output_tokens'])} output tokens cost {usd(ai['token_cost_cents'])} at constructed prices. Model access subscriptions and supporting work bring the total to {usd(ai['full_cost_cents'])}, or ${ai['cost_per_accepted_task_usd']} per accepted task. The busy interval requires {number(ai['required_input_tokens_per_minute'])} input tokens/minute against an assumed {number(ai['input_limit_per_minute'])} limit. An affordable month does not make that interval feasible.", "",
              f"**Index rebuild:** {number(rebuild['records'])} records / ({number(rebuild['records_per_worker_minute'])} records per worker-minute × {rebuild['compute_minutes']} compute minutes), rounded up, requires {rebuild['required_workers']} qualified workers. The existing {rebuild['available_workers']} can process {number(rebuild['records_completed_in_window'])} records in that compute window at the assumed rate. These workers are not presumed interchangeable with the web pool.", "",
              "**Stateful data services:** unresolved service, maintenance, and recovery evidence remains an open planning dependency. The worker report cannot approve a database change.", "",
              "## Review triggers", ""]
    lines += ["- " + trigger for trigger in report["decision"]["review_triggers"]]
    lines += ["", "## Limits", ""]
    lines += ["- " + limit for limit in report["limitations"]]
    lines += ["", "The JSON retains assumptions, evidence dates, event revisions, alternatives, and retrospective errors. CSVs support inspection in a spreadsheet; they do not replace the conditions recorded here.", ""]
    return "\n".join(lines)


def write_csv(path, records, fields):
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({key: json.dumps(value) if isinstance(value, (list, dict)) else value
                             for key, value in record.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    fixture = ROOT / "fixtures"
    config = json.loads((fixture / "portfolio.json").read_text(encoding="utf-8"))
    events = json.loads((fixture / "events.json").read_text(encoding="utf-8"))
    rows = read_observations(fixture / "observations.csv")
    report = make_report(config, events, rows)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output / "report.md").write_text(markdown(report), encoding="utf-8")
    fields = ["origin", "target", "horizon_days", "workload", "pool", "unit", "method", "estimate", "evidence_dates", "evidence_available_on"]
    write_csv(args.output / "forecasts.csv", report["forecasts"], fields)
    write_csv(args.output / "backtests.csv", report["backtests"], fields + ["actual", "error_actual_minus_forecast"])
    write_csv(args.output / "decisions.csv", report["decision"]["conditions"], ["owner", "action", "due"])
    print(f"Wrote synthetic report and four data files to {args.output.resolve()}")
    transferred = next(c for c in report["supply_cases"] if c["choice"] == "transfer-stage")
    print(f"Staged peak: {number(report['stage']['estimate'])} requests/s; transfer capacity after one group loss: {number(transferred['degraded_rps'])}.")
    print("Delivery and approvals remain conditions. See report.md for the transfer-expiry gap and uncertainty.")


if __name__ == "__main__":
    main()
