"""Reproduce constructed examples in Chapters 1, 5 and 15; standard library only.

Run from the directory that contains examples/: python3 examples/portfolio_math.py
No cloud access, fitted distributions, or estimated failure probabilities.
"""

import json
import math


# Chapter 1's constructed thirty-day ledger, in dollars. Each work line carries
# its location split (Provider A, Provider B, private data center), its charge
# split (committed or fixed floor, usage-sensitive amount) and its funding source.
LEDGER_WORK = {
    "Data platforms": ((0, 90_000, 30_000), (72_000, 48_000), "Central engineering and IT"),
    "AI support assistant": ((0, 100_000, 0), (88_000, 12_000), "Support organization"),
    "Transaction-facing web workers": ((76_800, 0, 0), (38_400, 38_400), "Website product line"),
    "Shared platform hosting many small applications": ((0, 0, 60_000), (42_000, 18_000), "Central engineering and IT"),
    "Shared network, observation, and support": ((14_400, 18_000, 7_200), (9_900, 29_700), "Central engineering and IT"),
    "Legacy system being retired": ((24_000, 0, 0), (24_000, 0), "Modernization program"),
    "New system replacing it": ((18_000, 0, 0), (7_200, 10_800), "Modernization program"),
    "Deferrable batch workers": ((9_600, 0, 0), (0, 9_600), "Operations and finance reporting"),
}
# Team attribution splits two work lines: the AI assistant among three teams,
# and the shared network line between the network and observation teams.
LEDGER_TEAMS = {
    "Data platforms team": {"Data platforms": 120_000},
    "AI support assistant team": {"AI support assistant": 80_000},
    "Web service team": {"Transaction-facing web workers": 76_800},
    "Legacy system team": {"Legacy system being retired": 24_000},
    "Network team": {"Shared network, observation, and support": 21_600},
    "New system team": {"New system replacing it": 18_000},
    "Observation team": {"Shared network, observation, and support": 18_000},
    "Search and retrieval team": {"AI support assistant": 12_000},
    "Batch workers team": {"Deferrable batch workers": 9_600},
    "Evaluation and platform team": {"AI support assistant": 8_000},
    "All remaining attributed consumers": {"Shared platform hosting many small applications": 60_000},
}
WORKER_DAY_DOLLARS = 40
DAYS = 30


def ledger_views(work=LEDGER_WORK, teams=LEDGER_TEAMS):
    """Group one ledger five ways, refusing any view that does not reconcile."""
    totals = {}
    for line, (locations, charges, _) in work.items():
        if sum(charges) != sum(locations):
            raise ValueError(f"{line}: charge split {sum(charges)} != location split {sum(locations)}")
        totals[line] = sum(locations)
    attributed = {line: 0 for line in totals}
    for team, shares in teams.items():
        for line, amount in shares.items():
            if line not in attributed:
                raise ValueError(f"{team}: unknown work line {line!r}")
            attributed[line] += amount
    for line, amount in attributed.items():
        if amount != totals[line]:
            raise ValueError(f"{line}: teams attributed {amount}, ledger has {totals[line]}")
    funding = {}
    for line, (_, _, source) in work.items():
        funding[source] = funding.get(source, 0) + totals[line]
    views = {
        "work": totals,
        "team": {team: sum(shares.values()) for team, shares in teams.items()},
        "location": dict(zip(("Provider A", "Provider B", "Private data center"),
                             (sum(column) for column in zip(*(w[0] for w in work.values()))))),
        "charge": dict(zip(("Committed or fixed floor", "Usage-sensitive amount"),
                           (sum(column) for column in zip(*(w[1] for w in work.values()))))),
        "funding": funding,
    }
    view_totals = {name: sum(view.values()) for name, view in views.items()}
    if len(set(view_totals.values())) != 1:
        raise ValueError(f"views disagree: {view_totals}")
    return views


def ledger_summary():
    views = ledger_views()
    total = sum(views["work"].values())
    top_workloads = sum(sorted(views["work"].values(), reverse=True)[:3])
    top_teams = sum(sorted(views["team"].values(), reverse=True)[:3])
    transfer = 8 * WORKER_DAY_DOLLARS * DAYS
    return {
        "views": views,
        "total": total,
        "daily_rate": round(total / DAYS, 2),
        "annualized_at_constant_daily_rate": round(total / DAYS * 365, 2),
        "three_largest_workloads": top_workloads,
        "three_largest_workloads_share": top_workloads / total,
        "three_largest_teams_share": top_teams / total,
        "two_provider_share": (views["location"]["Provider A"] + views["location"]["Provider B"]) / total,
        "floor_share": views["charge"]["Committed or fixed floor"] / total,
        "usage_sensitive_share": views["charge"]["Usage-sensitive amount"] / total,
        "batch_transfer_30_days": {
            "web_service_team_after": views["team"]["Web service team"] + transfer,
            "batch_workers_team_after": views["team"]["Batch workers team"] - transfer,
            "enterprise_total_after": total,
        },
        "ten_times": {
            "thirty_day_total": total * 10,
            "annualized_at_constant_daily_rate": round(total * 10 / DAYS * 365, 2),
        },
    }


def search_mix(search_share, search_ms=22.0, other_ms=2.0):
    """Mean CPU milliseconds per request for a two-class request mix."""
    return (1 - search_share) * other_ms + search_share * search_ms


def search_mix_example():
    tested_rate = 250
    surviving_workers = 54  # four groups of 18 with the borrowed workers, one lost
    staged_demand = 12_000
    tested = search_mix(0.05)
    shifted = search_mix(0.07)
    qualified = tested_rate * tested / shifted
    return {
        "assumptions": "Constructed two-class mix; a CPU-limited worker; latency tail ignored.",
        "transfer_margin": surviving_workers * tested_rate / staged_demand - 1,
        "tested_mean_cpu_ms": round(tested, 6),
        "shifted_mean_cpu_ms": round(shifted, 6),
        "cpu_growth": shifted / tested - 1,
        "qualified_requests_per_worker_second": qualified,
        "degraded_capacity_after_group_loss": surviving_workers * qualified,
        "staged_demand": staged_demand,
    }


def examples():
    head = 800
    tail_count = 1000
    per_project = 0.2
    tail = tail_count * per_project
    supply = 1030
    tail_increase = tail_count * 0.02
    head_increase = head * 0.02
    sigma = 0.05
    rho = 0.05
    logical_reads = 10000
    return {
        "assumptions": "Constructed, single-pool examples; no probability coverage implied.",
        "ledger": ledger_summary(),
        "portfolio": {
            "head_project_count": 20,
            "tail_project_count": tail_count,
            "top_20_share": head / (head + tail),
            "baseline_demand": head + tail,
            "supply": supply,
            "baseline_headroom": supply - head - tail,
            "tail_increase": tail_increase,
            "tail_only_headroom": supply - head - tail - tail_increase,
            "combined_demand": head + head_increase + tail + tail_increase,
            "combined_headroom": supply - head - head_increase - tail - tail_increase,
            "head_efficiency_saving": head * 0.02,
            "net_demand_change_after_saving_and_tail_growth": tail_increase - head * 0.02,
        },
        "error_standard_deviation": {
            "uncorrelated": sigma * math.sqrt(tail_count),
            "pairwise_correlation_0_05": sigma * math.sqrt(
                tail_count * (1 + (tail_count - 1) * rho)
            ),
        },
        "cpu": {
            "demand_cores": 1000 * 0.02,
            "provisional_cores_at_60_percent": math.ceil(1000 * 0.02 / 0.60),
        },
        "cache": {
            "reads_per_second_at_99_percent_hits": round(logical_reads * (1 - 0.99)),
            "reads_per_second_at_95_percent_hits": round(logical_reads * (1 - 0.95)),
            "assumed_service_limit_reads_per_second": 300,
        },
        "search_mix": search_mix_example(),
        "risk_sensitivity": {
            "annual_saving": 2000 * 12,
            "assumed_loss_per_event": 400000,
            "break_even_added_annual_probability": 2000 * 12 / 400000,
        },
    }


if __name__ == "__main__":
    print(json.dumps(examples(), indent=2))
