from __future__ import annotations
import time, os, csv, numpy as np
from .trace_gen import gen_trace

HELLO_URL = "http://127.0.0.1:8000/hello"

def emulate_handshake(lat_ms: float) -> float:
    from vehicle_node.handshake import handshake
    t0 = time.perf_counter()
    time.sleep(lat_ms / 2000.0)   # half-RTT pre
    handshake(HELLO_URL)
    time.sleep(lat_ms / 2000.0)   # half-RTT post
    t1 = time.perf_counter()
    return (t1 - t0) * 1000.0

def run_benchmark(n: int = 100, results_dir: str = "results"):
    os.makedirs(results_dir, exist_ok=True)
    df = gen_trace(n=n)
    samples = []
    for rtt in df["rtt_ms"].tolist():
        samples.append(emulate_handshake(rtt))
    arr = np.array(samples, dtype=float)
    p50 = float(np.percentile(arr, 50))
    p95 = float(np.percentile(arr, 95))
    print(f"Handshake latency: p50={p50:.1f} ms, p95={p95:.1f} ms (n={n})")

    csv_path = os.path.join(results_dir, f"handshakes_{n}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sample_idx", "latency_ms"])
        for i, v in enumerate(samples):
            w.writerow([i, v])
    print(f"[saved] {csv_path}")
    return p50, p95
