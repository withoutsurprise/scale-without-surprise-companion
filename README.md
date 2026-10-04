# Scale Without Surprise — companion examples

Companion code for *Scale Without Surprise: A Practical Guide to Cloud Cost and
Capacity* by Timothy O'Brien, draft edition, October 2026. The current version
is published at https://github.com/withoutsurprise/scale-without-surprise-companion.

From the directory that contains `examples/`, the root of the repository or of
its downloaded archive, run:

```sh
python3 examples/capacity_portfolio/run.py
python3 -m unittest discover -s examples/capacity_portfolio -p 'test_*.py'
python3 examples/portfolio_math.py
python3 examples/data_capacity_math.py
```

Requires Python 3.9+ and the standard library. No credentials, cloud services,
or package installation. Read examples/capacity_portfolio/README.md for the
fixtures, generated outputs, forecast methods, tests, and explicit limits.

All numerical scenarios are constructed. The programs retain assumptions and
expose decisions; they do not authorize actions or establish safe production
configurations.

The two figures the companion generates can be regenerated with:

```sh
python3 examples/capacity_portfolio/figures.py
```

This repository contains the examples and those two figures only; the book and
its publishing pipeline are separate. No proprietary records or production
credentials are included.

## License

Copyright 2026 Timothy O'Brien. The code, data, and generated figures in this
repository are licensed under the Apache License, Version 2.0; see `LICENSE`.
That license does not extend to the book, whose text and illustrations are all
rights reserved.
