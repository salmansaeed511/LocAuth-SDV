from __future__ import annotations
import numpy as np, pandas as pd

def gen_trace(n: int = 1000, mean: float = 22.0, jitter: float = 6.0, spike_prob: float = 0.01) -> pd.DataFrame:
    base = np.random.normal(loc=mean, scale=jitter, size=n)
    spikes = np.random.rand(n) < spike_prob
    base[spikes] += np.random.uniform(30, 80, size=spikes.sum())
    base = np.clip(base, 5, None)
    return pd.DataFrame({"rtt_ms": base})
