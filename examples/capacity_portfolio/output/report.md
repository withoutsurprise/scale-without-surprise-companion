# Synthetic capacity and cost review

Constructed teaching inputs, not an employer portfolio, forecast, or product benchmark.

**Forecast origin:** 2026-06-28. **Peak date:** 2026-07-06. Dates are UTC calendar dates.

Day 0 is the forecast origin. The transfer starts on day 2. Durations use a start-inclusive, end-exclusive interval; 30 days therefore ends on day 32.

## The decision

Stage launch after the transfer is qualified; pursue a new independent group; preserve a delayed-supply alternative.

**Status:** constructed recommended decision, not an approval.

The decision text is a declared proposal from the fixture, not an optimizer's recommendation. If you change inputs, recheck the supply table and revise that proposal; the code does not turn an infeasible choice into an approved action.

The arithmetic does not authorize deployment, spending, a batch delay, or relaxed service promises. The named roles below must make those decisions.

| Owner | Required action | Due |
|---|---|---|
| Product lead | Stage the rollout at the assumed 2000 additional requests/s and keep the ability to stop expansion. | before rollout |
| Batch product owner | Approve a bounded deferral and catch-up plan before transferring eight workers. | before transfer |
| Web operations lead | Qualify transferred capacity and failure behavior before treating it as available. | before rollout |
| Budget owner | Authorize the additional 640 dollars/day contingent on supply and actual commercial terms. | before purchase commitment |
| Responsible business executive | Accept residual exposure or change launch scope/deadline; resolve disagreement about obligations. | before rollout |

## What was known

The seasonal-naive baseline is **10,000 requests/s**. Its evidence dates are 2026-06-22; only observations and event revisions available at the forecast origin enter that view.

Staged-rollout scenario: 10,000 + 2,000 = **12,000 requests/s**.

Full-rollout scenario: 10,000 + 4,000 = **14,000 requests/s**.

These are conditional alternatives. They are not three quantities to add together and have no probability weights. The event requires review before the target date. Later evidence remains visible in the fixture but cannot improve the historical forecast retroactively.

## Usable web capacity

250 completed requests/s per worker at the stated request mix, p95 latency <= 200 ms, and errors <= 0.1% is a constructed measurement assumption. Checks at all modeled configurations are assumed, not run. The failure scope is loss of one of the listed independent groups; it does not represent region failure.

| Choice | Groups | Demand requests/s | After one group lost | Margin | Ready date assumption | Return date (exclusive) | Available at peak? |
|---|---|---:|---:|---:|---|---|---|
| existing-stage | 16+16+16+16 | 12,000 | 12,000 | 0 | 2026-06-28 | — | yes |
| existing-full | 16+16+16+16 | 14,000 | 12,000 | -2,000 | 2026-06-28 | — | yes |
| transfer-stage | 18+18+18+18 | 12,000 | 13,500 | 1,500 | 2026-06-30 | 2026-07-30 | yes |
| transfer-full | 18+18+18+18 | 14,000 | 13,500 | -500 | 2026-06-30 | 2026-07-30 | yes |
| new-group-full | 16+16+16+16+16 | 14,000 | 16,000 | 2,000 | 2026-08-09 | — | no |
| delayed-new-group-full | 16+16+16+16+16 | 14,000 | 16,000 | 2,000 | 2026-09-06 | — | no |

A nonnegative margin only passes the stated arithmetic constraint. Availability at the peak additionally requires that the ready date has arrived and any transfer agreement has not expired. Both are conditional assumptions; neither certifies workload behavior, approvals, or downstream dependencies. New supply still requires delivery and qualification.

## Cost and attribution

Current 64-worker service: **$2,560.00/day**, or **$76,800.00 for 30 days**.

The 30-day, 8-worker transfer increases service attribution by **$9,600.00** and decreases batch attribution by the same amount. Incremental enterprise cash from moving already-paid workers: **$0.00**. Batch opportunity cost remains unpriced and requires an agreement.

New 16-worker quote: **$640.00/day**, or **$19,200.00 per 30 days**. Realized cash effect requires the actual commercial obligations; no canceled commitment is assumed.

The transfer interval is [2026-06-30, 2026-07-30). If the workers return on that date, the gap before expected new supply is **10 days**, or **38 days** under the delayed alternative.

Bridging expected delivery would require 40 transfer days and **$12,800.00** attributed to the service. Bridging delayed delivery would require 68 transfer days and **$21,760.00**. Neither extension is approved by this report. Returning workers restores 12,000 requests/s of degraded web capacity; the staged estimate then has 0 requests/s of margin.

## Forecast method comparison

Weekly rolling origins, at least four initial weeks, fixed methods. Positive bias means underforecasting. All errors are requests/s. These synthetic results do not establish a production winner.

| Method | Horizon days | Cases | Bias | MAE | RMSE |
|---|---:|---:|---:|---:|---:|
| seasonal_naive | 1 | 12 | 45.00 | 63.33 | 72.11 |
| seasonal_naive | 7 | 12 | 45.00 | 63.33 | 72.11 |
| seasonal_naive | 8 | 11 | 89.09 | 94.55 | 108.80 |
| seasonal_naive | 14 | 11 | 89.09 | 94.55 | 108.80 |
| seasonal_naive | 42 | 7 | 298.57 | 298.57 | 299.98 |
| weekday_mean_4 | 1 | 12 | 116.25 | 116.25 | 123.15 |
| weekday_mean_4 | 7 | 12 | 116.25 | 116.25 | 123.15 |
| weekday_mean_4 | 8 | 11 | 160.68 | 160.68 | 166.55 |
| weekday_mean_4 | 14 | 11 | 160.68 | 160.68 | 166.55 |
| weekday_mean_4 | 42 | 7 | 367.50 | 367.50 | 367.72 |

Seasonal naive repeats the latest matching weekday. The alternative averages the latest four matching weekdays. The baseline is retained as the book's declared benchmark, not selected retrospectively to flatter the launch outcome. No calibrated prediction interval is claimed.

## Retrospective: intelligence helped and hurt

The rows are alternative constructed outcomes, not two observations to pool into an accuracy claim. Error is actual minus forecast.

| Alternative outcome | Actual | Baseline error | Adjusted error | Absolute error improvement | Margin under transfer configuration |
|---|---:|---:|---:|---:|---:|
| staged-launch-observed | 12,800 | 2,800 | 800 | 2,000 | 700 |
| delayed-launch-countercase | 10,200 | 200 | -1,800 | -1,600 | 3,300 |

## Separate pools: do not add these to the web total

**Long tail illustration:** top 20 projects use 800 units; 1,000 other projects use 200. Supply is 1,030. A shared change of 0.02 per small project adds 20 units and leaves 10; another 2% growth in the head produces 1,036 demand and a -6 margin. Illustrative aggregate error standard deviations are 1.58 with zero covariance and 11.29 with pairwise correlation 0.05. Neither is a probability guarantee.

**AI ledger:** 2,400,000,000 input tokens and 320,000,000 output tokens cost $12,000.00 at constructed prices. Model access subscriptions and supporting work bring the total to $100,000.00, or $1.25 per accepted task. The busy interval requires 2,400,000 input tokens/minute against an assumed 1,800,000 limit. An affordable month does not make that interval feasible.

**Index rebuild:** 12,000,000 records / (20,000 records per worker-minute × 20 compute minutes), rounded up, requires 30 qualified workers. The existing 16 can process 6,400,000 records in that compute window at the assumed rate. These workers are not presumed interchangeable with the web pool.

**Stateful data services:** unresolved service, maintenance, and recovery evidence remains an open planning dependency. The worker report cannot approve a database change.

## Review triggers

- forecast or observed demand consumes the staged margin
- request mix invalidates the tested rate
- new supply slips beyond the transfer agreement
- batch catch-up plan becomes infeasible
- launch timing or scope changes

## Limits

- Synthetic fixtures, not evidence about production behavior.
- No calibrated probabilities or prediction intervals.
- No inferred equivalence between resource pools.
- No annual seasonality or calendar-holiday model from 16 weeks of history.
- Only two fixed forecasting methods; no provider adapter or automated purchasing.
- The displayed choice is a recommendation whose approvals and measurements remain conditions.

The JSON retains assumptions, evidence dates, event revisions, alternatives, and retrospective errors. CSVs support inspection in a spreadsheet; they do not replace the conditions recorded here.
