from __future__ import annotations
import base64, time, uuid, requests, os, csv
from dataclasses import dataclass
from .handshake import handshake
from control_gateway.verify import tag_frame

CGW_URL = "http://127.0.0.1:9000"

@dataclass
class SendStats:
    ok: int; fail: int; avg_us: float

def run_demo(n_frames: int = 100, results_dir: str = "results") -> SendStats:
    os.makedirs(results_dir, exist_ok=True)
    hs = handshake()
    session_id = str(uuid.uuid4())
    transcript_b64 = base64.b64encode(hs.transcript).decode()
    ticket_b64 = base64.b64encode(hs.ticket).decode()

    r = requests.post(f"{CGW_URL}/open_session", json={
        "session_id": session_id,
        "ticket_b64": ticket_b64,
        "transcript_b64": transcript_b64,
    }, timeout=5).json()
    if not r.get("ok"):
        raise RuntimeError(f"CGW open_session failed: {r}")

    ok = fail = 0
    t_total = 0.0
    csv_path = os.path.join(results_dir, f"frames_{n_frames}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["frame_idx","rtt_ms","ok","can_id","payload_len"])
        for i in range(n_frames):
            can_id = 0x123
            payload = f"SPD:{30+i:03d}".encode()
            header = can_id.to_bytes(4, 'big')
            tag = tag_frame(hs.K_session, header, payload, i)

            t0 = time.perf_counter()
            resp = requests.post(f"{CGW_URL}/frame", json={
                "session_id": session_id,
                "can_id": can_id,
                "payload_b64": base64.b64encode(payload).decode(),
                "ctr": i,
                "tag_b64": base64.b64encode(tag).decode(),
            }, timeout=3).json()
            t1 = time.perf_counter()

            rtt_ms = (t1 - t0) * 1000.0
            t_total += (t1 - t0)

            ok_flag = 1 if resp.get("ok") else 0
            ok += ok_flag
            fail += (1 - ok_flag)
            w.writerow([i, rtt_ms, ok_flag, can_id, len(payload)])

    avg_us = (t_total / n_frames) * 1e6 if n_frames else 0.0
    print(f"Frames ok={ok}, fail={fail}, avg verify RTT ~{avg_us:.1f} µs")
    print(f"[saved] {csv_path}")
    return SendStats(ok=ok, fail=fail, avg_us=avg_us)
