from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

_PAYLOAD_FILES = {
    "PROTOCOL.json",
    "TRAIN_MENUS.jsonl",
    "EVAL_MENUS.jsonl",
    "SCRAMBLE.json",
}
_EXPECTED_FILES = _PAYLOAD_FILES | {"MANIFEST_SHA256.txt"}


@dataclass(frozen=True)
class ProtocolVerification:
    hashes: dict[str, str]
    manifest_sha256: str


def _nonempty_line_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)


def verify_protocol(protocol: str | Path) -> ProtocolVerification:
    protocol = Path(protocol)
    if not protocol.is_dir():
        raise ValueError(f"protocol directory does not exist: {protocol}")

    names = {path.name for path in protocol.iterdir()}
    if names != _EXPECTED_FILES:
        raise ValueError("protocol file set mismatch")

    recorded: dict[str, str] = {}
    for line in (protocol / "MANIFEST_SHA256.txt").read_text(encoding="ascii").splitlines():
        try:
            digest, name = line.split("  ", 1)
        except ValueError as exc:
            raise ValueError("malformed protocol manifest line") from exc
        if name in recorded:
            raise ValueError(f"duplicate protocol manifest entry: {name}")
        if len(digest) != 64:
            raise ValueError(f"invalid protocol manifest digest for {name}")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise ValueError(f"invalid protocol manifest digest for {name}") from exc
        recorded[name] = digest.lower()

    if set(recorded) != _PAYLOAD_FILES:
        raise ValueError("protocol manifest file set mismatch")

    for name in sorted(_PAYLOAD_FILES):
        actual = hashlib.sha256((protocol / name).read_bytes()).hexdigest()
        if actual != recorded[name]:
            raise ValueError(f"protocol hash mismatch: {name}")

    meta = json.loads((protocol / "PROTOCOL.json").read_text(encoding="utf-8"))
    if meta.get("schema") != "arc-reactor-mkii-protocol/v0":
        raise ValueError("protocol schema mismatch")

    for key, filename in (
        ("train_count", "TRAIN_MENUS.jsonl"),
        ("eval_count", "EVAL_MENUS.jsonl"),
    ):
        expected = meta.get(key)
        if not isinstance(expected, int) or expected < 0:
            raise ValueError(f"invalid protocol {key}")
        actual = _nonempty_line_count(protocol / filename)
        if actual != expected:
            raise ValueError(f"protocol {key} mismatch: expected {expected}, got {actual}")

    return ProtocolVerification(
        hashes=dict(recorded),
        manifest_sha256=hashlib.sha256((protocol / "MANIFEST_SHA256.txt").read_bytes()).hexdigest(),
    )
