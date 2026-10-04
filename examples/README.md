# Companion and worked arithmetic

The integrated planning cycle is in `capacity_portfolio/`. From the directory that contains `examples/`, run `python3 examples/capacity_portfolio/run.py`. It produces a review report and JSON/CSV data without credentials. Read `capacity_portfolio/README.md` for methods, fixtures and boundaries. Run its boundary tests with `python3 -m unittest discover -s examples/capacity_portfolio -p 'test_*.py'`.
## Portfolio arithmetic

Run `python3 examples/portfolio_math.py` from the same directory. Only Python's standard library is required. The script prints JSON reproducing the constructed examples in Chapters 5 and 15:

- Concentration, tail growth, and headroom exhaustion in one resource pool.
- Aggregate forecast-error standard deviation with and without positive correlation.
- A provisional CPU estimate, cache-miss sensitivity, and risk break-even arithmetic.

These are reproducible teaching calculations, not a fitted forecast, a power-law test, a rightsizing tool, or the complete companion model. Correlations, prices, service limits, and workload behavior require evidence before use in an actual plan. The complete integrated teaching cycle is implemented in `capacity_portfolio/`; see its README for scope and validation.

## Data-capacity arithmetic

Run `python3 examples/data_capacity_math.py` from the same directory to reproduce Chapter 12's synthetic Cassandra footprint and transfer, Kafka retention and catch-up, and PostgreSQL WAL-retention examples. Inputs use binary MiB/GiB/TiB units and constant rates. JSON `null` for catch-up means outstanding work cannot clear at the assumed processing rate. These are teaching calculations, not measured benchmarks, live collectors, or production sizing advice.
