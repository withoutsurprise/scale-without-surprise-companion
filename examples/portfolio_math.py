"""Reproduce constructed examples in Chapters 5 and 15; standard library only.

Run from the directory that contains examples/: python3 examples/portfolio_math.py
No cloud access, fitted distributions, or estimated failure probabilities.
"""

import json
import math


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
        "risk_sensitivity": {
            "annual_saving": 2000 * 12,
            "assumed_loss_per_event": 400000,
            "break_even_added_annual_probability": 2000 * 12 / 400000,
        },
    }


if __name__ == "__main__":
    print(json.dumps(examples(), indent=2))
