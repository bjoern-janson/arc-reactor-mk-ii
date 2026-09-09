import hashlib
import json
from pathlib import Path

import pytest

from arc_mkii.artifact import load_artifact, save_artifact
from arc_mkii.canonical import canonical_id
from arc_mkii.cli import build_parser, main
from arc_mkii.corpus import build_training_rows
from arc_mkii.domain import Menu
from arc_mkii.manifests import protocol_record
from arc_mkii.scramble import scramble_descriptor
from arc_mkii.selector import THETA0


def test_cli_has_separate_protocol_fit_and_evaluate_commands():
    parser = build_parser()
    help_text = parser.format_help()
    assert "freeze-protocol" in help_text
    assert "fit" in help_text
    assert "evaluate" in help_text


def test_freeze_protocol_writes_expected_files_and_is_byte_idempotent(tmp_path):
    out = tmp_path / "protocol"
    assert main(["freeze-protocol", "--out", str(out)]) == 0
    expected = {
        "PROTOCOL.json",
        "TRAIN_MENUS.jsonl",
        "EVAL_MENUS.jsonl",
        "SCRAMBLE.json",
        "MANIFEST_SHA256.txt",
    }
    assert {p.name for p in out.iterdir()} == expected
    before = {name: (out / name).read_bytes() for name in expected}
    assert main(["freeze-protocol", "--out", str(out)]) == 0
    after = {name: (out / name).read_bytes() for name in expected}
    assert after == before

    manifest_lines = (out / "MANIFEST_SHA256.txt").read_text().splitlines()
    hashes = dict(line.split("  ", 1)[::-1] for line in manifest_lines)
    for name in ("EVAL_MENUS.jsonl", "PROTOCOL.json", "SCRAMBLE.json", "TRAIN_MENUS.jsonl"):
        assert hashes[name] == hashlib.sha256((out / name).read_bytes()).hexdigest()


def _write_minimal_protocol(protocol: Path) -> None:
    protocol.mkdir()
    menu = Menu((15, 23, 51, 85))
    meta = protocol_record()
    meta["train_count"] = 1
    meta["eval_count"] = 1
    protocol_bytes = (json.dumps(meta, sort_keys=True, separators=(",", ":")) + "\n").encode()
    menu_bytes = (
        json.dumps(
            {"canonical_id": canonical_id(menu), "queries": list(menu.queries)},
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()
    scramble_bytes = (
        json.dumps(
            scramble_descriptor(build_training_rows([menu])),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()
    payloads = {
        "PROTOCOL.json": protocol_bytes,
        "TRAIN_MENUS.jsonl": menu_bytes,
        "EVAL_MENUS.jsonl": menu_bytes,
        "SCRAMBLE.json": scramble_bytes,
    }
    for name, content in payloads.items():
        (protocol / name).write_bytes(content)
    (protocol / "MANIFEST_SHA256.txt").write_text(
        "".join(
            f"{hashlib.sha256(payloads[name]).hexdigest()}  {name}\n"
            for name in sorted(payloads)
        ),
        encoding="ascii",
    )


def test_fit_learn_verifies_full_protocol_but_consumes_training_rows(tmp_path):
    protocol = tmp_path / "protocol"
    _write_minimal_protocol(protocol)
    eval_before = (protocol / "EVAL_MENUS.jsonl").read_bytes()
    out = tmp_path / "learn.json"
    assert main(["fit", "--protocol", str(protocol), "--arm", "learn", "--out", str(out)]) == 0
    theta = load_artifact(out)
    assert len(theta) == 8
    receipt = json.loads((tmp_path / "learn.json.receipt.json").read_text())
    assert receipt["arm"] == "learn"
    assert receipt["training_row_count"] > 0
    assert receipt["artifact_sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert receipt["protocol_manifest_sha256"] == hashlib.sha256(
        (protocol / "MANIFEST_SHA256.txt").read_bytes()
    ).hexdigest()
    assert (protocol / "EVAL_MENUS.jsonl").read_bytes() == eval_before


def test_fit_frozen_serializes_theta0_without_consuming_training_rows(tmp_path):
    protocol = tmp_path / "protocol"
    _write_minimal_protocol(protocol)
    out = tmp_path / "frozen.json"
    assert main(["fit", "--protocol", str(protocol), "--arm", "frozen", "--out", str(out)]) == 0
    assert load_artifact(out) == tuple(THETA0)
    receipt = json.loads((tmp_path / "frozen.json.receipt.json").read_text())
    assert receipt["training_row_count"] == 0


def test_fit_scrambled_uses_the_committed_scramble_descriptor(tmp_path):
    protocol = tmp_path / "protocol"
    _write_minimal_protocol(protocol)
    out = tmp_path / "scrambled.json"
    assert main(["fit", "--protocol", str(protocol), "--arm", "scrambled", "--out", str(out)]) == 0
    assert len(load_artifact(out)) == 8
    receipt = json.loads((tmp_path / "scrambled.json.receipt.json").read_text())
    assert receipt["arm"] == "scrambled"
    assert receipt["training_row_count"] > 0


def test_fit_fails_closed_if_frozen_eval_payload_is_tampered(tmp_path):
    protocol = tmp_path / "protocol"
    _write_minimal_protocol(protocol)
    (protocol / "EVAL_MENUS.jsonl").write_bytes(
        (protocol / "EVAL_MENUS.jsonl").read_bytes() + b"\n"
    )
    with pytest.raises(ValueError, match="protocol hash mismatch"):
        main([
            "fit",
            "--protocol", str(protocol),
            "--arm", "frozen",
            "--out", str(tmp_path / "frozen.json"),
        ])


def test_evaluate_is_read_only_and_writes_exact_paired_outputs(tmp_path, monkeypatch):
    protocol = tmp_path / "protocol"
    _write_minimal_protocol(protocol)
    learn = tmp_path / "learn.json"
    scrambled = tmp_path / "scrambled.json"
    frozen = tmp_path / "frozen.json"
    for path in (learn, scrambled, frozen):
        save_artifact(path, THETA0)

    def forbidden_fit(*args, **kwargs):
        raise AssertionError("evaluate must not fit")

    monkeypatch.setattr("arc_mkii.cli.fit_theta", forbidden_fit)
    out = tmp_path / "evaluation"
    assert main([
        "evaluate",
        "--protocol", str(protocol),
        "--learn", str(learn),
        "--scrambled", str(scrambled),
        "--frozen", str(frozen),
        "--out", str(out),
    ]) == 0

    assert {p.name for p in out.iterdir()} == {
        "SUMMARY.json",
        "LEARN_CASES.jsonl",
        "SCRAMBLED_CASES.jsonl",
        "FROZEN_CASES.jsonl",
        "PLANNER_REFERENCE.jsonl",
        "RESOURCES.json",
        "TRANSPLANT.json",
    }
    summary = json.loads((out / "SUMMARY.json").read_text())
    assert summary["ignition_pass"] is False
    assert set(summary["success_by_budget"]) == {"2", "3"}
    assert summary["protocol_manifest_sha256"] == hashlib.sha256(
        (protocol / "MANIFEST_SHA256.txt").read_bytes()
    ).hexdigest()
    transplant = json.loads((out / "TRANSPLANT.json").read_text())
    assert transplant["all_pass"] is True


def test_evaluate_fails_closed_before_loading_artifacts_if_protocol_is_tampered(tmp_path):
    protocol = tmp_path / "protocol"
    _write_minimal_protocol(protocol)
    (protocol / "TRAIN_MENUS.jsonl").write_bytes(
        (protocol / "TRAIN_MENUS.jsonl").read_bytes() + b"\n"
    )
    with pytest.raises(ValueError, match="protocol hash mismatch"):
        main([
            "evaluate",
            "--protocol", str(protocol),
            "--learn", str(tmp_path / "missing-learn.json"),
            "--scrambled", str(tmp_path / "missing-scrambled.json"),
            "--frozen", str(tmp_path / "missing-frozen.json"),
            "--out", str(tmp_path / "evaluation"),
        ])
