from __future__ import annotations
import base64, os, requests
from dataclasses import dataclass
from common.crypto import gen_ecdh_keypair, pubkey_bytes, ecdh_shared, hkdf, schnorr_prove, SchnorrProof

@dataclass
class HandshakeResult:
    K_session: bytes; ticket: bytes; transcript: bytes

def handshake(eas_url: str = "http://127.0.0.1:8000/hello") -> HandshakeResult:
    v_priv, v_pub = gen_ecdh_keypair()
    V_e_bytes = pubkey_bytes(v_pub)
    c_nonce = os.urandom(16)
    v_scalar = v_priv.private_numbers().private_value
    X_bytes, proof = schnorr_prove(v_scalar, m=c_nonce)
    assert V_e_bytes == X_bytes, "pub mismatch"
    payload = {
        "c_nonce": base64.b64encode(c_nonce).decode(),
        "V_e": base64.b64encode(V_e_bytes).decode(),
        "proof_R": base64.b64encode(proof.R).decode(),
        "proof_s": base64.b64encode(proof.s).decode(),
    }
    r = requests.post(eas_url, json=payload, timeout=5); r.raise_for_status()
    resp = r.json()
    E_e_bytes = base64.b64decode(resp["E_e"])
    transcript = c_nonce + V_e_bytes + E_e_bytes
    s1 = ecdh_shared(v_priv, E_e_bytes)
    K = hkdf(s1 + transcript, info=b"ECDDH-SDV-K")
    K_session = hkdf(K, info=b"ECDDH-SDV-session")
    ticket = base64.b64decode(resp["ticket"])
    return HandshakeResult(K_session=K_session, ticket=ticket, transcript=transcript)
