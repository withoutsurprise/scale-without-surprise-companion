"""Generate monochrome manuscript SVGs from the companion's computed report.

No image service or plotting package is needed. Numeric coordinates come from
the same calculations as the report. Labels remain text in the SVG sources.
"""

from html import escape
from pathlib import Path


def text(x, y, value, size=26, anchor="start", weight="normal"):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(value))}</text>'


def line(x1, y1, x2, y2, stroke="#222", width=2, dash=None):
    pattern = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{pattern}/>'


def frame(title, description):
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620" viewBox="0 0 1000 620" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(title)}</title><desc id="description">{escape(description)}</desc>',
        '<rect width="1000" height="620" fill="white"/>',
        '<g font-family="Arial, Helvetica, sans-serif" fill="#111">',
        text(50, 52, title, 32, weight="bold"),
    ]


def forecast_svg(report):
    parts = frame("The same intelligence can help or hurt",
                  "Two constructed outcomes share a 10000 requests/s baseline and a 12000 adjusted forecast. Actual demand is 12800 when rollout proceeds and 10200 in the delayed-launch alternative.")
    parts += [text(50, 91, "Constructed outcomes; requests per second", 26)]
    top, bottom = 155, 435
    y = lambda value: bottom - value / 15000 * (bottom - top)
    for value in (0, 5000, 10000, 15000):
        parts += [line(100, y(value), 950, y(value), "#d2d2d2", 1),
                  text(87, y(value) + 9, f"{value // 1000}k", 26, "end")]
    parts += [text(295, 134, "Rollout proceeds", 28, "middle", "bold"),
              text(755, 134, "Rollout delayed", 28, "middle", "bold")]
    for outcome, centers in zip(report["retrospective_alternative_outcomes"], ((175, 290, 405), (635, 750, 865))):
        values = (outcome["baseline_forecast"], outcome["adjusted_forecast"], outcome["actual_peak_rps"])
        for center, value, label, fill in zip(centers, values, ("Baseline", "Adjusted", "Actual"), ("#efefef", "#999", "#222")):
            parts.append(f'<rect x="{center - 33}" y="{y(value):.1f}" width="66" height="{bottom - y(value):.1f}" fill="{fill}" stroke="#222" stroke-width="2"/>')
            parts += [text(center, y(value) - 12, f"{value:,.0f}", 26, "middle"),
                      text(center, 477, label, 26, "middle")]
    parts += [text(295, 534, "Absolute error: 2,800 to 800", 27, "middle"),
              text(755, 534, "Absolute error: 200 to 1,800", 27, "middle"),
              text(500, 588, "Alternative histories, not a measured success rate.", 26, "middle"), "</g></svg>"]
    return "\n".join(parts) + "\n"


def capacity_svg(report):
    parts = frame("The return date leaves a gap",
                  "The modeled web service supplies 12000 requests/s after one failure group is lost, rising to 13500 when the transfer is ready on day 2. Its 30-day agreement expires at day 32. New supply is only estimated for day 42, when degraded capacity would reach 16000. Bridging the ten-day gap needs another agreement.")
    parts += [text(50, 91, "Capacity after one failure group is lost; requests/s", 26)]
    top, bottom = 158, 434
    x = lambda value: 110 + value / 70 * 825
    y = lambda value: bottom - (value - 10000) / 7000 * (bottom - top)
    for value in (10000, 12000, 14000, 16000):
        parts += [line(110, y(value), 935, y(value), "#d2d2d2", 1),
                  text(97, y(value) + 8, f"{value // 1000}k", 26, "end")]
    for value in (0, 32, 42, 70):
        parts += [line(x(value), bottom, x(value), bottom + 8),
                  text(x(value), bottom + 39, str(value), 26, "middle")]
    parts.append(text(520, 512, "Days after the planning decision", 26, "middle"))
    caps = {r["choice"]: r["degraded_rps"] for r in report["supply_cases"]}
    base, transfer, future = caps["existing-stage"], caps["transfer-stage"], caps["new-group-full"]
    initial = [(0, base), (2, base), (2, transfer), (32, transfer), (32, base), (42, base)]
    parts.append('<polyline points="' + " ".join(f"{x(t):.1f},{y(v):.1f}" for t, v in initial) + '" fill="none" stroke="#111" stroke-width="5"/>')
    parts += [line(x(42), y(base), x(42), y(future), "#111", 5, "10 7"),
              line(x(42), y(future), x(70), y(future), "#111", 5, "10 7"),
              line(x(32), y(transfer), x(42), y(transfer), "#777", 5, "3 6"),
              text(205, y(transfer) - 19, "13,500", 27),
              text(665, y(future) - 17, "16,000", 27),
              text(x(37), y(base) + 38, "10 days", 26, "middle"),
              text(155, 137, "Transfer ready on day 2", 26),
              text(665, 263, "New group", 26),
              text(665, 295, "estimated day 42", 26),
              text(500, 557, "Dotted bridge: extension requires a new agreement.", 26, "middle"),
              text(500, 594, "Without extension, capacity returns to 12,000 on day 32.", 26, "middle"),
              "</g></svg>"]
    return "\n".join(parts) + "\n"


def write_figures(report, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "forecast-intelligence.svg").write_text(forecast_svg(report), encoding="utf-8")
    (destination / "web-capacity-timeline.svg").write_text(capacity_svg(report), encoding="utf-8")


if __name__ == "__main__":
    import json
    from model import make_report, read_observations
    root = Path(__file__).resolve().parent
    fixture = root / "fixtures"
    report = make_report(json.loads((fixture / "portfolio.json").read_text()),
                         json.loads((fixture / "events.json").read_text()),
                         read_observations(fixture / "observations.csv"))
    destination = root.parents[1] / "manuscript" / "figures"
    write_figures(report, destination)
    print(f"Wrote two reproducible manuscript SVGs to {destination}")
