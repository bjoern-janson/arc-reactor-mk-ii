from __future__ import annotations

import hashlib
import json
import math
import time
import tracemalloc
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
from functools import cmp_to_key
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence

from .artifact import load_artifact, save_artifact
from .domain import FULL_MASK, SixQueryArena
from .evaluate import CaseTrace, DecisionTrace, EvaluationResult, ignition_pass
from .fit import fit_theta
from .host import execute_query, initial_state, terminal_repair
from .resources import ResourceCounter
from .selector import THETA0, choose_from_scores, query_scores
from .v2_g3_execution import (
    EXPECTED_G2_MANIFEST_SHA256,
    V2TrainingRow,
    iter_v2_training_rows,
    load_train_arenas,
    verify_frozen_g2_protocol,
    verify_train_corpus_against_scramble,
)

PRIMARY_SCHEMA = "arc-reactor-mkii-v2-g4-primary/v0"
AUTOPSY_SCHEMA = "arc-reactor-mkii-v2-g4-root-autopsy/v0"
FIT_RECEIPT_SCHEMA = "arc-reactor-mkii-v2-fit-receipt/v0"
EVAL_ARENA_COUNT = 64
ROW_ID_LIST_PREFIX = b"arc-mkii-row-id-list-v0\0"
_ARENA_KEYS = {
    "rank",
    "role",
    "split_rank",
    "family_id",
    "canonical_bytes_hex",
    "first_counter",
    "queries",
}


@dataclass(frozen=True)
class V2EvalArena:
    rank: int
    family_id: str
    queries: tuple[int, int, int, int, int, int]


@dataclass(frozen=True)
class RootGeometry:
    family_id: str
    tied_queries: tuple[int, ...]
    optimal_tied_queries: tuple[int, ...]
    feature_pairs: tuple[tuple[int, tuple[Fraction, Fraction]], ...]


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _jsonl_bytes(values: Iterable[object]) -> bytes:
    return b"".join(_json_bytes(value) for value in values)


def _require_hex(value: object, length: int, label: str) -> str:
    if not isinstance(value, str) or len(value) != length:
        raise ValueError(f"invalid {label}")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"invalid {label}")
    return value


def _parse_eval_record(raw: object) -> V2EvalArena:
    if not isinstance(raw, dict) or set(raw) != _ARENA_KEYS:
        raise ValueError("EVAL arena field set mismatch")
    if raw.get("role") != "EVAL":
        raise ValueError("EVAL arena role mismatch")
    rank = raw.get("rank")
    if not isinstance(rank, int) or isinstance(rank, bool):
        raise ValueError("EVAL arena rank malformed")
    family_id = _require_hex(raw.get("family_id"), 64, "EVAL family_id")
    _require_hex(raw.get("split_rank"), 64, "EVAL split_rank")
    _require_hex(raw.get("canonical_bytes_hex"), 16, "EVAL canonical bytes")
    first_counter = raw.get("first_counter")
    if not isinstance(first_counter, int) or isinstance(first_counter, bool) or first_counter < 0:
        raise ValueError("EVAL first_counter malformed")
    queries_raw = raw.get("queries")
    if not isinstance(queries_raw, list) or len(queries_raw) != 6:
        raise ValueError("EVAL arena requires six ordered query masks")
    if any(not isinstance(value, int) or isinstance(value, bool) for value in queries_raw):
        raise ValueError("EVAL query masks must be integers")
    queries = tuple(queries_raw)
    arena = SixQueryArena(queries)
    if arena.queries != queries:
        raise ValueError("EVAL arena query ordering/normalization drift")
    return V2EvalArena(rank=rank, family_id=family_id, queries=queries)


def load_eval_arenas(
    protocol_root: str | Path,
    *,
    require_count: int | None = EVAL_ARENA_COUNT,
) -> tuple[V2EvalArena, ...]:
    path = Path(protocol_root) / "EVAL_ARENAS.jsonl"
    records: list[V2EvalArena] = []
    seen: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            record = _parse_eval_record(json.loads(line))
            if record.family_id in seen:
                raise ValueError("duplicate EVAL family_id")
            seen.add(record.family_id)
            records.append(record)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("EVAL arena JSONL malformed") from exc
    if require_count is not None and len(records) != require_count:
        raise ValueError(f"EVAL arena count mismatch: expected {require_count}, got {len(records)}")
    expected_ranks = list(range(256, 256 + len(records)))
    if [record.rank for record in records] != expected_ranks:
        raise ValueError("EVAL arena ranks are not the frozen contiguous block")
    return tuple(records)


def evaluate_v2_theta(
    name: str,
    theta: tuple[Fraction, ...],
    arenas: Iterable[V2EvalArena],
    *,
    artifact_bytes: int = 0,
) -> EvaluationResult:
    arenas = tuple(arenas)
    resources = ResourceCounter()
    tracemalloc.start()
    started = time.perf_counter_ns()
    traces: list[CaseTrace] = []
    success_by_budget = {2: 0, 3: 0}

    for record in arenas:
        arena = SixQueryArena(record.queries)
        if arena.queries != record.queries:
            raise ValueError("V2 evaluator may not reorder the frozen presentation")
        for budget in (2, 3):
            for fault in range(8):
                state = initial_state(arena, fault=fault, budget=budget)
                decisions: list[DecisionTrace] = []
                selected: list[int] = []
                masks: list[int] = []
                while True:
                    view = state.selector_view()
                    scores = query_scores(theta, view, resources=resources)
                    chosen = choose_from_scores(scores)
                    decisions.append(
                        DecisionTrace(
                            candidate_mask=view.candidate_mask,
                            remaining_budget=view.remaining_budget,
                            scores=scores,
                            chosen_query=chosen,
                        )
                    )
                    if chosen is None:
                        break
                    selected.append(chosen)
                    state = execute_query(state, chosen, resources=resources)
                    masks.append(state.candidate_mask)
                repair = terminal_repair(state, resources=resources)
                success = int(repair == fault)
                success_by_budget[budget] += success
                traces.append(
                    CaseTrace(
                        canonical_task_id=record.family_id,
                        budget=budget,
                        fault=fault,
                        selected_query_ids=tuple(selected),
                        observed_bits=tuple(bit for _, bit in state.observations),
                        candidate_masks_after_queries=tuple(masks),
                        decisions=tuple(decisions),
                        repair=repair,
                        success=success,
                        query_count=len(selected),
                    )
                )

    wall_time_ns = time.perf_counter_ns() - started
    _, peak_python_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return EvaluationResult(
        name=name,
        case_traces=tuple(traces),
        success_by_budget=success_by_budget,
        resources=resources.report(
            artifact_bytes=artifact_bytes,
            peak_python_bytes=peak_python_bytes,
            wall_time_ns=wall_time_ns,
        ),
    )


def _parse_scramble_descriptor(descriptor: object) -> dict[tuple[int, int], dict[str, object]]:
    if not isinstance(descriptor, dict) or descriptor.get("schema") != "arc-reactor-mkii-scramble/v0":
        raise ValueError("SCRAMBLED descriptor schema mismatch")
    strata_raw = descriptor.get("strata")
    if not isinstance(strata_raw, list):
        raise ValueError("SCRAMBLED descriptor strata malformed")
    parsed: dict[tuple[int, int], dict[str, object]] = {}
    for item in strata_raw:
        if not isinstance(item, dict) or set(item) != {
            "budget",
            "decision_depth",
            "size",
            "offset",
            "row_ids_sha256",
        }:
            raise ValueError("SCRAMBLED stratum field set mismatch")
        key = (item["budget"], item["decision_depth"])
        if key in parsed:
            raise ValueError("duplicate SCRAMBLED stratum")
        parsed[key] = {
            "size": item["size"],
            "offset": item["offset"],
            "row_ids_sha256": item["row_ids_sha256"],
        }
    return parsed


def scrambled_feedback_map(
    rows: Iterable[V2TrainingRow],
    descriptor: object,
) -> dict[str, int]:
    expected = _parse_scramble_descriptor(descriptor)
    grouped: dict[tuple[int, int], list[tuple[str, int]]] = defaultdict(list)
    for row in rows:
        grouped[(row.budget, row.decision_depth)].append((row.row_id, row.feedback))
    if set(grouped) != set(expected):
        raise ValueError("SCRAMBLED row strata mismatch")

    feedback_by_id: dict[str, int] = {}
    for key in sorted(grouped):
        ordered = sorted(grouped[key], key=lambda item: item[0])
        frozen = expected[key]
        n = len(ordered)
        if n != frozen["size"]:
            raise ValueError(f"SCRAMBLED row-count mismatch for {key}")
        payload = b"\n".join(row_id.encode("ascii") for row_id, _ in ordered)
        digest = hashlib.sha256(ROW_ID_LIST_PREFIX + payload).hexdigest()
        if digest != frozen["row_ids_sha256"]:
            raise ValueError(f"SCRAMBLED row-ID-list hash mismatch for {key}")
        offset = frozen["offset"]
        if not isinstance(offset, int) or isinstance(offset, bool) or not 0 <= offset < max(1, n):
            raise ValueError(f"SCRAMBLED offset malformed for {key}")
        for index, (destination_id, _) in enumerate(ordered):
            feedback_by_id[destination_id] = ordered[(index + offset) % n][1]
    return feedback_by_id


def iter_scrambled_rows(
    rows: Iterable[V2TrainingRow],
    feedback_by_id: dict[str, int],
) -> Iterator[V2TrainingRow]:
    seen: set[str] = set()
    for row in rows:
        try:
            feedback = feedback_by_id[row.row_id]
        except KeyError as exc:
            raise ValueError("SCRAMBLED feedback map missing row ID") from exc
        if row.row_id in seen:
            raise ValueError("duplicate row ID while applying SCRAMBLED feedback")
        seen.add(row.row_id)
        yield replace(row, feedback=feedback)
    if seen != set(feedback_by_id):
        raise ValueError("SCRAMBLED feedback map contains rows absent from corpus")


def build_scrambled_rows(
    rows: Sequence[V2TrainingRow],
    descriptor: object,
) -> list[V2TrainingRow]:
    feedback = scrambled_feedback_map(rows, descriptor)
    return list(iter_scrambled_rows(rows, feedback))


def fresh_host_replay_equivalent(
    theta: tuple[Fraction, ...],
    arenas: Iterable[V2EvalArena],
) -> bool:
    arenas = tuple(arenas)
    first = evaluate_v2_theta("source", theta, arenas)
    second = evaluate_v2_theta("replay", theta, arenas)
    return first.case_traces == second.case_traces and first.success_by_budget == second.success_by_budget


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"n": value.numerator, "d": value.denominator}


def _decision_record(decision: DecisionTrace) -> dict[str, object]:
    return {
        "candidate_mask": decision.candidate_mask,
        "remaining_budget": decision.remaining_budget,
        "scores": [
            {"query_id": query_id, "score": _fraction_record(score)}
            for query_id, score in decision.scores
        ],
        "chosen_query": decision.chosen_query,
    }


def _case_record(case: CaseTrace) -> dict[str, object]:
    return {
        "canonical_task_id": case.canonical_task_id,
        "budget": case.budget,
        "fault": case.fault,
        "selected_query_ids": list(case.selected_query_ids),
        "observed_bits": list(case.observed_bits),
        "candidate_masks_after_queries": list(case.candidate_masks_after_queries),
        "decisions": [_decision_record(decision) for decision in case.decisions],
        "repair": case.repair,
        "success": case.success,
        "query_count": case.query_count,
    }


def _fit_and_save(
    *,
    arm: str,
    rows: Iterable[V2TrainingRow] | None,
    artifact_path: Path,
    implementation_commit: str,
    protocol_manifest_sha256: str,
) -> tuple[Fraction, ...]:
    resources = ResourceCounter()
    if arm == "FROZEN":
        theta = tuple(THETA0)
        training_rows = 0
    else:
        if rows is None:
            raise ValueError("trained arm requires rows")
        theta = fit_theta(rows, resources=resources)  # runtime is iterator-compatible
        training_rows = resources.training_rows_consumed
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    save_artifact(artifact_path, theta)
    receipt = {
        "schema": FIT_RECEIPT_SCHEMA,
        "implementation_commit": implementation_commit,
        "protocol_manifest_sha256": protocol_manifest_sha256,
        "arm": arm,
        "training_row_count": training_rows,
        "artifact_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
    }
    artifact_path.with_name(artifact_path.name + ".receipt.json").write_bytes(_json_bytes(receipt))
    return theta


def execute_primary_result(
    *,
    protocol_root: str | Path,
    out: str | Path,
    implementation_commit: str,
    g4_start_lock_commit: str,
) -> None:
    implementation_commit = _require_hex(implementation_commit, 40, "G3 implementation commit")
    g4_start_lock_commit = _require_hex(g4_start_lock_commit, 40, "G4 start lock commit")
    protocol = Path(protocol_root)
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"primary result output already exists: {out}")

    verification = verify_frozen_g2_protocol(protocol)
    if verification.manifest_sha256 != EXPECTED_G2_MANIFEST_SHA256:
        raise ValueError("unexpected G2 manifest at G4 primary execution")
    verify_train_corpus_against_scramble(protocol)
    train_arenas = load_train_arenas(protocol)

    try:
        scramble_descriptor = json.loads((protocol / "SCRAMBLE.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("frozen SCRAMBLED descriptor unreadable") from exc

    out.mkdir(parents=True, exist_ok=False)
    artifact_root = out / "artifacts"

    learn_theta = _fit_and_save(
        arm="LEARN",
        rows=iter_v2_training_rows(train_arenas),
        artifact_path=artifact_root / "LEARN.json",
        implementation_commit=implementation_commit,
        protocol_manifest_sha256=verification.manifest_sha256,
    )

    feedback_map = scrambled_feedback_map(iter_v2_training_rows(train_arenas), scramble_descriptor)
    scrambled_theta = _fit_and_save(
        arm="SCRAMBLED",
        rows=iter_scrambled_rows(iter_v2_training_rows(train_arenas), feedback_map),
        artifact_path=artifact_root / "SCRAMBLED.json",
        implementation_commit=implementation_commit,
        protocol_manifest_sha256=verification.manifest_sha256,
    )
    frozen_theta = _fit_and_save(
        arm="FROZEN",
        rows=None,
        artifact_path=artifact_root / "FROZEN.json",
        implementation_commit=implementation_commit,
        protocol_manifest_sha256=verification.manifest_sha256,
    )

    # Artifact bytes, not in-memory fitting objects, cross into evaluation.
    theta_by_arm = {
        "LEARN": load_artifact(artifact_root / "LEARN.json"),
        "SCRAMBLED": load_artifact(artifact_root / "SCRAMBLED.json"),
        "FROZEN": load_artifact(artifact_root / "FROZEN.json"),
    }
    if theta_by_arm != {
        "LEARN": learn_theta,
        "SCRAMBLED": scrambled_theta,
        "FROZEN": frozen_theta,
    }:
        raise RuntimeError("serialized selector artifact round-trip mismatch")

    eval_arenas = load_eval_arenas(protocol)
    results = {
        arm: evaluate_v2_theta(
            arm,
            theta,
            eval_arenas,
            artifact_bytes=(artifact_root / f"{arm}.json").stat().st_size,
        )
        for arm, theta in theta_by_arm.items()
    }

    replay = {
        "theta_before_into_fresh_host": fresh_host_replay_equivalent(theta_by_arm["FROZEN"], eval_arenas),
        "theta_after_into_fresh_host": fresh_host_replay_equivalent(theta_by_arm["LEARN"], eval_arenas),
        "scientific_interpretation": "fresh-host serialized-artifact replay equivalence",
    }
    replay["all_pass"] = bool(
        replay["theta_before_into_fresh_host"] and replay["theta_after_into_fresh_host"]
    )

    passed = ignition_pass(
        results["LEARN"],
        results["SCRAMBLED"],
        results["FROZEN"],
        transplant_ok=bool(replay["all_pass"]),
    )

    for arm in ("LEARN", "SCRAMBLED", "FROZEN"):
        (out / f"{arm}_CASES.jsonl").write_bytes(
            _jsonl_bytes(_case_record(case) for case in results[arm].case_traces)
        )
    (out / "TRANSPLANT.json").write_bytes(_json_bytes(replay))
    (out / "RESOURCES.json").write_bytes(
        _json_bytes({arm: asdict(results[arm].resources) for arm in ("LEARN", "SCRAMBLED", "FROZEN")})
    )
    primary = {
        "schema": PRIMARY_SCHEMA,
        "implementation_commit": implementation_commit,
        "g4_start_lock_commit": g4_start_lock_commit,
        "protocol_manifest_sha256": verification.manifest_sha256,
        "eval_family_count": len(eval_arenas),
        "replay_all_pass": replay["all_pass"],
        "ignition_pass": passed,
        "success_by_budget": {
            str(budget): {
                arm: results[arm].success_by_budget[budget]
                for arm in ("LEARN", "SCRAMBLED", "FROZEN")
            }
            for budget in (2, 3)
        },
        "root_autopsy_status": "NOT_COMPUTED_PRIMARY_RESULT_ONLY",
    }
    (out / "PRIMARY_RESULT.json").write_bytes(_json_bytes(primary))

    payload_names = sorted(
        str(path.relative_to(out))
        for path in out.rglob("*")
        if path.is_file() and path.name != "PRIMARY_MANIFEST_SHA256.txt"
    )
    manifest = "".join(
        f"{hashlib.sha256((out / name).read_bytes()).hexdigest()}  {name}\n"
        for name in payload_names
    ).encode("ascii")
    (out / "PRIMARY_MANIFEST_SHA256.txt").write_bytes(manifest)


def _dot(beta: tuple[Fraction, Fraction], z: tuple[Fraction, Fraction]) -> Fraction:
    return beta[0] * z[0] + beta[1] * z[1]


def tie_choice(beta: tuple[Fraction, Fraction], geometry: RootGeometry) -> int:
    pairs = dict(geometry.feature_pairs)
    if set(pairs) != set(geometry.tied_queries):
        raise ValueError("root geometry feature pairs do not cover T_a")
    scored = [(query_id, _dot(beta, pairs[query_id])) for query_id in geometry.tied_queries]
    best = max(score for _, score in scored)
    return min(query_id for query_id, score in scored if score == best)


def conditional_tie_success(beta: tuple[Fraction, Fraction], geometries: Sequence[RootGeometry]) -> int:
    return sum(
        tie_choice(beta, geometry) in set(geometry.optimal_tied_queries)
        for geometry in geometries
    )


def _primitive_line_normal(
    first: tuple[Fraction, Fraction],
    second: tuple[Fraction, Fraction],
) -> tuple[int, int] | None:
    dx = first[0] - second[0]
    dy = first[1] - second[1]
    if dx == 0 and dy == 0:
        return None
    lcm = math.lcm(dx.denominator, dy.denominator)
    a = dx.numerator * (lcm // dx.denominator)
    b = dy.numerator * (lcm // dy.denominator)
    divisor = math.gcd(abs(a), abs(b))
    a //= divisor
    b //= divisor
    if a < 0 or (a == 0 and b < 0):
        a, b = -a, -b
    return a, b


def _half_plane(vector: tuple[int, int]) -> int:
    x, y = vector
    return 0 if y > 0 or (y == 0 and x >= 0) else 1


def _ray_compare(left: tuple[int, int], right: tuple[int, int]) -> int:
    left_half = _half_plane(left)
    right_half = _half_plane(right)
    if left_half != right_half:
        return -1 if left_half < right_half else 1
    cross = left[0] * right[1] - left[1] * right[0]
    if cross > 0:
        return -1
    if cross < 0:
        return 1
    return 0


def _candidate_betas(geometries: Sequence[RootGeometry]) -> tuple[tuple[Fraction, Fraction], ...]:
    lines: set[tuple[int, int]] = set()
    for geometry in geometries:
        pairs = dict(geometry.feature_pairs)
        for i, left in enumerate(geometry.tied_queries):
            for right in geometry.tied_queries[i + 1 :]:
                normal = _primitive_line_normal(pairs[left], pairs[right])
                if normal is not None:
                    lines.add(normal)

    if not lines:
        return ((Fraction(0), Fraction(0)),)

    rays: set[tuple[int, int]] = set()
    for a, b in lines:
        ray = (b, -a)
        divisor = math.gcd(abs(ray[0]), abs(ray[1]))
        ray = (ray[0] // divisor, ray[1] // divisor)
        rays.add(ray)
        rays.add((-ray[0], -ray[1]))
    ordered = sorted(rays, key=cmp_to_key(_ray_compare))

    candidates: list[tuple[Fraction, Fraction]] = [(Fraction(0), Fraction(0))]
    for ray in ordered:
        candidates.append((Fraction(ray[0]), Fraction(ray[1])))
    for index, first in enumerate(ordered):
        second = ordered[(index + 1) % len(ordered)]
        witness = (first[0] + second[0], first[1] + second[1])
        if witness == (0, 0):
            witness = (-first[1], first[0])
        candidates.append((Fraction(witness[0]), Fraction(witness[1])))

    unique: list[tuple[Fraction, Fraction]] = []
    seen: set[tuple[Fraction, Fraction]] = set()
    for beta in candidates:
        if beta not in seen:
            seen.add(beta)
            unique.append(beta)
    return tuple(unique)


def max_conditional_tie_success(geometries: Sequence[RootGeometry]) -> int:
    if not geometries:
        return 0
    return max(conditional_tie_success(beta, geometries) for beta in _candidate_betas(geometries))


def _geometry_from_eval(record: V2EvalArena) -> RootGeometry:
    # Deliberately imported only in the post-primary autopsy path.
    from .v2_gladiator import analyze_arena

    analysis = analyze_arena(SixQueryArena(record.queries))
    if not analysis.admitted:
        raise ValueError("frozen EVAL arena no longer satisfies admitted-root geometry")
    return RootGeometry(
        family_id=record.family_id,
        tied_queries=analysis.tied_queries,
        optimal_tied_queries=analysis.optimal_tied_queries,
        feature_pairs=analysis.feature_pairs,
    )


def _load_primary_learn_roots(primary_root: Path) -> dict[str, int]:
    choices: dict[str, set[int]] = defaultdict(set)
    try:
        for line in (primary_root / "LEARN_CASES.jsonl").read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            record = json.loads(line)
            if record.get("budget") != 3:
                continue
            decisions = record.get("decisions")
            if not isinstance(decisions, list) or not decisions:
                raise ValueError("primary LEARN trace lacks root decision")
            root = decisions[0].get("chosen_query")
            if not isinstance(root, int):
                raise ValueError("primary LEARN root query malformed")
            family_id = _require_hex(record.get("canonical_task_id"), 64, "primary LEARN family_id")
            choices[family_id].add(root)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("primary LEARN cases unreadable") from exc

    resolved: dict[str, int] = {}
    for family_id, roots in choices.items():
        if len(roots) != 1:
            raise ValueError("LEARN root choice depends on hidden fault")
        resolved[family_id] = next(iter(roots))
    return resolved


def compute_root_autopsy(
    *,
    protocol_root: str | Path,
    primary_root: str | Path,
    primary_record_commit: str,
    out: str | Path,
) -> None:
    primary_record_commit = _require_hex(primary_record_commit, 40, "primary result commit")
    protocol = Path(protocol_root)
    primary = Path(primary_root)
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"root autopsy output already exists: {out}")
    verify_frozen_g2_protocol(protocol)

    try:
        primary_record = json.loads((primary / "PRIMARY_RESULT.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("durable primary result payload missing or malformed") from exc
    if primary_record.get("schema") != PRIMARY_SCHEMA:
        raise ValueError("primary result schema mismatch")
    if primary_record.get("root_autopsy_status") != "NOT_COMPUTED_PRIMARY_RESULT_ONLY":
        raise ValueError("primary result is not an autopsy-free fossil")
    if primary_record.get("protocol_manifest_sha256") != EXPECTED_G2_MANIFEST_SHA256:
        raise ValueError("primary result protocol provenance mismatch")

    eval_arenas = load_eval_arenas(protocol)
    geometries = tuple(_geometry_from_eval(record) for record in eval_arenas)
    learn_theta = load_artifact(primary / "artifacts" / "LEARN.json")
    beta = (learn_theta[6], learn_theta[7])
    roots = _load_primary_learn_roots(primary)
    if set(roots) != {record.family_id for record in eval_arenas}:
        raise ValueError("primary LEARN traces do not cover frozen EVAL families exactly")

    c_tie_max = max_conditional_tie_success(geometries)
    c_tie_learn = conditional_tie_success(beta, geometries)
    t_retention = 0
    c_actual = 0
    per_arena: list[dict[str, object]] = []
    for geometry in geometries:
        actual_root = roots[geometry.family_id]
        tied = actual_root in set(geometry.tied_queries)
        conditional_root = tie_choice(beta, geometry)
        conditional_good = conditional_root in set(geometry.optimal_tied_queries)
        actual_good = actual_root in set(geometry.optimal_tied_queries)
        if tied:
            t_retention += 1
            if actual_root != conditional_root:
                raise RuntimeError("root success factorization violated inside T_a")
        if actual_good:
            c_actual += 1
        if actual_good != (tied and conditional_good):
            raise RuntimeError("A_a = R_a G_a factorization violated")
        per_arena.append(
            {
                "family_id": geometry.family_id,
                "conditional_root": conditional_root,
                "actual_root": actual_root,
                "tie_retained": tied,
                "conditional_optimal": conditional_good,
                "actual_optimal": actual_good,
            }
        )

    result = {
        "schema": AUTOPSY_SCHEMA,
        "status": "POST_PRIMARY_NONACCEPTANCE_DIAGNOSTIC",
        "primary_record_commit": primary_record_commit,
        "protocol_manifest_sha256": EXPECTED_G2_MANIFEST_SHA256,
        "values": {
            "C_tie_max": c_tie_max,
            "C_tie_learn": c_tie_learn,
            "T_retention_learn": t_retention,
            "C_actual_learn": c_actual,
            "best_common_orientation_count_shortfall": c_tie_max - c_tie_learn,
            "off_manifold_interference_count": c_tie_learn - c_actual,
            "within_manifold_ranking_error_count": t_retention - c_actual,
        },
        "beta_learn": [_fraction_record(beta[0]), _fraction_record(beta[1])],
        "per_arena": per_arena,
        "acceptance_effect": "NONE",
    }
    out.mkdir(parents=True, exist_ok=False)
    (out / "ROOT_AUTOPSY.json").write_bytes(_json_bytes(result))
