import hashlib
import json
from pathlib import Path

import pytest

from arc_mkii.protocol import verify_protocol


def _write_protocol(
    root: Path,
    *,
    train_lines: int = 2,
    eval_lines: int = 1,
    train_count: int = 2,
    eval_count: int = 1,
) -> None:
    root.mkdir()
    payloads = {
        "PROTOCOL.json": (
            json.dumps(
                {
                    "schema": "arc-reactor-mkii-protocol/v0",
                    "train_count": train_count,
                    "eval_count": eval_count,
                }
            )
            + "\n"
        ).encode(),
        "TRAIN_MENUS.jsonl": ("{}\n" * train_lines).encode(),
        "EVAL_MENUS.jsonl": ("{}\n" * eval_lines).encode(),
        "SCRAMBLE.json": b"{}\n",
    }
    for name, data in payloads.items():
        (root / name).write_bytes(data)
    manifest = "".join(
        f"{hashlib.sha256(payloads[name]).hexdigest()}  {name}\n"
        for name in sorted(payloads)
    )
    (root / "MANIFEST_SHA256.txt").write_text(manifest, encoding="ascii")


def test_verify_protocol_accepts_exact_manifest_and_returns_manifest_digest(tmp_path):
    root = tmp_path / "protocol"
    _write_protocol(root)
    result = verify_protocol(root)
    assert result.hashes["EVAL_MENUS.jsonl"] == hashlib.sha256(
        (root / "EVAL_MENUS.jsonl").read_bytes()
    ).hexdigest()
    assert result.manifest_sha256 == hashlib.sha256(
        (root / "MANIFEST_SHA256.txt").read_bytes()
    ).hexdigest()


def test_verify_protocol_rejects_payload_tampering(tmp_path):
    root = tmp_path / "protocol"
    _write_protocol(root)
    (root / "EVAL_MENUS.jsonl").write_text("tampered\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_protocol(root)


def test_verify_protocol_rejects_unexpected_file(tmp_path):
    root = tmp_path / "protocol"
    _write_protocol(root)
    (root / "extra.txt").write_text("x")
    with pytest.raises(ValueError, match="file set"):
        verify_protocol(root)


def test_verify_protocol_rejects_count_mismatch_even_when_hashes_match(tmp_path):
    root = tmp_path / "protocol"
    _write_protocol(root, eval_lines=1, eval_count=2)
    with pytest.raises(ValueError, match="eval_count"):
        verify_protocol(root)
