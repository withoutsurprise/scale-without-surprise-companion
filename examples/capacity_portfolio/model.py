"""Inspectable synthetic planning arithmetic; no service or provider integration.

Forecasts use dates AND evidence availability dates. Units and pool IDs must match
before addition. Money is calculated with Decimal and emitted as integer cents.
The code is intentionally small enough to review beside Chapters 4 and 14–16.
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
import csv
import math


METHODS = ("seasonal_naive", "weekday_mean_4")


def day(value):
    return date.fromisoformat(value)


def require_compatible(left, right):
    if (left["pool"], left["unit"]) != (right["pool"], right["unit"]):
        raise ValueError("Cannot combine different resource pools or units")


def read_observations(path):
    with open(path, newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    seen = set()
    for row in rows:
        key = row["workload"], row["date"]
        if key in seen:
            raise ValueError("Duplicate workload/date observation")
        seen.add(key)
        day(row["date"])
        day(row["available_on"])
        if row["available_on"] < row["date"]:
            raise ValueError("An observation cannot be available before it occurs")
        row["value"] = float(row["value"])
        if not math.isfinite(row["value"]) or row["value"] < 0:
            raise ValueError("Observed demand must be finite and nonnegative")
    return rows


def forecast(rows, as_of, target, method, workload="web-service"):
    """Forecast a future date from evidence available by as_of; no imputation."""
    if method not in METHODS:
        raise ValueError("Unknown forecasting method")
    if day(target) <= day(as_of):
        raise ValueError("Forecast target must follow its origin")
    history = sorted(
        (r for r in rows if r["workload"] == workload
         and r["date"] <= as_of and r["available_on"] <= as_of),
        key=lambda r: r["date"],
    )
    if not history:
        raise ValueError("No history available at forecast origin")
    for row in history:
        require_compatible(history[0], row)
    required = 1 if method == "seasonal_naive" else 4
    # Demand is a daily peak fixture with a seven-day calendar. The exact recent
    # matching weekdays are required, so a missing week is not silently skipped.
    latest = day(as_of) - timedelta(
        days=(day(as_of).weekday() - day(target).weekday()) % 7
    )
    wanted = [str(latest - timedelta(days=7 * k)) for k in range(required)]
    by_date = {r["date"]: r for r in history}
    if any(d not in by_date for d in wanted):
        raise ValueError("Missing matching-weekday evidence at forecast origin")
    evidence = [by_date[d] for d in wanted]
    return {
        "origin": as_of, "target": target, "horizon_days": (day(target) - day(as_of)).days,
        "workload": workload, "pool": history[0]["pool"], "unit": history[0]["unit"],
        "method": method, "estimate": sum(r["value"] for r in evidence) / required,
        "evidence_dates": wanted, "evidence_available_on": [r["available_on"] for r in evidence],
        "uncertainty": "point estimate only; no calibrated prediction interval",
    }


def rolling_backtest(rows, as_of, horizons=(1, 7, 8, 14, 42)):
    """Weekly origins, four initial weeks, matched methods and known outcomes.

    Outcome evidence is restricted to as_of; fitting at each origin is restricted
    separately. This evaluates fixed methods, not a tuned/held-out model contest.
    """
    available = [r for r in rows if r["workload"] == "web-service"
                 and r["date"] <= as_of and r["available_on"] <= as_of]
    if not available:
        raise ValueError("No backtest data")
    by_date = {r["date"]: r for r in available}
    origin = min(day(r["date"]) for r in available) + timedelta(days=27)
    records = []
    while origin < day(as_of):
        for horizon in horizons:
            target = str(origin + timedelta(days=horizon))
            if target not in by_date:
                continue
            for method in METHODS:
                prediction = forecast(rows, str(origin), target, method)
                require_compatible(prediction, by_date[target])
                actual = by_date[target]["value"]
                records.append({**prediction, "actual": actual,
                                "error_actual_minus_forecast": actual - prediction["estimate"]})
        origin += timedelta(days=7)
    groups = defaultdict(list)
    for record in records:
        groups[record["method"], record["horizon_days"]].append(record["error_actual_minus_forecast"])
    summaries = []
    for (method, horizon), errors in sorted(groups.items()):
        summaries.append({"method": method, "horizon_days": horizon, "count": len(errors),
                          "bias": sum(errors) / len(errors),
                          "mae": sum(abs(e) for e in errors) / len(errors),
                          "rmse": math.sqrt(sum(e * e for e in errors) / len(errors)),
                          "unit": "requests/s"})
    return records, summaries


def event_snapshot(events, as_of):
    """Select only the latest known revision; never rewrite the original view."""
    seen = set()
    selected = {}
    versions = defaultdict(list)
    for event in events:
        key = event["id"], event["revision"]
        if key in seen:
            raise ValueError("Duplicate event ID/revision")
        seen.add(key)
        if event["revision"] < 1 or not isinstance(event["revision"], int):
            raise ValueError("Event revision must be a positive integer")
        for field in ("known_at", "starts", "ends", "review_by", "valid_until"):
            day(event[field])
        if event["starts"] > event["ends"]:
            raise ValueError("Event ends before it starts")
        if event["known_at"] > event["valid_until"]:
            raise ValueError("Event evidence expired before it was known")
        versions[event["id"]].append(event)
        if event["known_at"] <= as_of:
            prior = selected.get(event["id"])
            if prior is None or event["revision"] > prior["revision"]:
                selected[event["id"]] = event
    for revisions in versions.values():
        ordered = sorted(revisions, key=lambda e: e["revision"])
        if any(a["known_at"] > b["known_at"] for a, b in zip(ordered, ordered[1:])):
            raise ValueError("Revisions must advance in evidence time")
    return list(selected.values())


def adjust_forecast(baseline, events, scenario):
    """Add net event increments, preventing duplicate cause accounting.

    A cause shared across several workloads may appear once per workload. Two
    concurrent records for that same cause/workload are ambiguous, not additive.
    An event on another pool is not a candidate for this baseline.
    """
    selected = event_snapshot(events, baseline["origin"])
    active = [e for e in selected if e["workload"] == baseline["workload"]
              and e["starts"] <= baseline["target"] <= e["ends"]]
    causes = set()
    applied = []
    for event in active:
        require_compatible(baseline, event)
        if event["valid_until"] < baseline["origin"]:
            raise ValueError("Expired demand intelligence requires review")
        if event["cause_id"] in causes:
            raise ValueError("Overlapping event records describe the same demand cause")
        causes.add(event["cause_id"])
        if scenario not in event["gross_increment"]:
            raise ValueError("Scenario missing from event")
        gross = float(event["gross_increment"][scenario])
        overlap = float(event["already_in_baseline"][scenario])
        if not all(math.isfinite(v) and v >= 0 for v in (gross, overlap)) or overlap > gross:
            raise ValueError("Baseline overlap must be between zero and gross increment")
        applied.append({"id": event["id"], "revision": event["revision"],
                        "gross_increment": gross, "already_in_baseline": overlap,
                        "net_increment": gross - overlap, "owner": event["owner"],
                        "review_by": event["review_by"],
                        "review_due_before_target": event["review_by"] < baseline["target"],
                        "evidence_known_at": event["known_at"]})
    return {**baseline, "scenario": scenario, "baseline": baseline["estimate"],
            "estimate": baseline["estimate"] + sum(e["net_increment"] for e in applied),
            "events": applied,
            "uncertainty": "constructed event scenario, not a probability-weighted forecast"}


def service_capacity(groups, rate, lost_groups=1):
    if not groups or any(not isinstance(g, int) or isinstance(g, bool) or g <= 0 for g in groups):
        raise ValueError("Each failure group needs a positive integer worker count")
    if not isinstance(lost_groups, int) or lost_groups < 0 or lost_groups > len(groups):
        raise ValueError("Invalid failure scope")
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("Service rate must be positive and finite")
    lost_workers = sum(sorted(groups, reverse=True)[:lost_groups])
    return {"groups": groups, "workers": sum(groups),
            "normal_rps": sum(groups) * rate,
            "lost_groups": lost_groups, "largest_loss_workers": lost_workers,
            "degraded_rps": (sum(groups) - lost_workers) * rate}


def worker_cost_cents(schedule, start, days, workers):
    """Effective-dated quoted charge, not a claim about realized cash savings."""
    if days < 0 or workers < 0 or not isinstance(days, int) or not isinstance(workers, int):
        raise ValueError("Cost needs nonnegative integer days and workers")
    prices = sorted(schedule, key=lambda p: p["effective_from"])
    if len({p["effective_from"] for p in prices}) != len(prices):
        raise ValueError("Ambiguous effective-dated price")
    total = Decimal("0")
    for offset in range(days):
        current = str(day(start) + timedelta(days=offset))
        candidates = [p for p in prices if p["effective_from"] <= current]
        if not candidates:
            raise ValueError("No applicable price for a billed day")
        rate = Decimal(candidates[-1]["usd_per_worker_day"])
        if not rate.is_finite() or rate < 0:
            raise ValueError("Price must be finite and nonnegative")
        total += rate * workers
    cents = total * 100
    if cents != cents.to_integral_value():
        raise ValueError("Fractional-cent total requires an explicit rounding policy")
    return int(cents)


def supply_cases(config, stage, full):
    web = config["web"]
    if len(web["groups"]) != len(web["transfer_per_group"]):
        raise ValueError("Transfer placement must name each existing group")
    transferred = sum(web["transfer_per_group"])
    if transferred > web["already_paid_batch_workers"]:
        raise ValueError("Transfer allocation exceeds existing batch supply")
    if any(not isinstance(x, int) or x < 0 for x in web["transfer_per_group"]):
        raise ValueError("Invalid transfer count")
    base = service_capacity(web["groups"], web["tested_requests_per_worker_second"])
    transfer = service_capacity([a + b for a, b in zip(web["groups"], web["transfer_per_group"])],
                                web["tested_requests_per_worker_second"])
    future = service_capacity(web["groups"] + [web["new_group_workers"]],
                              web["tested_requests_per_worker_second"])
    transfer_end = day(config["as_of"]) + timedelta(days=web["transfer_ready_days"] + web["transfer_days"])
    records = []
    for name, cap, demand, ready, status in (
        ("existing-stage", base, stage, 0, "current fixture supply"),
        ("existing-full", base, full, 0, "full rollout without a batch transfer"),
        ("transfer-stage", transfer, stage, web["transfer_ready_days"], "requires batch agreement and qualification"),
        ("transfer-full", transfer, full, web["transfer_ready_days"], "full-rollout test under the temporary configuration"),
        ("new-group-full", future, full, web["new_supply_ready_days"], "estimated arrival; return borrowed workers"),
        ("delayed-new-group-full", future, full, web["delayed_supply_ready_days"], "alternative estimated arrival; not usable before then"),
    ):
        ready_date = str(day(config["as_of"]) + timedelta(days=ready))
        expires = str(transfer_end) if name.startswith("transfer-") else None
        available_at_peak = ready_date <= config["peak_date"] and (
            expires is None or config["peak_date"] < expires
        )
        records.append({"choice": name, **cap, "demand_rps": demand,
                        "degraded_headroom_rps": cap["degraded_rps"] - demand,
                        "passes_stated_capacity_arithmetic": cap["degraded_rps"] >= demand,
                        "ready_date_assumption": ready_date,
                        "ready_by_launch_peak": ready_date <= config["peak_date"],
                        "available_until_exclusive": expires,
                        "available_at_launch_peak": available_at_peak, "status": status})
    schedule = web["price_schedule"]
    period = web["billing_period_days"]
    base_workers = sum(web["groups"])
    transfer_start = str(day(config["as_of"]) + timedelta(days=web["transfer_ready_days"]))
    transferred_cost = worker_cost_cents(schedule, transfer_start, web["transfer_days"], transferred)
    costs = {
        "currency": "USD", "all_amounts": "integer cents", "period_days": period,
        "existing_web_per_day": worker_cost_cents(schedule, config["as_of"], 1, base_workers),
        "existing_web_period": worker_cost_cents(schedule, config["as_of"], period, base_workers),
        "existing_web_plus_batch_period": worker_cost_cents(schedule, config["as_of"], period, base_workers + web["already_paid_batch_workers"]),
        "transfer_attribution_web_increase": transferred_cost,
        "transfer_attribution_batch_decrease": -transferred_cost,
        "transfer_enterprise_cash_increment": 0,
        "new_workers_daily_quote": worker_cost_cents(schedule, config["as_of"], 1, web["new_group_workers"]),
        "new_workers_period_quote": worker_cost_cents(schedule, config["as_of"], period, web["new_group_workers"]),
        "new_workers_realized_cash_effect": "unknown until commercial terms and obligations are checked",
        "batch_opportunity_cost": web["transfer_opportunity_cost"],
        "transfer_agreement_expires": str(transfer_end),
        "transfer_start_inclusive": transfer_start,
        "transfer_end_exclusive": str(transfer_end),
        "transfer_attribution_through_expected_supply": worker_cost_cents(
            schedule, transfer_start, max(0, web["new_supply_ready_days"] - web["transfer_ready_days"]), transferred),
        "transfer_attribution_through_delayed_supply": worker_cost_cents(
            schedule, transfer_start, max(0, web["delayed_supply_ready_days"] - web["transfer_ready_days"]), transferred),
        "gap_to_expected_supply_days": max(0, web["new_supply_ready_days"] - web["transfer_ready_days"] - web["transfer_days"]),
        "gap_to_delayed_supply_days": max(0, web["delayed_supply_ready_days"] - web["transfer_ready_days"] - web["transfer_days"]),
    }
    return records, costs


def tail_example(tail):
    head = tail["head_total"]
    n = tail["tail_projects"]
    remainder = n * tail["per_tail_project"]
    baseline = head + remainder
    increase = n * tail["common_increase_per_project"]
    head_change = head * tail["head_growth"]
    sigma = tail["error_sigma"]
    rho = tail["illustrative_pairwise_correlation"]
    return {"pool": "tail-shared-pool", "unit": "tested work units/interval",
            "head_projects": tail["head_projects"], "tail_projects": n,
            "common_increase_per_project": tail["common_increase_per_project"],
            "head_growth": tail["head_growth"], "illustrative_pairwise_correlation": rho,
            "baseline": baseline, "head": head, "tail": remainder,
            "head_share": head / baseline, "head_project_share": tail["head_projects"] / (tail["head_projects"] + n),
            "supply": tail["supply"], "baseline_headroom": tail["supply"] - baseline,
            "common_tail_increase": increase,
            "tail_only_headroom": tail["supply"] - baseline - increase,
            "combined_demand": baseline + increase + head_change,
            "combined_headroom": tail["supply"] - baseline - increase - head_change,
            "independent_error_sd": sigma * math.sqrt(n),
            "correlated_error_sd": sigma * math.sqrt(n * (1 + (n - 1) * rho)),
            "interpretation": "sensitivity arithmetic; not a fitted power law, estimated correlation, or probability interval"}


def ai_examples(ai, rebuild):
    calls = ai["attempted_tasks"] * ai["calls_per_task"]
    input_tokens = calls * ai["input_tokens_per_call"]
    output_tokens = calls * ai["output_tokens_per_call"]
    token_dollars = (Decimal(input_tokens) * Decimal(ai["usd_per_million_input"])
                     + Decimal(output_tokens) * Decimal(ai["usd_per_million_output"])) / 1000000
    full_dollars = token_dollars + Decimal(ai["model_access_subscription_usd"]) + Decimal(ai["supporting_cost_usd"])
    for dollars in (token_dollars, full_dollars):
        if not dollars.is_finite() or dollars < 0:
            raise ValueError("Cost must be finite and nonnegative")
        if dollars * 100 != (dollars * 100).to_integral_value():
            raise ValueError("Fractional-cent total requires an explicit rounding policy")
    required_rate = ai["busy_tasks_per_minute"] * ai["calls_per_task"] * ai["input_tokens_per_call"]
    if ai["accepted_tasks"] <= 0 or ai["accepted_tasks"] > ai["attempted_tasks"]:
        raise ValueError("Accepted task count must be positive and not exceed attempts")
    required_workers = math.ceil(rebuild["records"] / (rebuild["records_per_worker_minute"] * rebuild["compute_minutes"]))
    return {
        "token_ledger": {"pool": "external-model-api", "input_tokens": input_tokens,
                         "output_tokens": output_tokens, "token_cost_cents": int(token_dollars * 100),
                         "full_cost_cents": int(full_dollars * 100),
                         "cost_per_accepted_task_usd": str(full_dollars / ai["accepted_tasks"]),
                         "required_input_tokens_per_minute": required_rate,
                         "input_limit_per_minute": ai["input_token_limit_per_minute"],
                         "input_limit_gap_per_minute": ai["input_token_limit_per_minute"] - required_rate,
                         "price_status": "constructed rates; no provider prices or live calls"},
        "index_rebuild": {"pool": "qualified-index-workers", "required_workers": required_workers,
                          "records": rebuild["records"],
                          "records_per_worker_minute": rebuild["records_per_worker_minute"],
                          "available_workers": rebuild["available_qualified_workers"],
                          "records_completed_in_window": rebuild["available_qualified_workers"] * rebuild["records_per_worker_minute"] * rebuild["compute_minutes"],
                          "deadline_minutes": rebuild["deadline_minutes"],
                          "compute_minutes": rebuild["compute_minutes"],
                          "measurement_status": "constructed tested rate; concurrent serving and data supply must qualify separately"}
    }


def reconcile_components(components, expected, pool, unit):
    """Only add aligned, unique component records within an explicit boundary."""
    seen = set()
    total = 0.0
    intervals = set()
    for row in components:
        require_compatible(row, {"pool": pool, "unit": unit})
        if row["id"] in seen:
            raise ValueError("Duplicate component")
        seen.add(row["id"])
        intervals.add(row["interval"])
        total += row["value"]
    if len(intervals) > 1:
        raise ValueError("Components must share an aligned interval")
    if not math.isclose(total, expected, rel_tol=1e-10, abs_tol=1e-8):
        raise ValueError("Components do not reconcile to the declared total")
    return total


def make_report(config, events, rows):
    baseline = forecast(rows, config["as_of"], config["peak_date"], "seasonal_naive")
    alternatives = [forecast(rows, config["as_of"], config["peak_date"], m) for m in METHODS]
    stage = adjust_forecast(baseline, events, "stage")
    full = adjust_forecast(baseline, events, "full")
    cases, costs = supply_cases(config, stage["estimate"], full["estimate"])
    backtests, summaries = rolling_backtest(rows, config["as_of"])
    future = [forecast(rows, config["as_of"], str(day(config["as_of"]) + timedelta(days=h)), m)
              for h in range(1, 15) for m in METHODS]
    transfer_capacity = next(c["degraded_rps"] for c in cases if c["choice"] == "transfer-stage")
    outcomes = []
    for outcome in config["outcomes"]:
        actual = outcome["actual_peak_rps"]
        base_error = actual - baseline["estimate"]
        adjusted_error = actual - stage["estimate"]
        outcomes.append({**outcome, "baseline_forecast": baseline["estimate"],
                         "adjusted_forecast": stage["estimate"],
                         "baseline_error": base_error, "adjusted_error": adjusted_error,
                         "absolute_error_improvement": abs(base_error) - abs(adjusted_error),
                         "interpretation": "compare the two preserved forecast errors; service capacity and supply readiness are separate tests",
                         "degraded_headroom_rps": transfer_capacity - actual})
    return {"description": config["description"], "as_of": config["as_of"],
            "peak_date": config["peak_date"], "workloads": config["workloads"],
            "web_assumptions": config["web"],
            "observation_definition": config["history"], "baseline": baseline,
            "method_comparison": alternatives, "stage": stage, "full": full,
            "backtest_summary": summaries, "backtests": backtests, "forecasts": future,
            "supply_cases": cases, "costs": costs, "decision": config["decision"],
            "retrospective_alternative_outcomes": outcomes,
            "tail": tail_example(config["tail"]),
            "ai": ai_examples(config["ai"], config["index_rebuild"]),
            "residual_risks": config["web"]["residual_risks"],
            "limitations": ["Synthetic fixtures, not evidence about production behavior.",
                            "No calibrated probabilities or prediction intervals.",
                            "No inferred equivalence between resource pools.",
                            "No annual seasonality or calendar-holiday model from 16 weeks of history.",
                            "Only two fixed forecasting methods; no provider adapter or automated purchasing.",
                            "The displayed choice is a recommendation whose approvals and measurements remain conditions."]}
