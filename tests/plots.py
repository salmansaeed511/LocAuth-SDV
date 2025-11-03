from __future__ import annotations
import os, csv
import matplotlib.pyplot as plt

RESULTS_DIR = "results"
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")

def _load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def _save(fig, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    print(f"[plot saved] {out_path}")

def plot_frames_series(n_frames: int):
    path = os.path.join(RESULTS_DIR, f"frames_{n_frames}.csv")
    rows = _load_csv(path)
    x = [int(r["frame_idx"]) for r in rows]
    y = [float(r["rtt_ms"]) for r in rows]

    fig = plt.figure()
    plt.plot(x, y)
    plt.title(f"Per-frame verify RTT (n={n_frames})")
    plt.xlabel("Frame index")
    plt.ylabel("RTT (ms)")
    out = os.path.join(PLOTS_DIR, f"frames_series_{n_frames}.png")
    _save(fig, out)
    return fig

def plot_frames_hist(n_frames: int, bins: int = 20):
    path = os.path.join(RESULTS_DIR, f"frames_{n_frames}.csv")
    rows = _load_csv(path)
    y = [float(r["rtt_ms"]) for r in rows]

    fig = plt.figure()
    plt.hist(y, bins=bins)
    plt.title(f"Per-frame verify RTT — Histogram (n={n_frames})")
    plt.xlabel("RTT (ms)")
    plt.ylabel("Count")
    out = os.path.join(PLOTS_DIR, f"frames_hist_{n_frames}.png")
    _save(fig, out)
    return fig

def plot_handshake_cdf(n_samples: int):
    path = os.path.join(RESULTS_DIR, f"handshakes_{n_samples}.csv")
    rows = _load_csv(path)
    vals = sorted(float(r["latency_ms"]) for r in rows)
    if not vals:
        print(f"[warn] no handshake data: {path}")
        return None

    y = [i / (len(vals) - 1) if len(vals) > 1 else 1.0 for i in range(len(vals))]

    fig = plt.figure()
    plt.plot(vals, y)
    plt.title(f"Handshake latency ECDF (n={n_samples})")
    plt.xlabel("Latency (ms)")
    plt.ylabel("CDF")
    out = os.path.join(PLOTS_DIR, f"handshake_ecdf_{n_samples}.png")
    _save(fig, out)
    return fig

def make_all_plots(n: int, show: bool = True):
    """Generate and optionally show all plots together."""
    figs = []
    f1 = plot_frames_series(n)
    if f1: figs.append(f1)
    f2 = plot_frames_hist(n)
    if f2: figs.append(f2)
    f3 = plot_handshake_cdf(n)
    if f3: figs.append(f3)

    if show:
        # Display all figures together
        plt.show(block=False)
        print("plots")
        plt.pause(0)  # ensures non-blocking behavior
