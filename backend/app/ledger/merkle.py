import hashlib
from typing import Sequence


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def build_merkle_root(hashes: Sequence[str]) -> str:
    if not hashes:
        return "0" * 64
    layer = [bytes.fromhex(h) for h in hashes]
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [sha256(layer[i] + layer[i + 1]) for i in range(0, len(layer), 2)]
    return layer[0].hex()


def merkle_proof(hashes: Sequence[str], index: int) -> list[dict]:
    layer = [bytes.fromhex(h) for h in hashes]
    proof: list[dict] = []
    idx = index
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        sibling_idx = idx ^ 1
        proof.append({"hash": layer[sibling_idx].hex(), "position": "right" if idx % 2 == 0 else "left"})
        layer = [sha256(layer[i] + layer[i + 1]) for i in range(0, len(layer), 2)]
        idx //= 2
    return proof