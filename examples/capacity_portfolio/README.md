# A complete, synthetic planning cycle

From the directory that contains `examples/`:

```sh
python3 examples/capacity_portfolio/run.py
python3 -m unittest discover -s examples/capacity_portfolio -p 'test_*.py'
```

To regenerate the two monochrome manuscript figures from the same calculated values, run `python3 examples/capacity_portfolio/figures.py`. Editable SVG sources are written to `manuscript/figures`; the book's publishing build renders them for EPUB and print. Figures use separate alternative outcomes, not estimated probabilities.

Python 3.9 or later, standard library only. No credentials, API calls, purchases, package installation, or production measurements. All inputs describe constructed teaching examples. This is inspectable example code, not a production capacity platform.

The first command writes `output/report.md`, `report.json`, `forecasts.csv`, `backtests.csv`, and `decisions.csv`. Use `--output /your/output/directory` to choose another destination. Paths are resolved relative to the script for fixture loading, so it can be invoked from any directory.

## Follow a decision through the files

1. **`fixtures/portfolio.json`** defines the planning boundary, work units, owners, constructed service rates, failure groups, delivery assumptions, effective-dated quoted prices, and the proposed decision. It also defines explicitly separate long-tail, AI, and index-rebuild examples. Database capacity remains an unresolved specialist dependency; no generic CPU metric fills it in.
2. **`fixtures/observations.csv`** holds 16 weeks of daily maximum one-minute mean offered request rates for the web service. `date` says when the measurement occurred; `available_on` says when a planner could have seen it. All dates are UTC. Historical fixture demand is assumed served without rejection or queue accumulation. Sub-minute bursts remain outside the data's resolution.
3. **`fixtures/events.json`** preserves versions of demand intelligence, timing, owners, scenario increments, and the amount already present in the baseline. Its July 8 revision cannot enter the June 28 forecast. Two records describing the same cause for the same workload and target are rejected, even if their IDs differ. Independent records with different causes still require the planner to judge dependencies; the code cannot discover semantic duplicates automatically.
4. **`model.py`** retains a seasonal-naive baseline and a four-week matching-weekday mean alternative. Rolling-origin comparisons use 1-, 7-, 8-, 14-, and 42-day horizons with at least four weeks of initial history. Eight days matches the launch decision's horizon; 42 days matches the initial supply estimate. These fixed models are compared on the synthetic data; no model is selected using the later launch outcome, and no calibrated prediction interval is claimed.
5. **`output/report.md`** connects the baseline and event scenarios to failure-aware supply, supply readiness, cost attribution, conditions for a decision, and a later review. Two alternative outcomes show intelligence helping and hurting. They are counterfactual alternatives, not a two-point empirical evaluation.

The history CSV is reproducible: for week `w` and weekday `d`, the value is `weekday_peak_rps[d] + weekly_offsets_rps[w]` from `portfolio.json`, beginning at `history.start`. It is deliberately transparent, not a realistic sample on which to claim forecasting accuracy. Missing matching weekdays are rejected rather than silently filled. To use real observations, establish treatment of late arrivals, missing intervals, rejected demand, changing request mix, and revisions first.

## The canonical arithmetic

At 250 completed requests/s per worker under a fixed tested request mix, p95 latency <= 200 ms, and errors <= 0.1%:

- 64 workers in four groups of 16 sustain 12,000 requests/s after losing one group.
- Eight already-paid batch workers, two per group, produce four groups of 18: `(72 - 18) × 250 = 13,500` requests/s after a group loss.
- Staged demand is `10,000 + 2,000 = 12,000`; full demand is `10,000 + 4,000 = 14,000`. The first fits the stated degraded capacity with 1,500 of margin; the second exceeds it by 500.
- Once a new independent 16-worker group is qualified and the borrowed workers returned, five groups of 16 provide `(80 - 16) × 250 = 16,000` degraded requests/s.

The measurements are fixture assumptions at all modeled configurations. There is no inference that real service capacity scales linearly or survives an entire region loss. Spare workers elsewhere, database bytes, and AI token allowances cannot be added to this pool's capacity.

Day 0 is June 28, 2026. The transfer starts on day 2, June 30. A 30-day agreement covers `[June 30, July 30)`, ending at the start of day 32. Expected new supply is day 42, August 9, leaving a ten-day gap. A delayed day-70 arrival leaves a 38-day gap. The supply table checks both readiness and the return date at the proposed peak, so a transfer that has expired is not shown as available. The report requires a new agreement or another operational choice rather than assuming borrowed workers last forever.

At the constructed $40/worker-day charge, a 30-day transfer changes service attribution by `$40 × 8 × 30 = $9,600`, with an equal reduction in batch attribution and no incremental enterprise cash cost from the transfer itself. Forty days through expected supply would attribute $12,800; 68 days through delayed supply would attribute $21,760. Batch delay is not free and is not assigned an invented monetary value. New supply quotes $640/day or $19,200/30 days; actual cash effects require commercial review.

## Tests and limits

Tests check evidence-time boundaries, missing observations, duplicate observations and event versions, overlapping causes, baseline overlap, incompatible units and pools, actual failure-group size, supply readiness, effective price dates, start-inclusive/end-exclusive transfer periods, allocation conservation, component reconciliation, and the AI arithmetic. They check that a later event revision cannot flatter an earlier forecast and that the unfavorable intelligence outcome remains in the report.

There is no adapter for Azure or another provider. There is no power-law fitting, automatic correlation estimate, annual/holiday seasonality model, GPU capacity conversion, automated rightsizing, or generalized database optimizer. The long-tail covariance calculation is a sensitivity example. The decision is a proposed choice with named roles and conditions, not automatic approval. The scripts reproduce arithmetic and retain uncertainty; they do not supply the relationships or operational evidence needed to act.

## Method references

- Hyndman and Athanasopoulos, *Forecasting: Principles and Practice*, [simple benchmark methods](https://otexts.com/fpp3/simple-methods.html), [rolling-origin evaluation](https://otexts.com/fpp3/tscv.html), and [judgmental adjustments](https://otexts.com/fpp3/judgmental-adjustments.html).
- The four-week matching-weekday average is this example's deliberately simple alternative. The code does not implement the book's broader statistical libraries or claim to improve on them.
