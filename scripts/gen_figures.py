#!/usr/bin/env python3
"""Generate the CS-A study figures (SVG) from analysis/results.csv.

Usage: python3 scripts/gen_figures.py  (from the repo root)
Writes analysis/figures/*.svg. No dependencies beyond the stdlib.

Design notes: dark terminal-style panel (#141414) matching bomly.dev's
terminal mocks, so the figures read identically on the blog (dark-default)
and on GitHub in light or dark mode. Series colors are fixed by entity:
blue = bare, orange = with the Bomly MCP server. Palette validated for
colorblind separation and contrast against the panel surface.
"""

import csv
import collections
import os
import sys

# ---------------------------------------------------------------- palette
PANEL = "#141414"
BORDER = "#262626"
GRID = "#242424"
TEXT = "#ededed"
TEXT2 = "#a3a3a3"
TEXT3 = "#737373"
BARE = "#189fdb"   # blue  — bare condition
MCP = "#e75c3a"    # orange — with Bomly MCP (bomly.dev accent)

SANS = "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

CELL_LABELS = [
    ("claude", "bare", "Claude Code · bare"),
    ("claude", "mcp", "Claude Code · MCP"),
    ("codex", "bare", "Codex CLI · bare"),
    ("codex", "mcp", "Codex CLI · MCP"),
]


def load_runs(csv_path):
    """One record per (agent, condition, scope, run)."""
    runs = {}
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            k = (r["agent"], r["condition"], r["scope"], int(r["run_number"]))
            runs[k] = {
                "comp": float(r["run_completeness"]),
                "wall": float(r["wall_seconds"]),
                "build": r["build_ok"] == "True",
                "tools": int(r["tool_calls"]),
            }
    return runs


def load_bad_runs(csv_path):
    """(agent, condition) -> set of bigapp run numbers with >=1 hallucinated
    or wrongly-declined package."""
    bad = collections.defaultdict(set)
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            if r["scope"] == "bigapp" and r["outcome"] in (
                "HALLUCINATED",
                "INCORRECTLY_DECLINED",
            ):
                bad[(r["agent"], r["condition"])].add(int(r["run_number"]))
    return bad


def svg_open(w, h, title):
    return [
        f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}">',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" '
        f'fill="{PANEL}" stroke="{BORDER}"/>',
    ]


def text(x, y, s, size=11, color=TEXT2, anchor="start", weight="normal",
         family=SANS):
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{s}</text>'
    )


def header(parts, w, title, subtitle):
    parts.append(text(24, 34, title, 15, TEXT, weight="600", family=MONO))
    parts.append(text(24, 54, subtitle, 12, TEXT2))


def legend(parts, x, y):
    parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{BARE}"/>')
    parts.append(text(x + 11, y + 4, "bare", 11, TEXT2))
    parts.append(f'<circle cx="{x + 58}" cy="{y}" r="5" fill="{MCP}"/>')
    parts.append(text(x + 69, y + 4, "with Bomly MCP", 11, TEXT2))


def dot(parts, x, y, color, r=6):
    parts.append(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" '
        f'stroke="{PANEL}" stroke-width="2"/>'
    )


def spread_dups(values):
    """Vertical offsets so identical values don't fully overlap."""
    counts = collections.Counter(values)
    seen = collections.Counter()
    offsets = []
    for v in values:
        n = counts[v]
        i = seen[v]
        seen[v] += 1
        offsets.append(0 if n == 1 else (i - (n - 1) / 2) * 8)
    return offsets


# ------------------------------------------------------- fig 1: completeness
def fig_completeness(runs, out):
    W, H = 720, 352
    x0, x1 = 200, 688
    rows_y = [104, 158, 224, 278]
    parts = svg_open(W, H, "Completeness per run on the bigapp fixture")
    header(
        parts, W,
        "bigapp (Grouper 4.x) — completeness per run",
        "Share of the 56 fixable advisories remediated, per run. N=5 per cell.",
    )
    legend(parts, x0, 76)

    def X(pct):
        return x0 + (x1 - x0) * pct / 100.0

    # grid + x labels
    for pct in (0, 25, 50, 75, 100):
        gx = X(pct)
        parts.append(
            f'<line x1="{gx:.1f}" y1="92" x2="{gx:.1f}" y2="302" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(text(gx, 322, f"{pct}%", 11, TEXT3, anchor="middle"))
    # agent group separator
    parts.append(
        f'<line x1="24" y1="191" x2="{x1}" y2="191" stroke="{GRID}" '
        f'stroke-width="1"/>'
    )

    for (agent, cond, label), y in zip(CELL_LABELS, rows_y):
        color = MCP if cond == "mcp" else BARE
        parts.append(text(188, y + 4, label, 12, TEXT2, anchor="end"))
        vals = [
            runs[(agent, cond, "bigapp", n)]["comp"] * 100 for n in range(1, 6)
        ]
        offs = spread_dups(vals)
        for v, off in zip(vals, offs):
            dot(parts, X(v), y + off, color)

    # selective annotations
    x14 = X(14.3)
    parts.append(
        f'<line x1="{x14:.1f}" y1="{rows_y[0] + 16}" x2="{x14:.1f}" '
        f'y2="{rows_y[0] + 30}" stroke="{TEXT3}" stroke-width="1"/>'
    )
    parts.append(
        text(x14, rows_y[0] + 43, "2 of 5 runs stopped at 14%", 11, TEXT2,
             anchor="middle")
    )
    parts.append(
        text(X(100) - 12, rows_y[1] - 16, "MCP: never below 98%", 11, TEXT2,
             anchor="end")
    )
    parts.append("</svg>")
    write(out, parts)


# ----------------------------------------------------- fig 2: hallucination
def fig_hallucination(bad, out):
    W, H = 720, 300
    x0, x1 = 200, 688
    rows_y = [104, 152, 212, 260]
    parts = svg_open(W, H, "Runs with hallucinated or wrongly-declined fixes")
    header(
        parts, W,
        "bigapp — runs with a hallucinated or wrong fix claim",
        "Runs (of 5) where at least one package was claimed fixed but was not, "
        "or wrongly declined.",
    )
    legend(parts, x0, 76)

    def X(v):
        return x0 + (x1 - x0) * v / 5.0

    for v in range(6):
        gx = X(v)
        parts.append(
            f'<line x1="{gx:.1f}" y1="92" x2="{gx:.1f}" y2="274" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(text(gx, 291, str(v), 11, TEXT3, anchor="middle"))
    parts.append(
        f'<line x1="24" y1="182" x2="{x1}" y2="182" stroke="{GRID}" '
        f'stroke-width="1"/>'
    )

    for (agent, cond, label), y in zip(CELL_LABELS, rows_y):
        color = MCP if cond == "mcp" else BARE
        n = len(bad.get((agent, cond), set()))
        parts.append(text(188, y + 4, label, 12, TEXT2, anchor="end"))
        bw = X(n) - x0
        parts.append(
            f'<path d="M {x0} {y - 9} h {bw - 4:.1f} a 4 4 0 0 1 4 4 v 10 '
            f'a 4 4 0 0 1 -4 4 h {-(bw - 4):.1f} z" fill="{color}"/>'
        )
        parts.append(text(X(n) + 10, y + 4, f"{n} of 5", 11, TEXT, weight="600"))
    parts.append("</svg>")
    write(out, parts)


# ------------------------------------------------------------ fig 3: time
def fig_time(runs, out):
    W, H = 720, 330
    x0, x1 = 200, 688
    rows_y = [104, 158, 224, 278]
    tmax = 1050
    parts = svg_open(W, H, "Wall-clock time per run on the bigapp fixture")
    header(
        parts, W,
        "bigapp — wall-clock time per run",
        "Minutes per run; the tick marks each cell’s mean. N=5 per cell.",
    )
    legend(parts, x0, 76)

    def X(s):
        return x0 + (x1 - x0) * s / tmax

    for m in (0, 4, 8, 12, 16):
        gx = X(m * 60)
        parts.append(
            f'<line x1="{gx:.1f}" y1="92" x2="{gx:.1f}" y2="292" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(text(gx, 310, f"{m}m", 11, TEXT3, anchor="middle"))
    parts.append(
        f'<line x1="24" y1="191" x2="{x1}" y2="191" stroke="{GRID}" '
        f'stroke-width="1"/>'
    )

    for (agent, cond, label), y in zip(CELL_LABELS, rows_y):
        color = MCP if cond == "mcp" else BARE
        parts.append(text(188, y + 4, label, 12, TEXT2, anchor="end"))
        vals = [
            runs[(agent, cond, "bigapp", n)]["wall"] for n in range(1, 6)
        ]
        mean = sum(vals) / len(vals)
        parts.append(
            f'<line x1="{X(mean):.1f}" y1="{y - 13}" x2="{X(mean):.1f}" '
            f'y2="{y + 13}" stroke="{TEXT2}" stroke-width="2"/>'
        )
        for v, off in zip(vals, spread_dups(vals)):
            dot(parts, X(v), y + off, color)
    mean_codex_mcp = sum(
        runs[("codex", "mcp", "bigapp", n)]["wall"] for n in range(1, 6)
    ) / 5
    parts.append(
        text(X(mean_codex_mcp), rows_y[3] - 24,
             f"mean {mean_codex_mcp / 60:.1f}m", 11, TEXT2, anchor="middle")
    )
    parts.append("</svg>")
    write(out, parts)


# --------------------------------------------------- fig 5: effort/outcome
def fig_effort(runs, out):
    W, H = 720, 420
    y0, y1 = 130, 330
    tmax = 100
    panels = [("claude", "Claude Code", 90, 368), ("codex", "Codex CLI", 410, 688)]
    parts = svg_open(W, H, "Tool calls versus completeness per run on bigapp")
    header(
        parts, W,
        "bigapp — tool calls vs. completeness per run",
        "All 20 runs. More effort did not mean a better outcome without the "
        "list.",
    )
    legend(parts, 90, 76)

    def Y(pct):
        return y1 - (y1 - y0) * pct / 100.0

    for agent, label, px0, px1 in panels:
        def X(v):
            return px0 + (px1 - px0) * v / tmax

        parts.append(text((px0 + px1) / 2, 112, label, 12, TEXT,
                          anchor="middle", weight="600", family=MONO))
        for pct in (0, 25, 50, 75, 100):
            gy = Y(pct)
            parts.append(
                f'<line x1="{px0}" y1="{gy:.1f}" x2="{px1}" y2="{gy:.1f}" '
                f'stroke="{GRID}" stroke-width="1"/>'
            )
        for v in (0, 25, 50, 75, 100):
            gx = X(v)
            parts.append(
                f'<line x1="{gx:.1f}" y1="{y0}" x2="{gx:.1f}" y2="{y1}" '
                f'stroke="{GRID}" stroke-width="1"/>'
            )
            parts.append(text(gx, y1 + 20, str(v), 11, TEXT3,
                              anchor="middle"))
        marked = None
        for cond, color in (("bare", BARE), ("mcp", MCP)):
            for n in range(1, 6):
                r = runs[(agent, cond, "bigapp", n)]
                dot(parts, X(r["tools"]), Y(r["comp"] * 100), color)
                if cond == "bare" and r["tools"] > 80:
                    marked = (X(r["tools"]), Y(r["comp"] * 100))
        if marked:
            mx, my = marked
            parts.append(
                f'<line x1="{mx:.1f}" y1="{my - 12}" x2="{mx:.1f}" '
                f'y2="{my - 30}" stroke="{TEXT3}" stroke-width="1"/>'
            )
            parts.append(
                text(mx + 4, my - 38, "87 calls, 14% complete", 11, TEXT2,
                     anchor="end")
            )
    for pct in (0, 25, 50, 75, 100):
        parts.append(text(80, Y(pct) + 4, f"{pct}%", 11, TEXT3, anchor="end"))
    parts.append(
        text((90 + 688) / 2, y1 + 44, "tool calls in the run", 11, TEXT3,
             anchor="middle")
    )
    parts.append("</svg>")
    write(out, parts)


# --------------------------------------------------------- fig 4: ceiling
def fig_ceiling(runs, out):
    W, H = 720, 424
    x0, x1 = 200, 688
    fixtures = [("webapp", "webapp (npm)"), ("service", "service (Python)"),
                ("api-java", "api-java (Maven)")]
    agents = [("claude", "Claude Code"), ("codex", "Codex CLI")]
    # build-broken cells (round 1), marked with a dagger in the caption
    broken = {("claude", "bare", "service"), ("claude", "mcp", "service"),
              ("claude", "bare", "api-java")}
    parts = svg_open(W, H, "Completeness on the three smaller fixtures")
    header(
        parts, W,
        "The three smaller fixtures — completeness, round 1",
        "Both agents finish at or near 100% with or without MCP: a ceiling, "
        "not a win.",
    )
    legend(parts, x0, 76)

    def X(pct):
        return x0 + (x1 - x0) * pct / 100.0

    for pct in (0, 25, 50, 75, 100):
        gx = X(pct)
        parts.append(
            f'<line x1="{gx:.1f}" y1="92" x2="{gx:.1f}" y2="378" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(text(gx, 396, f"{pct}%", 11, TEXT3, anchor="middle"))

    y = 112
    callout = None
    for fi, (scope, flabel) in enumerate(fixtures):
        parts.append(text(24, y + 2, flabel, 12, TEXT, weight="600",
                          family=MONO))
        y += 22
        for agent, alabel in agents:
            parts.append(text(188, y + 4, alabel, 12, TEXT2, anchor="end"))
            for cond, color, off in (("bare", BARE, -4), ("mcp", MCP, 4)):
                v = runs[(agent, cond, scope, 1)]["comp"] * 100
                other = runs[(agent, "mcp" if cond == "bare" else "bare",
                              scope, 1)]["comp"] * 100
                yoff = off if abs(v - other) < 2.5 else 0
                dot(parts, X(v), y + yoff, color)
                if (agent, cond, scope) in broken:
                    parts.append(text(X(v), y - 10 + yoff, "†", 11, TEXT2,
                                      anchor="middle"))
                if v < 75:
                    callout = (X(v) - 14, y + 4, f"{v:.0f}%")
            y += 26
        if fi < 2:
            parts.append(
                f'<line x1="24" y1="{y + 2}" x2="{x1}" y2="{y + 2}" '
                f'stroke="{GRID}" stroke-width="1"/>'
            )
        y += 22
    if callout:
        cx, cy, cs = callout
        parts.append(text(cx, cy, cs, 11, TEXT2, anchor="end"))
    parts.append(
        text(24, 414, "† run finished with the shared build broken",
             11, TEXT3)
    )
    parts.append("</svg>")
    write(out, parts)


def write(path, parts):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(parts) + "\n")
    print("wrote", path)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(root, "analysis", "results.csv")
    figdir = os.path.join(root, "analysis", "figures")
    runs = load_runs(csv_path)
    bad = load_bad_runs(csv_path)
    fig_completeness(runs, os.path.join(figdir, "bigapp-completeness.svg"))
    fig_hallucination(bad, os.path.join(figdir, "bigapp-hallucination.svg"))
    fig_time(runs, os.path.join(figdir, "bigapp-time.svg"))
    fig_ceiling(runs, os.path.join(figdir, "ceiling-three-fixtures.svg"))
    fig_effort(runs, os.path.join(figdir, "bigapp-effort.svg"))


if __name__ == "__main__":
    sys.exit(main())
