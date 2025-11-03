from __future__ import annotations
from vehicle_node.can_client import run_demo
from latency.harness import run_benchmark
from tests.plots import make_all_plots

MENU = (
    "Choose vehicle density scenario (frames to send):\n"
    "  1) Low    (1)\n"
    "  2) Medium (50)\n"
    "  3) High   (100)\n"
    "  Or enter any positive integer \n"
    "-->"
)

def ask_n_frames(default: int = 50) -> int:
    raw = input(MENU).strip()
    if raw == "1":
        return 1
    if raw == "2":
        return 50
    if raw == "3":
        return 100
    try:
        n = int(raw)
        if n <= 0:
            print(f"Invalid value — must be > 0. Using default {default}.")
            return default
        return n
    except ValueError:
        print(f"Invalid input — using default {default}.")
        return default

if __name__ == "__main__":
    n = ask_n_frames(default=50)
    print(f"[Scenario] Running handshake + {n} authenticated frames")
    run_demo(n_frames=n)
    print(f"\n[Benchmark] Handshake latency under 5G-like RTTs (n={n})")
    run_benchmark(n=n)
    print("\n[Plots] Generating PNGs...")
    make_all_plots(n, show=True)
    print("Done. See results/ and results/plots/")
