from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from arc_mkii.domain import SixQueryArena
from arc_mkii.v2_g2_protocol import RankedFamily, training_row_identity_records
from arc_mkii.v2_g3_execution import (
    DESIGN_FREEZE_ID_V2_G3,
    EXPECTED_G2_MANIFEST_SHA256,
    G2_RECORD_ID,
    EXPECTED_TRAIN_ROWS,
    EXPECTED_TRAIN_STRATA,
    V2TrainingRow,
    iter_v2_training_rows,
    load_train_arenas,
    verify_frozen_g2_protocol,
    verify_train_corpus_against_scramble,
)


G2_PROTOCOL = Path("experiments/v2/protocol")


def _synthetic_ranked_family() -> RankedFamily:
    return RankedFamily(
        rank=0,
        role="TRAIN",
        split_rank="00" * 32,
        family_id=hashlib.sha256(b"g3-synthetic-family").hexdigest(),
        canonical_bytes_hex="0001020408102040",
        first_counter=0,
        queries=(1, 2, 4, 8, 16, 32),
    )


def test_g3_provenance_constants_are_frozen():
    assert G2_RECORD_ID == "5689645287c41a71e109f1b022529e8b98f2006d"
    assert EXPECTED_G2_MANIFEST_SHA256 == "419b7be408a5a37ab6a7ee304ac58646683a6fc4771b503e0b0f475002b4d075"
    assert DESIGN_FREEZE_ID_V2_G3 == "b6d520eafd81b367c81c145d05c4702dac94b74c"
    assert EXPECTED_TRAIN_ROWS == 817_105
    assert EXPECTED_TRAIN_STRATA == {
        (2, 0): {
            "size": 61_440,
            "offset": 26_027,
            "row_ids_sha256": "0bcc9fe377e1f0aa573865d7305022cefd622d40ee452f1f7d912ad5a0ed3654",
        },
        (2, 1): {
            "size": 60_805,
            "offset": 11_302,
            "row_ids_sha256": "71132d31d6cefcf5c2d236275a6cec2d9bc1573cad785e8dc4bcb521afdc595b",
        },
        (3, 0): {
            "size": 245_760,
            "offset": 167_833,
            "row_ids_sha256": "71eac513f895ebe9a39a8300acc54dc00ed62d8614936e0c99b4e21d021178e5",
        },
        (3, 1): {
            "size": 243_220,
            "offset": 12_092,
            "row_ids_sha256": "5cddc338d1ecd2d5bd17f3a4eaa676104ffa4e7d3042e416506ee1f6309e0925",
        },
        (3, 2): {
            "size": 205_880,
            "offset": 92_488,
            "row_ids_sha256": "e498c5667a0af60001c1acdb23618847512ad606e147f0e9b403768c956cc488",
        },
    }


def test_g3_import_graph_excludes_result_bearing_modules():
    code = r'''
import sys
import arc_mkii.v2_g3_cli
forbidden = {
    "arc_mkii.fit",
    "arc_mkii.evaluate",
    "arc_mkii.artifact",
    "arc_mkii.v2_g4_execution",
}
assert forbidden.isdisjoint(sys.modules), forbidden.intersection(sys.modules)
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    subprocess.run([sys.executable, "-c", code], check=True, env=env)


def test_v2_training_rows_preserve_g2_identity_and_add_terminal_feedback_only():
    ranked = _synthetic_ranked_family()
    identity = next(training_row_identity_records((ranked,)))
    row = next(iter_v2_training_rows((ranked,)))
    assert isinstance(row, V2TrainingRow)
    assert row.row_id == identity.row_id
    assert row.canonical_task_id == ranked.family_id
    assert row.query_masks == ranked.queries
    assert len(row.query_masks) == 6
    assert row.budget == identity.budget
    assert row.fault == identity.fault
    assert row.planned_sequence == identity.planned_sequence
    assert row.decision_depth == identity.decision_depth
    assert row.candidate_mask == identity.candidate_mask
    assert row.remaining_query_ids == identity.remaining_query_ids
    assert row.action_query_id == identity.action_query_id
    assert row.features == identity.features
    assert row.terminal_repair == identity.terminal_repair
    assert row.feedback == int(row.terminal_repair == row.fault)


def test_train_loader_requires_frozen_family_identity_and_six_query_order(tmp_path):
    protocol = tmp_path / "protocol"
    protocol.mkdir()
    record = {
        "rank": 0,
        "role": "TRAIN",
        "split_rank": "11" * 32,
        "family_id": hashlib.sha256(b"loader").hexdigest(),
        "canonical_bytes_hex": "0001020408102040",
        "first_counter": 0,
        "queries": [58, 59, 96, 12, 30, 106],
    }
    (protocol / "TRAIN_ARENAS.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    rows = load_train_arenas(protocol, require_count=None)
    assert len(rows) == 1
    assert rows[0].family_id == record["family_id"]
    assert rows[0].queries == tuple(record["queries"])
    assert SixQueryArena(rows[0].queries).queries == tuple(record["queries"])

    record["role"] = "EVAL"
    (protocol / "TRAIN_ARENAS.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="TRAIN"):
        load_train_arenas(protocol, require_count=None)


def test_frozen_g2_protocol_verification_binds_manifest_and_unevaluated_autopsy():
    verification = verify_frozen_g2_protocol(G2_PROTOCOL)
    assert verification.manifest_sha256 == EXPECTED_G2_MANIFEST_SHA256
    assert verification.train_count == 256
    assert verification.eval_count == 64
    assert verification.outside_count == 116
    assert verification.root_autopsy_values_present is False


def test_real_v2_train_corpus_matches_all_frozen_scramble_custody():
    report = verify_train_corpus_against_scramble(G2_PROTOCOL)
    assert report.total_rows == EXPECTED_TRAIN_ROWS
    assert report.strata == EXPECTED_TRAIN_STRATA
    assert report.fit_performed is False
    assert report.eval_performed is False
    assert report.autopsy_performed is False
    assert report.ignition_computed is False
