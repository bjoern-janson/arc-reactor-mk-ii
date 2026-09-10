from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from arc_mkii.corpus import build_training_rows
from arc_mkii.domain import Menu, SixQueryArena
from arc_mkii.v2_g2_protocol import (
    EVAL_COUNT,
    EXPECTED_G1_CENSUS_SHA256,
    EXPECTED_G1_FAMILIES_SHA256,
    OUTSIDE_COUNT,
    TRAIN_COUNT,
    FamilyInput,
    freeze_v2_protocol,
    load_g1_custody,
    rank_families,
    row_id_from_fields,
    scramble_descriptor_for_train,
    split_families,
    split_rank,
    training_row_identity_records,
    verify_v2_protocol,
)


def _family(index: int) -> FamilyInput:
    family_id = hashlib.sha256(f"family-{index}".encode()).hexdigest()
    queries = tuple(1 + ((index * 11 + slot * 17) % 127) for slot in range(6))
    if len(set(queries)) != 6:
        queries = (1, 2, 3, 4, 5, 6)
    return FamilyInput(
        canonical_bytes_hex=f"{index:016x}"[-16:],
        family_id=family_id,
        first_counter=index,
        queries=queries,
    )


def test_frozen_g1_hash_constants():
    assert EXPECTED_G1_CENSUS_SHA256 == "d0959d5794f3d398cae226050f48c2e68b8032819991536b9aadbdc8683dcd54"
    assert EXPECTED_G1_FAMILIES_SHA256 == "213a5133208c1f4ca19edd500e9f68b40ef13ed47959fdc2921a4daf3e951057"


def test_split_rank_uses_frozen_prefix():
    family_id = "00" * 32
    expected = hashlib.sha256(
        b"arc-mkii-v2-six-query-gladiator-split\0" + family_id.encode("ascii")
    ).hexdigest()
    assert split_rank(family_id) == expected


def test_split_counts_and_rank_order_are_frozen():
    split = split_families(tuple(_family(i) for i in range(436)))
    assert len(split.train) == TRAIN_COUNT == 256
    assert len(split.eval) == EVAL_COUNT == 64
    assert len(split.outside) == OUTSIDE_COUNT == 116
    assert [row.rank for row in split.all_rows] == list(range(436))
    assert list(split.all_rows) == sorted(split.all_rows, key=lambda row: (row.split_rank, row.family_id))
    assert all(row.role == "TRAIN" for row in split.train)
    assert all(row.role == "EVAL" for row in split.eval)
    assert all(row.role == "OUTSIDE_CONFIRMATORY_V2" for row in split.outside)


def test_split_rejects_duplicate_or_malformed_family_identity():
    record = _family(1)
    with pytest.raises(ValueError, match="duplicate family_id"):
        rank_families((record, record))
    with pytest.raises(ValueError, match="family_id"):
        rank_families((FamilyInput("00", "not-hex", 1, (1, 2, 3, 4, 5, 6)),))


def test_row_id_serializer_is_byte_compatible_with_v0_training_row():
    menu = Menu((15, 23, 51, 85))
    row = build_training_rows([menu])[0]
    actual = row_id_from_fields(
        canonical_task_id=row.canonical_task_id,
        query_masks=row.query_masks,
        budget=row.budget,
        fault=row.fault,
        planned_sequence=row.planned_sequence,
        decision_depth=row.decision_depth,
        candidate_mask=row.candidate_mask,
        remaining_query_ids=row.remaining_query_ids,
        action_query_id=row.action_query_id,
        features=row.features,
        terminal_repair=row.terminal_repair,
    )
    assert actual == row.row_id


def test_v2_training_row_identity_binds_canonical_task_id_to_family_id():
    family = FamilyInput(
        canonical_bytes_hex="0001020408102040",
        family_id=hashlib.sha256(b"task-id-binding").hexdigest(),
        first_counter=1,
        queries=(1, 2, 4, 8, 16, 32),
    )
    ranked = rank_families((family,))
    first = next(iter(training_row_identity_records(ranked)))
    assert first.canonical_task_id == family.family_id


def test_six_query_scramble_descriptor_preserves_v0_strata_shape():
    arena = SixQueryArena((1, 2, 4, 8, 16, 32))
    ranked = rank_families((
        FamilyInput("0001020408102040", hashlib.sha256(b"tiny").hexdigest(), 1, arena.queries),
    ))
    descriptor = scramble_descriptor_for_train(ranked)
    assert descriptor["schema"] == "arc-reactor-mkii-scramble/v0"
    strata = {(item["budget"], item["decision_depth"]): item for item in descriptor["strata"]}
    assert set(strata) == {(2, 0), (2, 1), (3, 0), (3, 1), (3, 2)}
    assert all(item["size"] > 0 for item in strata.values())
    assert all(len(item["row_ids_sha256"]) == 64 for item in strata.values())


def _write_fake_g1(root: Path, records: list[FamilyInput]) -> None:
    root.mkdir(parents=True)
    census = {
        "schema": "arc-reactor-mkii-v2-g1-census/v0",
        "preflight_base": "078b3cfc948262bb71604a631e17972f8ad11a1f",
        "implementation_commit": "9ba2e6e8ad448e72702ade6af23f4a1a25fbe932",
        "seed": "arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001",
        "raw_counter_count": 1048576,
        "canonical_threshold": 320,
        "status": "G1_PASS",
        "counts": {"admitted_canonical": 436},
    }
    census_bytes = (json.dumps(census, sort_keys=True, separators=(",", ":")) + "\n").encode()
    family_bytes = b"".join(
        (json.dumps({
            "canonical_bytes_hex": row.canonical_bytes_hex,
            "family_id": row.family_id,
            "first_counter": row.first_counter,
            "queries": list(row.queries),
        }, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for row in records
    )
    (root / "CENSUS.json").write_bytes(census_bytes)
    (root / "FAMILIES.jsonl").write_bytes(family_bytes)
    (root / "SHA256.txt").write_text(
        f"{hashlib.sha256(census_bytes).hexdigest()}  CENSUS.json\n"
        f"{hashlib.sha256(family_bytes).hexdigest()}  FAMILIES.jsonl\n",
        encoding="ascii",
    )


def test_real_g1_loader_fails_closed_if_payload_hashes_do_not_match(tmp_path):
    root = tmp_path / "g1"
    _write_fake_g1(root, [_family(i) for i in range(436)])
    with pytest.raises(ValueError, match="G1 custody hash mismatch"):
        load_g1_custody(root)


def test_g2_module_import_graph_excludes_fit_evaluate_and_census():
    code = r'''
import sys
import arc_mkii.v2_g2_cli
forbidden = {
    "arc_mkii.fit",
    "arc_mkii.evaluate",
    "arc_mkii.v2_census",
}
assert forbidden.isdisjoint(sys.modules), forbidden.intersection(sys.modules)
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    subprocess.run([sys.executable, "-c", code], check=True, env=env)


def test_freeze_and_verify_exact_protocol_on_real_g1(tmp_path):
    repo_g1 = Path("experiments/v2/g1-census")
    if not repo_g1.exists():
        pytest.skip("repository G1 custody not available")
    out = tmp_path / "protocol"
    freeze_v2_protocol(repo_g1, out)
    verification = verify_v2_protocol(repo_g1, out)
    assert verification.train_count == 256
    assert verification.eval_count == 64
    assert verification.outside_count == 116
    assert len(verification.manifest_sha256) == 64
    assert {path.name for path in out.iterdir()} == {
        "PROTOCOL.json",
        "TRAIN_ARENAS.jsonl",
        "EVAL_ARENAS.jsonl",
        "OUTSIDE_CONFIRMATORY.jsonl",
        "SPLIT_RANKS.jsonl",
        "SCRAMBLE.json",
        "ROOT_AUTOPSY_CONTRACT.json",
        "MANIFEST_SHA256.txt",
    }
    protocol = json.loads((out / "PROTOCOL.json").read_text())
    assert protocol["schema"] == "arc-reactor-mkii-v2-protocol/v0"
    assert protocol["canonical_task_identity"] == "family_id"
    assert protocol["root_autopsy_status"] == "POST_G1_PRE_G4_UNEVALUATED_NONACCEPTANCE"

    autopsy = json.loads((out / "ROOT_AUTOPSY_CONTRACT.json").read_text())
    assert autopsy["status"] == "POST_G1_PRE_G4_UNEVALUATED_NONACCEPTANCE"
    assert set(autopsy["diagnostics"]) == {
        "C_tie_max",
        "C_tie_learn",
        "T_retention_learn",
        "C_actual_learn",
    }
    assert all(value == "UNEVALUATED" for value in autopsy["diagnostics"].values())
    assert "values" not in autopsy

    forbidden_output_tokens = {
        '"theta":',
        '"ignition_pass":',
        '"success_by_budget":',
        '"diagnostic_value":',
        '"evaluated_value":',
    }
    for path in out.iterdir():
        if path.suffix in {".json", ".jsonl"}:
            text = path.read_text(encoding="utf-8")
            assert all(token not in text for token in forbidden_output_tokens)

    before = {path.name: path.read_bytes() for path in out.iterdir()}
    freeze_v2_protocol(repo_g1, out)
    after = {path.name: path.read_bytes() for path in out.iterdir()}
    assert after == before

    (out / "PROTOCOL.json").write_bytes((out / "PROTOCOL.json").read_bytes() + b"\n")
    with pytest.raises(ValueError, match="protocol hash mismatch"):
        verify_v2_protocol(repo_g1, out)
