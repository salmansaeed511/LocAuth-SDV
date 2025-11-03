from cryptography.hazmat.primitives import hashes, hmac

def tag_frame(K_session: bytes, header: bytes, payload: bytes, ctr: int) -> bytes:
    h = hmac.HMAC(K_session, hashes.SHA256())
    h.update(header + payload + ctr.to_bytes(8, 'big'))
    return h.finalize()

def verify_tag(K_session: bytes, header: bytes, payload: bytes, ctr: int, tag: bytes) -> bool:
    try:
        h = hmac.HMAC(K_session, hashes.SHA256())
        h.update(header + payload + ctr.to_bytes(8, 'big'))
        h.verify(tag)
        return True
    except Exception:
        return False
