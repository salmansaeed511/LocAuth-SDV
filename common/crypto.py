from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from ecdsa import NIST256p, ellipticcurve, numbertheory
from hashlib import sha256

# ---------- ECDH + key utils (SECP256R1) ----------

def gen_ecdh_keypair() -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    priv = ec.generate_private_key(ec.SECP256R1())
    return priv, priv.public_key()

def ecdh_shared(priv: ec.EllipticCurvePrivateKey, peer_pub_bytes: bytes) -> bytes:
    pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), peer_pub_bytes)
    return priv.exchange(ec.ECDH(), pub)

def pubkey_bytes(pub: ec.EllipticCurvePublicKey) -> bytes:
    return pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint
    )

def hkdf(ikm: bytes, info: bytes = b"ECDDH-SDV", length: int = 32) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=None, info=info).derive(ikm)

def aead_encrypt(k: bytes, aad: bytes, plaintext: bytes) -> bytes:
    nonce = os.urandom(12)
    aead = ChaCha20Poly1305(k)
    ct = aead.encrypt(nonce, plaintext, aad)
    return nonce + ct

def aead_decrypt(k: bytes, aad: bytes, blob: bytes) -> bytes:
    nonce, ct = blob[:12], blob[12:]
    aead = ChaCha20Poly1305(k)
    return aead.decrypt(nonce, ct, aad)

# ---------- Schnorr ZKP over NIST256p (for proving knowledge of v) ----------

Curve = NIST256p
G = Curve.generator
n = Curve.order

def _int_to_bytes(x: int) -> bytes:
    return x.to_bytes(32, "big")

def _point_to_bytes(P) -> bytes:
    x = _int_to_bytes(P.x())
    y = P.y()
    prefix = b"\x03" if (y & 1) else b"\x02"
    return prefix + x

def _bytes_to_point(b: bytes):
    if len(b) != 33 or b[0] not in (2, 3):
        raise ValueError("invalid compressed point")
    x = int.from_bytes(b[1:], "big")
    curve = Curve.curve
    p = curve.p()
    a = curve.a()
    bcoef = curve.b()
    alpha = (pow(x, 3, p) + (a * x) + bcoef) % p
    beta = numbertheory.square_root_mod_prime(alpha, p)
    if beta is None:
        raise ValueError("no sqrt, invalid point")
    y = beta if (beta & 1) == (b[0] & 1) else (p - beta)
    return ellipticcurve.Point(curve, x, y, n)

@dataclass
class SchnorrProof:
    R: bytes  # commitment point (compressed)
    s: bytes  # response scalar (32 bytes)

def schnorr_prove(x: int, m: bytes):
    """Prover knows x; proves w.r.t. message m."""
    X = _point_to_bytes(x * G)
    k = int.from_bytes(os.urandom(32), "big") % n
    R_point = k * G
    R = _point_to_bytes(R_point)
    e = int.from_bytes(sha256(R + X + m).digest(), "big") % n
    s = (k + e * x) % n
    return X, SchnorrProof(R=R, s=_int_to_bytes(s))

def schnorr_verify(X_bytes: bytes, proof: SchnorrProof, m: bytes) -> bool:
    """Verifier checks proof for public X and message m."""
    try:
        X = _bytes_to_point(X_bytes)
        R = _bytes_to_point(proof.R)
        s = int.from_bytes(proof.s, "big") % n
        e = int.from_bytes(sha256(proof.R + X_bytes + m).digest(), "big") % n
        lhs = s * G
        rhs = R + e * X
        return lhs == rhs
    except Exception:
        return False

