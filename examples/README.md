# Companion and worked arithmetic

The integrated planning cycle is in `capacity_portfolio/`. From the directory that contains `examples/`, run `python3 examples/capacity_portfolio/run.py`. It produces a review report and JSON/CSV data without credentials. Read `capacity_portfolio/README.md` for methods, fixtures and boundaries. Run its boundary tests, which also check the arithmetic below, with `python3 -m unittest discover -s examples/capacity_portfolio -p 'test_*.py'`.
## Portfolio arithmetic

Run `python3 examples/portfolio_math.py` from the same directory. Only Python's standard library is required. The script prints JSON reproducing the constructed examples in Chapters 1, 5 and 15:

- Chapter 1's $448,000 thirty-day ledger grouped five ways (work, team, location, charge behavior and funding), with each view reconciled to the same total; the shares, annualized figures and batch-worker transfer the chapter cites. A view that does not reconcile is rejected rather than printed.
- Chapter 5's search-mix sensitivity: a shift from 5 to 7 percent history searches uses up the transfer's 12.5 percent margin.
- Concentration, tail growth, and headroom exhaustion in one resource pool.
- Aggregate forecast-error standard deviation with and without positive correlation.
- A provisional CPU estimate, cache-miss sensitivity, and risk break-even arithmetic.

These are reproducible teaching calculations, not a fitted forecast, a power-law test, a rightsizing tool, or the complete companion model. Correlations, prices, service limits, and workload behavior require evidence before use in an actual plan. The complete integrated teaching cycle is implemented in `capacity_portfolio/`; see its README for scope and validation.

## Data-capacity arithmetic

Run `python3 examples/data_capacity_math.py` from the same directory to reproduce Chapter 12's synthetic Cassandra footprint and transfer, Kafka retention and catch-up, and PostgreSQL WAL-retention examples. Inputs use binary MiB/GiB/TiB units and constant rates. JSON `null` for catch-up means outstanding work cannot clear at the assumed processing rate. These are teaching calculations, not measured benchmarks, live collectors, or production sizing advice.
