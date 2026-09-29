from __future__ import annotations
import base64
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from app.config import settings

KEYS_DIR = Path(settings.keys_dir)
PRIVATE_KEY_PATH = KEYS_DIR / "ledger_ed25519"
PUBLIC_KEY_PATH = KEYS_DIR / "ledger_ed25519.pub"


class Signer:
    def __init__(self) -> None:
        KEYS_DIR.mkdir(parents=True, exist_ok=True)
        if PRIVATE_KEY_PATH.exists():
            raw = PRIVATE_KEY_PATH.read_bytes()
            self._private = Ed25519PrivateKey.from_private_bytes(raw)
        else:
            self._private = Ed25519PrivateKey.generate()
            PRIVATE_KEY_PATH.write_bytes(
                self._private.private_bytes(
                    serialization.Encoding.Raw,
                    serialization.PrivateFormat.Raw,
                    serialization.NoEncryption(),
                )
            )
            pub = self._private.public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw
            )
            PUBLIC_KEY_PATH.write_bytes(pub)

        pub_bytes = self._private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        self.pubkey_id = hashlib.sha256(pub_bytes).hexdigest()[:16]
        self._public = self._private.public_key()

    def sign(self, data: bytes) -> str:
        sig = self._private.sign(data)
        return base64.b64encode(sig).decode()

    def verify(self, data: bytes, sig_b64: str) -> bool:
        try:
            sig = base64.b64decode(sig_b64)
            self._public.verify(sig, data)
            return True
        except Exception:
            return False