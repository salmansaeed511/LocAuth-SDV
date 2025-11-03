from __future__ import annotations
import base64, os, requests
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# supports both: `python -m control_gateway.server` and `python control_gateway\server.py`
try:
    from .verify import verify_tag
except Exception:
    from control_gateway.verify import verify_tag  # fallback

app = FastAPI()
EAS_URL = os.environ.get("EAS_URL", "http://127.0.0.1:8000")
K_SESSION_DB = {}

class OpenSession(BaseModel):
    session_id: str
    ticket_b64: str
    transcript_b64: str

class Frame(BaseModel):
    session_id: str
    can_id: int
    payload_b64: str
    ctr: int
    tag_b64: str

@app.post("/open_session")
def open_session(req: OpenSession):
    r = requests.post(f"{EAS_URL}/redeem", json={
        "ticket": req.ticket_b64,
        "transcript": req.transcript_b64,
    }, timeout=5)
    if r.status_code != 200:
        return {"ok": False, "err": "redeem_failed", "detail": r.text}
    K_session_b64 = r.json().get("K_session_b64")
    if not K_session_b64:
        return {"ok": False, "err": "no_k_session"}
    K_SESSION_DB[req.session_id] = base64.b64decode(K_session_b64)
    return {"ok": True}

@app.post("/frame")
def accept_frame(f: Frame):
    K_session = K_SESSION_DB.get(f.session_id)
    if not K_session:
        return {"ok": False, "err": "unknown_session"}
    header = f.can_id.to_bytes(4, 'big')
    payload = base64.b64decode(f.payload_b64)
    tag = base64.b64decode(f.tag_b64)
    ok = verify_tag(K_session, header, payload, f.ctr, tag)
    return {"ok": ok}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
