from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from arc_mkii.artifact import load_artifact, save_artifact
from arc_mkii.corpus import build_training_rows
from arc_mkii.domain import Menu
from arc_mkii.fit import fit_theta
from arc_mkii.scramble import scramble_descriptor, scramble_feedback
from arc_mkii.selector import THETA0
from arc_mkii.v2_g2_protocol import RankedFamily
from arc_mkii.v2_g3_execution import iter_v2_training_rows
from arc_mkii.v2_g4_execution import (
    RootGeometry,
    V2EvalArena,
    build_scrambled_rows,
    conditional_tie_success,
    evaluate_v2_theta,
    load_eval_arenas,
    max_conditional_tie_success,
    tie_choice,
)


def _family_id(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _synthetic_eval() -> V2EvalArena:
    return V2EvalArena(
        rank=256,
        family_id=_family_id("synthetic-eval"),
        queries=(15, 23, 51, 85, 30, 45),
    )


def _synthetic_train() -> RankedFamily:
    return RankedFamily(
        rank=0,
        role="TRAIN",
        split_rank="00" * 32,
        family_id=_family_id("synthetic-train"),
        canonical_bytes_hex="0001020408102040",
        first_counter=0,
        queries=(1, 2, 4, 8, 16, 32),
    )


def test_v2_evaluator_preserves_family_id_without_recanonicalizing():
    arena = _synthetic_eval()
    result = evaluate_v2_theta("FROZEN", tuple(THETA0), (arena,))
    assert len(result.case_traces) == 16
    assert {case.canonical_task_id for case in result.case_traces} == {arena.family_id}
    assert set(result.success_by_budget) == {2, 3}
    assert all(set(case.selected_query_ids).issubset(set(range(6))) for case in result.case_traces)


def test_eval_loader_preserves_explicit_order_on_synthetic_fixture(tmp_path: Path):
    protocol = tmp_path / "protocol"
    protocol.mkdir()
    arena = _synthetic_eval()
    raw = {
        "rank": arena.rank,
        "role": "EVAL",
        "split_rank": "11" * 32,
        "family_id": arena.family_id,
        "canonical_bytes_hex": "0001020408102040",
        "first_counter": 1,
        "queries": list(arena.queries),
    }
    (protocol / "EVAL_ARENAS.jsonl").write_text(json.dumps(raw) + "\n", encoding="utf-8")
    loaded = load_eval_arenas(protocol, require_count=None)
    assert loaded == (arena,)

    raw["role"] = "TRAIN"
    (protocol / "EVAL_ARENAS.jsonl").write_text(json.dumps(raw) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="EVAL"):
        load_eval_arenas(protocol, require_count=None)


def test_v2_scrambled_adapter_is_semantically_identical_to_v0_on_public_fixture():
    rows = build_training_rows([Menu((15, 23, 51, 85))])
    descriptor = scramble_descriptor(rows)
    expected = scramble_feedback(rows)
    actual = build_scrambled_rows(rows, descriptor)  # runtime duck-typing is deliberate
    assert [row.row_id for row in actual] == [row.row_id for row in expected]
    assert [row.feedback for row in actual] == [row.feedback for row in expected]
    assert [row.features for row in actual] == [row.features for row in expected]


def test_unchanged_exact_fitter_accepts_v2_rows_and_artifact_round_trips(tmp_path: Path):
    rows = list(iter_v2_training_rows((_synthetic_train(),)))[:200]
    theta = fit_theta(rows)
    assert len(theta) == 8
    assert all(isinstance(value, Fraction) for value in theta)
    artifact = tmp_path / "theta.json"
    save_artifact(artifact, theta)
    assert load_artifact(artifact) == theta


def test_conditional_root_geometry_uses_exact_public_id_tie_rule():
    geometry = RootGeometry(
        family_id=_family_id("geometry-boundary"),
        tied_queries=(0, 1, 2),
        optimal_tied_queries=(2,),
        feature_pairs=(
            (0, (Fraction(0), Fraction(0))),
            (1, (Fraction(1), Fraction(0))),
            (2, (Fraction(1), Fraction(1))),
        ),
    )
    assert tie_choice((Fraction(0), Fraction(0)), geometry) == 0
    assert tie_choice((Fraction(1), Fraction(0)), geometry) == 1
    assert tie_choice((Fraction(1), Fraction(1)), geometry) == 2


def test_exact_c_tie_max_enumerates_sectors_boundaries_and_zero_without_float_grid():
    first = RootGeometry(
        family_id=_family_id("geometry-a"),
        tied_queries=(0, 1),
        optimal_tied_queries=(1,),
        feature_pairs=(
            (0, (Fraction(0), Fraction(0))),
            (1, (Fraction(1), Fraction(0))),
        ),
    )
    second = RootGeometry(
        family_id=_family_id("geometry-b"),
        tied_queries=(0, 1),
        optimal_tied_queries=(0,),
        feature_pairs=(
            (0, (Fraction(0), Fraction(0))),
            (1, (Fraction(0), Fraction(1))),
        ),
    )
    geometries = (first, second)
    assert conditional_tie_success((Fraction(1), Fraction(-1)), geometries) == 2
    assert max_conditional_tie_success(geometries) == 2
    assert max_conditional_tie_success(()) == 0


def test_g4_module_does_not_load_real_frozen_eval_at_import_time():
    # Importing the dormant result-capable module must not itself touch protocol data.
    import arc_mkii.v2_g4_execution as module

    assert module.EVAL_ARENA_COUNT == 64
    assert callable(module.execute_primary_result)
    assert callable(module.compute_root_autopsy)
