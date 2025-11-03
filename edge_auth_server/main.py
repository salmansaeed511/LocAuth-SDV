from __future__ import annotations
import base64, os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from common.crypto import (
    gen_ecdh_keypair, pubkey_bytes, ecdh_shared, hkdf,
    aead_encrypt, aead_decrypt, SchnorrProof, schnorr_verify
)

app = FastAPI()

EAS_PRIV, EAS_PUB = gen_ecdh_keypair()
TICKET_AEAD_KEY = os.urandom(32)

class HelloReq(BaseModel):
    c_nonce: str
    V_e: str
    proof_R: str
    proof_s: str

class HelloResp(BaseModel):
    s_nonce: str
    E_e: str
    ticket: str
    k_info: str

class RedeemReq(BaseModel):
    ticket: str
    transcript: str

class RedeemResp(BaseModel):
    K_session_b64: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/hello", response_model=HelloResp)
def hello(req: HelloReq):
    c_nonce = base64.b64decode(req.c_nonce)
    V_e_bytes = base64.b64decode(req.V_e)
    proof = SchnorrProof(
        R=base64.b64decode(req.proof_R),
        s=base64.b64decode(req.proof_s)
    )

    if not schnorr_verify(V_e_bytes, proof, c_nonce):
        raise HTTPException(status_code=400, detail="Invalid ZKP")

    E_e_priv, E_e_pub = gen_ecdh_keypair()
    E_e_bytes = pubkey_bytes(E_e_pub)
    s1 = ecdh_shared(E_e_priv, V_e_bytes)
    transcript = c_nonce + V_e_bytes + E_e_bytes
    K = hkdf(s1 + transcript, info=b"ECDDH-SDV-K")
    K_session = hkdf(K, info=b"ECDDH-SDV-session")

    payload = b"K_session:" + K_session
    ticket_blob = aead_encrypt(TICKET_AEAD_KEY, aad=transcript, plaintext=payload)

    s_nonce = os.urandom(16)
    return HelloResp(
        s_nonce=base64.b64encode(s_nonce).decode(),
        E_e=base64.b64encode(E_e_bytes).decode(),
        ticket=base64.b64encode(ticket_blob).decode(),
        k_info=base64.b64encode(b"ECDDH-SDV-K").decode(),
    )

@app.post("/redeem", response_model=RedeemResp)
def redeem(req: RedeemReq):
    try:
        ticket_blob = base64.b64decode(req.ticket)
        transcript = base64.b64decode(req.transcript)
        payload = aead_decrypt(TICKET_AEAD_KEY, aad=transcript, blob=ticket_blob)
        if not payload.startswith(b"K_session:"):
            raise ValueError("bad ticket payload")
        K_session = payload.split(b":", 1)[1]
        return RedeemResp(K_session_b64=base64.b64encode(K_session).decode())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"redeem_failed: {e}")
