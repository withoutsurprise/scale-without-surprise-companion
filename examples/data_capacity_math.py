"""Constructed Chapter 12 arithmetic; no production sizing or live-system access."""
import json

MIB_PER_TIB = 1024 * 1024
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR


def catch_up_hours(backlog_tib, arrival_mib_s, processing_mib_s):
    """Constant rates in the same input-byte units; None means no catch-up."""
    if backlog_tib < 0 or arrival_mib_s < 0 or processing_mib_s < 0:
        raise ValueError("Backlog and rates must be nonnegative")
    if backlog_tib == 0:
        return 0.0
    net_rate = processing_mib_s - arrival_mib_s
    if net_rate <= 0:
        return None
    return backlog_tib * MIB_PER_TIB / net_rate / SECONDS_PER_HOUR


def scenarios():
    return {
        "scope": "Synthetic constant-rate examples; excludes operational overheads",
        "cassandra": {
            "replicated_baseline_tib": 24 * 3,
            "two_month_growth_tib": 2 * 2 * 3,
            "baseline_plus_growth_tib": (24 + 2 * 2) * 3,
            "transfer_only_hours": 12 * MIB_PER_TIB / 200 / SECONDS_PER_HOUR,
            "four_hour_transfer_required_mib_s": 12 * MIB_PER_TIB / (4 * SECONDS_PER_HOUR),
        },
        "kafka": {
            "seven_day_log_tib": 10 * (7 * SECONDS_PER_DAY) * 3 / MIB_PER_TIB,
            "fourteen_day_log_tib": 10 * (14 * SECONDS_PER_DAY) * 3 / MIB_PER_TIB,
            "catch_up_hours": catch_up_hours(2, 20, 60),
            "at_arrival_rate_catch_up_hours": catch_up_hours(2, 20, 20),
        },
        "postgresql": {
            "six_hour_retained_wal_mib": 40 * 6 * SECONDS_PER_HOUR,
            "six_hour_retained_wal_gib": 40 * 6 * SECONDS_PER_HOUR / 1024,
        },
    }


if __name__ == "__main__":
    print(json.dumps(scenarios(), indent=2))
