from arc_mkii.cli import build_parser


def test_cli_has_separate_protocol_fit_and_evaluate_commands():
    parser = build_parser()
    help_text = parser.format_help()
    assert "freeze-protocol" in help_text
    assert "fit" in help_text
    assert "evaluate" in help_text

import hashlib
from pathlib import Path

from arc_mkii.cli import main


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

import json

from arc_mkii.artifact import load_artifact
from arc_mkii.canonical import canonical_id
from arc_mkii.corpus import build_training_rows
from arc_mkii.domain import Menu
from arc_mkii.manifests import protocol_record
from arc_mkii.scramble import scramble_descriptor
from arc_mkii.selector import THETA0


def _write_minimal_protocol(protocol: Path) -> None:
    protocol.mkdir()
    menu = Menu((15, 23, 51, 85))
    protocol_bytes = (json.dumps(protocol_record(), sort_keys=True, separators=(",", ":")) + "\n").encode()
    train_bytes = (json.dumps({"canonical_id": canonical_id(menu), "queries": list(menu.queries)}, sort_keys=True, separators=(",", ":")) + "\n").encode()
    scramble_bytes = (json.dumps(scramble_descriptor(build_training_rows([menu])), sort_keys=True, separators=(",", ":")) + "\n").encode()
    (protocol / "PROTOCOL.json").write_bytes(protocol_bytes)
    (protocol / "TRAIN_MENUS.jsonl").write_bytes(train_bytes)
    (protocol / "SCRAMBLE.json").write_bytes(scramble_bytes)
    (protocol / "EVAL_MENUS.jsonl").mkdir()
    lines = [
        f"{hashlib.sha256(protocol_bytes).hexdigest()}  PROTOCOL.json\n",
        f"{hashlib.sha256(train_bytes).hexdigest()}  TRAIN_MENUS.jsonl\n",
        f"{hashlib.sha256(scramble_bytes).hexdigest()}  SCRAMBLE.json\n",
        f"{'0' * 64}  EVAL_MENUS.jsonl\n",
    ]
    (protocol / "MANIFEST_SHA256.txt").write_text("".join(sorted(lines)))


def test_fit_learn_uses_training_side_only_and_writes_minimal_artifact_receipt(tmp_path):
    protocol = tmp_path / "protocol"
    _write_minimal_protocol(protocol)
    out = tmp_path / "learn.json"
    assert main(["fit", "--protocol", str(protocol), "--arm", "learn", "--out", str(out)]) == 0
    theta = load_artifact(out)
    assert len(theta) == 8
    receipt = json.loads((tmp_path / "learn.json.receipt.json").read_text())
    assert receipt["arm"] == "learn"
    assert receipt["training_row_count"] > 0
    assert receipt["artifact_sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert (protocol / "EVAL_MENUS.jsonl").is_dir()


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

from arc_mkii.artifact import save_artifact


def _write_minimal_eval_protocol(protocol: Path) -> None:
    protocol.mkdir()
    menu = Menu((15, 23, 51, 85))
    (protocol / "PROTOCOL.json").write_bytes(
        (json.dumps(protocol_record(), sort_keys=True, separators=(",", ":")) + "\n").encode()
    )
    (protocol / "EVAL_MENUS.jsonl").write_bytes(
        (json.dumps({"canonical_id": canonical_id(menu), "queries": list(menu.queries)}, sort_keys=True, separators=(",", ":")) + "\n").encode()
    )


def test_evaluate_is_read_only_and_writes_exact_paired_outputs(tmp_path, monkeypatch):
    protocol = tmp_path / "protocol"
    _write_minimal_eval_protocol(protocol)
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
    transplant = json.loads((out / "TRANSPLANT.json").read_text())
    assert transplant["all_pass"] is True
