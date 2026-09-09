from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from arc_mkii.v2_census import CensusResult, FamilyRecord
from arc_mkii import v2_g1_cli


def _tiny_result() -> CensusResult:
    return CensusResult(
        raw_counters=1_048_576,
        grammar_valid=900_000,
        root_matched_tie=400_000,
        planner_gap=500,
        feature_representable=490,
        admitted_presentations=490,
        families=(
            FamilyRecord(
                family_id="a" * 64,
                canonical_bytes_hex="00010204090b1a2b",
                first_counter=7,
                queries=(16, 46, 89, 4, 45, 1),
            ),
        ),
    )


def test_g1_parser_exposes_only_census():
    parser = v2_g1_cli.build_parser()
    help_text = parser.format_help()
    assert "census" in help_text
    assert "fit" not in help_text
    assert "evaluate" not in help_text
    assert "train" not in help_text


def test_g1_cli_import_graph_excludes_learning_and_evaluation_modules():
    code = r'''
import sys
import arc_mkii.v2_g1_cli
forbidden = {
    "arc_mkii.fit",
    "arc_mkii.evaluate",
    "arc_mkii.corpus",
    "arc_mkii.scramble",
    "arc_mkii.artifact",
}
assert forbidden.isdisjoint(sys.modules), forbidden.intersection(sys.modules)
'''
    subprocess.run([sys.executable, "-c", code], check=True)


def test_census_command_writes_exact_deterministic_custody(tmp_path, monkeypatch):
    monkeypatch.setattr(v2_g1_cli, "run_census", lambda workers=4: _tiny_result())
    out = tmp_path / "g1"

    assert v2_g1_cli.main(["census", "--out", str(out)]) == 0
    assert {p.name for p in out.iterdir()} == {"CENSUS.json", "FAMILIES.jsonl", "SHA256.txt"}

    census_before = (out / "CENSUS.json").read_bytes()
    families_before = (out / "FAMILIES.jsonl").read_bytes()
    manifest_before = (out / "SHA256.txt").read_bytes()

    census = json.loads(census_before)
    assert census["schema"] == "arc-reactor-mkii-v2-g1-census/v0"
    assert census["preflight_base"] == "078b3cfc948262bb71604a631e17972f8ad11a1f"
    assert census["seed"] == "arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001"
    assert census["counts"]["admitted_canonical"] == 1
    assert census["status"] == "ARENA_UNIVERSE_INSUFFICIENT"

    parsed_hashes = {}
    for line in manifest_before.decode("ascii").splitlines():
        digest, name = line.split("  ", 1)
        parsed_hashes[name] = digest
    assert parsed_hashes == {
        "CENSUS.json": hashlib.sha256(census_before).hexdigest(),
        "FAMILIES.jsonl": hashlib.sha256(families_before).hexdigest(),
    }

    def forbidden_rerun(*args, **kwargs):
        raise AssertionError("validated custody should not rerun census")

    monkeypatch.setattr(v2_g1_cli, "run_census", forbidden_rerun)
    assert v2_g1_cli.main(["census", "--out", str(out)]) == 0
    assert (out / "CENSUS.json").read_bytes() == census_before
    assert (out / "FAMILIES.jsonl").read_bytes() == families_before
    assert (out / "SHA256.txt").read_bytes() == manifest_before


def test_existing_custody_fails_closed_on_tamper(tmp_path, monkeypatch):
    monkeypatch.setattr(v2_g1_cli, "run_census", lambda workers=4: _tiny_result())
    out = tmp_path / "g1"
    assert v2_g1_cli.main(["census", "--out", str(out)]) == 0
    (out / "CENSUS.json").write_bytes((out / "CENSUS.json").read_bytes() + b"\n")
    with pytest.raises(ValueError, match="custody"):
        v2_g1_cli.main(["census", "--out", str(out)])
