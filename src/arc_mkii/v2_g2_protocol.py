from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from .domain import SixQueryArena
from .features import feature_vector
from .host import execute_query, initial_state, terminal_repair
from .v2_canonical import FAMILY_PREFIX, canonical_bytes

G1_RECORD_ID = "1edf919be5a9810d8e670ed26c0174642b3e7756"
G1_IMPLEMENTATION_FREEZE_ID_V2 = "9ba2e6e8ad448e72702ade6af23f4a1a25fbe932"
EXPECTED_G1_CENSUS_SHA256 = "d0959d5794f3d398cae226050f48c2e68b8032819991536b9aadbdc8683dcd54"
EXPECTED_G1_FAMILIES_SHA256 = "213a5133208c1f4ca19edd500e9f68b40ef13ed47959fdc2921a4daf3e951057"
EXPECTED_G1_CANONICAL = 436
V2_SEED = "arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001"
SPLIT_PREFIX = b"arc-mkii-v2-six-query-gladiator-split\0"
TRAIN_COUNT = 256
EVAL_COUNT = 64
OUTSIDE_COUNT = EXPECTED_G1_CANONICAL - TRAIN_COUNT - EVAL_COUNT
PROTOCOL_SCHEMA = "arc-reactor-mkii-v2-protocol/v0"
ROOT_AUTOPSY_SCHEMA = "arc-reactor-mkii-v2-root-autopsy-contract/v0"
ROOT_AUTOPSY_STATUS = "POST_G1_PRE_G4_UNEVALUATED_NONACCEPTANCE"
SCRAMBLE_SCHEMA = "arc-reactor-mkii-scramble/v0"
ROW_ID_PREFIX = b"arc-mkii-training-row-v0\0"
ROW_ID_LIST_PREFIX = b"arc-mkii-row-id-list-v0\0"

_PAYLOAD_FILES = {
    "PROTOCOL.json",
    "TRAIN_ARENAS.jsonl",
    "EVAL_ARENAS.jsonl",
    "OUTSIDE_CONFIRMATORY.jsonl",
    "SPLIT_RANKS.jsonl",
    "SCRAMBLE.json",
    "ROOT_AUTOPSY_CONTRACT.json",
}
_EXPECTED_FILES = _PAYLOAD_FILES | {"MANIFEST_SHA256.txt"}
_G1_FILES = {"CENSUS.json", "FAMILIES.jsonl", "SHA256.txt"}
_FAMILY_KEYS = {"canonical_bytes_hex", "family_id", "first_counter", "queries"}
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
class FamilyInput:
    canonical_bytes_hex: str
    family_id: str
    first_counter: int
    queries: tuple[int, int, int, int, int, int]


@dataclass(frozen=True)
class RankedFamily:
    rank: int
    role: str
    split_rank: str
    family_id: str
    canonical_bytes_hex: str
    first_counter: int
    queries: tuple[int, int, int, int, int, int]


@dataclass(frozen=True)
class ProtocolSplit:
    all_rows: tuple[RankedFamily, ...]
    train: tuple[RankedFamily, ...]
    eval: tuple[RankedFamily, ...]
    outside: tuple[RankedFamily, ...]


@dataclass(frozen=True)
class RowIdentity:
    canonical_task_id: str
    query_masks: tuple[int, ...]
    budget: int
    fault: int
    planned_sequence: tuple[int, ...]
    decision_depth: int
    candidate_mask: int
    remaining_query_ids: tuple[int, ...]
    action_query_id: int
    features: tuple[Fraction, ...]
    terminal_repair: int
    row_id: str


@dataclass(frozen=True)
class V2ProtocolVerification:
    hashes: dict[str, str]
    manifest_sha256: str
    train_count: int
    eval_count: int
    outside_count: int


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


def _require_hex64(value: object, label: str) -> str:
    return _require_hex(value, 64, label)


def split_rank(family_id: str) -> str:
    family_id = _require_hex64(family_id, "family_id")
    return hashlib.sha256(SPLIT_PREFIX + family_id.encode("ascii")).hexdigest()


def _validate_family(record: FamilyInput, *, verify_canonical: bool) -> None:
    _require_hex64(record.family_id, "family_id")
    _require_hex(record.canonical_bytes_hex, 16, "canonical_bytes_hex")
    if not isinstance(record.first_counter, int) or isinstance(record.first_counter, bool) or record.first_counter < 0:
        raise ValueError("invalid first_counter")
    if not isinstance(record.queries, tuple) or len(record.queries) != 6:
        raise ValueError("family queries must contain exactly six masks")
    if any(not isinstance(query, int) or isinstance(query, bool) for query in record.queries):
        raise ValueError("family query masks must be integers")
    arena = SixQueryArena(record.queries)
    if arena.queries != record.queries:
        raise ValueError("family queries are not stored as normalized operational masks")
    if verify_canonical:
        canonical = canonical_bytes(arena)
        if canonical.hex() != record.canonical_bytes_hex:
            raise ValueError("G1 canonical bytes mismatch")
        expected_family_id = hashlib.sha256(FAMILY_PREFIX + canonical).hexdigest()
        if expected_family_id != record.family_id:
            raise ValueError("G1 family_id mismatch")


def _parse_g1_manifest(root: Path) -> dict[str, str]:
    recorded: dict[str, str] = {}
    try:
        lines = (root / "SHA256.txt").read_text(encoding="ascii").splitlines()
        for line in lines:
            digest, name = line.split("  ", 1)
            if name in recorded or name not in {"CENSUS.json", "FAMILIES.jsonl"}:
                raise ValueError
            recorded[name] = _require_hex64(digest, "G1 manifest digest")
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError("G1 custody manifest malformed") from exc
    if set(recorded) != {"CENSUS.json", "FAMILIES.jsonl"}:
        raise ValueError("G1 custody manifest file set mismatch")
    return recorded


def load_g1_custody(root: str | Path) -> tuple[dict[str, object], tuple[FamilyInput, ...]]:
    root = Path(root)
    if not root.is_dir():
        raise ValueError("G1 custody directory does not exist")
    if {path.name for path in root.iterdir()} != _G1_FILES:
        raise ValueError("G1 custody file set mismatch")

    census_bytes = (root / "CENSUS.json").read_bytes()
    families_bytes = (root / "FAMILIES.jsonl").read_bytes()
    actual_hashes = {
        "CENSUS.json": hashlib.sha256(census_bytes).hexdigest(),
        "FAMILIES.jsonl": hashlib.sha256(families_bytes).hexdigest(),
    }
    expected_hashes = {
        "CENSUS.json": EXPECTED_G1_CENSUS_SHA256,
        "FAMILIES.jsonl": EXPECTED_G1_FAMILIES_SHA256,
    }
    if actual_hashes != expected_hashes:
        raise ValueError("G1 custody hash mismatch")
    if _parse_g1_manifest(root) != expected_hashes:
        raise ValueError("G1 custody manifest does not bind frozen hashes")

    try:
        census = json.loads(census_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("G1 census JSON malformed") from exc
    if census.get("schema") != "arc-reactor-mkii-v2-g1-census/v0":
        raise ValueError("G1 census schema mismatch")
    if census.get("implementation_commit") != G1_IMPLEMENTATION_FREEZE_ID_V2:
        raise ValueError("G1 implementation freeze mismatch")
    if census.get("status") != "G1_PASS":
        raise ValueError("G1 status is not G1_PASS")
    counts = census.get("counts")
    if not isinstance(counts, dict) or counts.get("admitted_canonical") != EXPECTED_G1_CANONICAL:
        raise ValueError("G1 canonical family count mismatch")

    records: list[FamilyInput] = []
    seen: set[str] = set()
    try:
        text = families_bytes.decode("utf-8")
        for line in text.splitlines():
            if not line:
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict) or set(raw) != _FAMILY_KEYS:
                raise ValueError("G1 family record field set mismatch")
            queries_raw = raw["queries"]
            if not isinstance(queries_raw, list):
                raise ValueError("G1 family queries must be a list")
            record = FamilyInput(
                canonical_bytes_hex=raw["canonical_bytes_hex"],
                family_id=raw["family_id"],
                first_counter=raw["first_counter"],
                queries=tuple(queries_raw),
            )
            _validate_family(record, verify_canonical=True)
            if record.family_id in seen:
                raise ValueError("duplicate family_id in G1 custody")
            seen.add(record.family_id)
            records.append(record)
    except (UnicodeError, json.JSONDecodeError, TypeError) as exc:
        raise ValueError("G1 family JSONL malformed") from exc
    if len(records) != EXPECTED_G1_CANONICAL:
        raise ValueError("G1 family line count mismatch")
    return census, tuple(records)


def _role_for_rank(rank: int) -> str:
    if rank < TRAIN_COUNT:
        return "TRAIN"
    if rank < TRAIN_COUNT + EVAL_COUNT:
        return "EVAL"
    return "OUTSIDE_CONFIRMATORY_V2"


def rank_families(records: Iterable[FamilyInput]) -> tuple[RankedFamily, ...]:
    source = tuple(records)
    seen: set[str] = set()
    ranked_source: list[tuple[str, str, FamilyInput]] = []
    for record in source:
        _validate_family(record, verify_canonical=False)
        if record.family_id in seen:
            raise ValueError(f"duplicate family_id: {record.family_id}")
        seen.add(record.family_id)
        digest = split_rank(record.family_id)
        ranked_source.append((digest, record.family_id, record))
    ranked_source.sort(key=lambda item: (item[0], item[1]))
    return tuple(
        RankedFamily(
            rank=rank,
            role=_role_for_rank(rank),
            split_rank=digest,
            family_id=record.family_id,
            canonical_bytes_hex=record.canonical_bytes_hex,
            first_counter=record.first_counter,
            queries=record.queries,
        )
        for rank, (digest, _, record) in enumerate(ranked_source)
    )


def split_families(records: Iterable[FamilyInput]) -> ProtocolSplit:
    ranked = rank_families(records)
    if len(ranked) != EXPECTED_G1_CANONICAL:
        raise ValueError(f"G2 requires exactly {EXPECTED_G1_CANONICAL} G1 families")
    train = ranked[:TRAIN_COUNT]
    eval_rows = ranked[TRAIN_COUNT : TRAIN_COUNT + EVAL_COUNT]
    outside = ranked[TRAIN_COUNT + EVAL_COUNT :]
    if len(train) != TRAIN_COUNT or len(eval_rows) != EVAL_COUNT or len(outside) != OUTSIDE_COUNT:
        raise RuntimeError("frozen G2 role partition has incorrect size")
    return ProtocolSplit(all_rows=ranked, train=train, eval=eval_rows, outside=outside)


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"n": value.numerator, "d": value.denominator}


def row_id_from_fields(
    *,
    canonical_task_id: str,
    query_masks: Sequence[int],
    budget: int,
    fault: int,
    planned_sequence: Sequence[int],
    decision_depth: int,
    candidate_mask: int,
    remaining_query_ids: Sequence[int],
    action_query_id: int,
    features: Sequence[Fraction],
    terminal_repair: int,
) -> str:
    record = {
        "canonical_task_id": canonical_task_id,
        "query_masks": list(query_masks),
        "budget": budget,
        "fault": fault,
        "planned_sequence": list(planned_sequence),
        "decision_depth": decision_depth,
        "candidate_mask": candidate_mask,
        "remaining_query_ids": list(remaining_query_ids),
        "action_query_id": action_query_id,
        "features": [_fraction_record(Fraction(value)) for value in features],
        "terminal_repair": terminal_repair,
    }
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(ROW_ID_PREFIX + payload).hexdigest()


def _rows_for_arena(record: RankedFamily) -> Iterator[RowIdentity]:
    arena = SixQueryArena(record.queries)
    feature_cache: dict[tuple[int, tuple[int, ...], int, int], tuple[Fraction, ...]] = {}
    for budget in (2, 3):
        for fault in range(8):
            for sequence in itertools.permutations(range(6), budget):
                state = initial_state(arena, fault=fault, budget=budget)
                staged: list[tuple[int, int, tuple[int, ...], int, tuple[Fraction, ...]]] = []
                for decision_depth, query_id in enumerate(sequence):
                    if state.candidate_mask.bit_count() == 1:
                        break
                    view = state.selector_view()
                    cache_key = (
                        view.candidate_mask,
                        view.remaining_query_ids,
                        view.remaining_budget,
                        query_id,
                    )
                    features = feature_cache.get(cache_key)
                    if features is None:
                        features = tuple(feature_vector(view, query_id))
                        feature_cache[cache_key] = features
                    staged.append(
                        (
                            decision_depth,
                            state.candidate_mask,
                            state.remaining_query_ids,
                            query_id,
                            features,
                        )
                    )
                    state = execute_query(state, query_id)
                repair = terminal_repair(state)
                for decision_depth, candidate_mask, remaining_ids, query_id, features in staged:
                    identifier = row_id_from_fields(
                        canonical_task_id=record.family_id,
                        query_masks=arena.queries,
                        budget=budget,
                        fault=fault,
                        planned_sequence=sequence,
                        decision_depth=decision_depth,
                        candidate_mask=candidate_mask,
                        remaining_query_ids=remaining_ids,
                        action_query_id=query_id,
                        features=features,
                        terminal_repair=repair,
                    )
                    yield RowIdentity(
                        canonical_task_id=record.family_id,
                        query_masks=arena.queries,
                        budget=budget,
                        fault=fault,
                        planned_sequence=sequence,
                        decision_depth=decision_depth,
                        candidate_mask=candidate_mask,
                        remaining_query_ids=remaining_ids,
                        action_query_id=query_id,
                        features=features,
                        terminal_repair=repair,
                        row_id=identifier,
                    )


def training_row_identity_records(arenas: Iterable[RankedFamily]) -> Iterator[RowIdentity]:
    for record in sorted(tuple(arenas), key=lambda item: (item.rank, item.family_id)):
        yield from _rows_for_arena(record)


def _offset(budget: int, depth: int, n: int) -> int:
    if n <= 1:
        return 0
    seed = f"arc-reactor-mk-ii/v0/scramble/{budget}/{depth}".encode()
    return 1 + (int.from_bytes(hashlib.sha256(seed).digest()[:8], "big") % (n - 1))


def scramble_descriptor_for_train(arenas: Iterable[RankedFamily]) -> dict[str, object]:
    grouped: dict[tuple[int, int], list[str]] = defaultdict(list)
    for row in training_row_identity_records(arenas):
        grouped[(row.budget, row.decision_depth)].append(row.row_id)
    strata: list[dict[str, object]] = []
    for budget, depth in sorted(grouped):
        ordered_ids = sorted(grouped[(budget, depth)])
        payload = b"\n".join(identifier.encode("ascii") for identifier in ordered_ids)
        strata.append(
            {
                "budget": budget,
                "decision_depth": depth,
                "size": len(ordered_ids),
                "offset": _offset(budget, depth, len(ordered_ids)),
                "row_ids_sha256": hashlib.sha256(ROW_ID_LIST_PREFIX + payload).hexdigest(),
            }
        )
    expected_strata = {(2, 0), (2, 1), (3, 0), (3, 1), (3, 2)}
    if set(grouped) != expected_strata:
        raise RuntimeError("V2 TRAIN row population produced unexpected SCRAMBLED strata")
    return {"schema": SCRAMBLE_SCHEMA, "strata": strata}


def _arena_record(record: RankedFamily) -> dict[str, object]:
    return {
        "rank": record.rank,
        "role": record.role,
        "split_rank": record.split_rank,
        "family_id": record.family_id,
        "canonical_bytes_hex": record.canonical_bytes_hex,
        "first_counter": record.first_counter,
        "queries": list(record.queries),
    }


def _protocol_record() -> dict[str, object]:
    return {
        "schema": PROTOCOL_SCHEMA,
        "g1_record_id": G1_RECORD_ID,
        "g1_implementation_freeze_id_v2": G1_IMPLEMENTATION_FREEZE_ID_V2,
        "g1_custody_sha256": {
            "CENSUS.json": EXPECTED_G1_CENSUS_SHA256,
            "FAMILIES.jsonl": EXPECTED_G1_FAMILIES_SHA256,
        },
        "g1_status": "G1_PASS",
        "seed": V2_SEED,
        "fault_count": 8,
        "query_count": 6,
        "budgets": [2, 3],
        "feature_count": 8,
        "ridge_lambda": {"n": 1, "d": 100},
        "canonical_family_count": EXPECTED_G1_CANONICAL,
        "train_count": TRAIN_COUNT,
        "eval_count": EVAL_COUNT,
        "outside_confirmatory_count": OUTSIDE_COUNT,
        "canonical_task_identity": "family_id",
        "split_prefix": SPLIT_PREFIX.decode("ascii"),
        "scramble_schema": SCRAMBLE_SCHEMA,
        "scramble_interpretation": (
            "prospectively fixed matched corrupted-feedback control with preserved "
            "within-stratum feedback marginals"
        ),
        "replay_interpretation_ceiling": "fresh-host serialized-artifact replay equivalence",
        "root_autopsy_schema": ROOT_AUTOPSY_SCHEMA,
        "root_autopsy_status": ROOT_AUTOPSY_STATUS,
    }


def _root_autopsy_record() -> dict[str, object]:
    return {
        "schema": ROOT_AUTOPSY_SCHEMA,
        "status": ROOT_AUTOPSY_STATUS,
        "use": "POST_RESULT_NONACCEPTANCE_DIAGNOSTICS_ONLY",
        "diagnostics": {
            "C_tie_max": "UNEVALUATED",
            "C_tie_learn": "UNEVALUATED",
            "T_retention_learn": "UNEVALUATED",
            "C_actual_learn": "UNEVALUATED",
        },
        "definitions": {
            "T_a": "budget-3 root queries with immediate balance 1/2",
            "O_a": "argmax over T_a of frozen exact two-query continuation value V_2",
            "z_a": "(weighted_best_next_split,worst_child_best_next_split)",
            "q_a_tie": "minimum-public-ID argmax over T_a of beta dot z_a",
            "C_tie_max": "maximum EVAL count with q_a_tie(beta) in O_a over rational beta",
            "C_tie_learn": "EVAL count with q_a_tie(beta_LEARN) in O_a",
            "T_retention_learn": "EVAL count where actual LEARN root remains in T_a",
            "C_actual_learn": "EVAL count where actual LEARN root lies in O_a",
        },
        "exact_geometry_algorithm": [
            "construct pairwise d=z_i-z_j inside each T_a",
            "discard d=0",
            "deduplicate coincident homogeneous lines",
            "evaluate one exact rational witness for every open sector",
            "evaluate both oriented rays of every distinct boundary line",
            "evaluate beta=0 separately",
            "use exact Fraction arithmetic and minimum-public-ID tie rule",
        ],
        "interpretation": {
            "C_tie_max_minus_C_tie_learn": "best-common-orientation count shortfall only",
            "C_tie_learn_minus_C_actual_learn": "off-manifold interference count",
            "T_retention_learn_minus_C_actual_learn": "within-manifold ranking error count",
        },
        "forbidden_effects": [
            "ignition",
            "dataset membership",
            "learner modification",
            "feature modification",
            "coefficient modification",
            "refitting",
            "threshold selection",
            "arena exclusion",
        ],
    }


def _manifest_bytes(payloads: dict[str, bytes]) -> bytes:
    return "".join(
        f"{hashlib.sha256(payloads[name]).hexdigest()}  {name}\n"
        for name in sorted(payloads)
    ).encode("ascii")


def _build_payloads(g1_root: Path) -> dict[str, bytes]:
    _, families = load_g1_custody(g1_root)
    split = split_families(families)
    payloads: dict[str, bytes] = {
        "PROTOCOL.json": _json_bytes(_protocol_record()),
        "TRAIN_ARENAS.jsonl": _jsonl_bytes(_arena_record(row) for row in split.train),
        "EVAL_ARENAS.jsonl": _jsonl_bytes(_arena_record(row) for row in split.eval),
        "OUTSIDE_CONFIRMATORY.jsonl": _jsonl_bytes(_arena_record(row) for row in split.outside),
        "SPLIT_RANKS.jsonl": _jsonl_bytes(_arena_record(row) for row in split.all_rows),
        "SCRAMBLE.json": _json_bytes(scramble_descriptor_for_train(split.train)),
        "ROOT_AUTOPSY_CONTRACT.json": _json_bytes(_root_autopsy_record()),
    }
    payloads["MANIFEST_SHA256.txt"] = _manifest_bytes(payloads)
    return payloads


def _parse_protocol_manifest(protocol: Path) -> dict[str, str]:
    recorded: dict[str, str] = {}
    try:
        for line in (protocol / "MANIFEST_SHA256.txt").read_text(encoding="ascii").splitlines():
            digest, name = line.split("  ", 1)
            if name in recorded or name not in _PAYLOAD_FILES:
                raise ValueError
            recorded[name] = _require_hex64(digest, "protocol manifest digest")
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError("protocol manifest malformed") from exc
    if set(recorded) != _PAYLOAD_FILES:
        raise ValueError("protocol manifest file set mismatch")
    return recorded


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError
            rows.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"malformed JSONL: {path.name}") from exc
    return rows


def verify_v2_protocol(g1_root: str | Path, protocol: str | Path) -> V2ProtocolVerification:
    g1_root = Path(g1_root)
    protocol = Path(protocol)
    if not protocol.is_dir():
        raise ValueError("V2 protocol directory does not exist")
    if {path.name for path in protocol.iterdir()} != _EXPECTED_FILES:
        raise ValueError("V2 protocol file set mismatch")

    recorded = _parse_protocol_manifest(protocol)
    for name, expected in recorded.items():
        actual = hashlib.sha256((protocol / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"protocol hash mismatch: {name}")

    expected_payloads = _build_payloads(g1_root)
    for name in sorted(_EXPECTED_FILES):
        if (protocol / name).read_bytes() != expected_payloads[name]:
            raise ValueError(f"V2 protocol content mismatch: {name}")

    try:
        meta = json.loads((protocol / "PROTOCOL.json").read_text(encoding="utf-8"))
        autopsy = json.loads((protocol / "ROOT_AUTOPSY_CONTRACT.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("V2 protocol JSON malformed") from exc
    if meta.get("schema") != PROTOCOL_SCHEMA:
        raise ValueError("V2 protocol schema mismatch")
    if meta.get("g1_record_id") != G1_RECORD_ID:
        raise ValueError("V2 protocol G1 record provenance mismatch")
    if meta.get("g1_implementation_freeze_id_v2") != G1_IMPLEMENTATION_FREEZE_ID_V2:
        raise ValueError("V2 protocol G1 implementation provenance mismatch")
    if meta.get("canonical_task_identity") != "family_id":
        raise ValueError("V2 protocol canonical task identity mismatch")
    if autopsy.get("schema") != ROOT_AUTOPSY_SCHEMA or autopsy.get("status") != ROOT_AUTOPSY_STATUS:
        raise ValueError("V2 root-autopsy contract mismatch")
    diagnostics = autopsy.get("diagnostics")
    if not isinstance(diagnostics, dict) or set(diagnostics) != {
        "C_tie_max",
        "C_tie_learn",
        "T_retention_learn",
        "C_actual_learn",
    } or any(value != "UNEVALUATED" for value in diagnostics.values()):
        raise ValueError("V2 root-autopsy diagnostics are not frozen unevaluated")
    if "values" in autopsy:
        raise ValueError("V2 root-autopsy contract contains evaluated values")

    all_rows = _read_jsonl(protocol / "SPLIT_RANKS.jsonl")
    if len(all_rows) != EXPECTED_G1_CANONICAL or any(set(row) != _ARENA_KEYS for row in all_rows):
        raise ValueError("V2 split-rank manifest shape mismatch")
    if [row.get("rank") for row in all_rows] != list(range(EXPECTED_G1_CANONICAL)):
        raise ValueError("V2 split ranks are not contiguous")

    role_counts = {
        "TRAIN": len(_read_jsonl(protocol / "TRAIN_ARENAS.jsonl")),
        "EVAL": len(_read_jsonl(protocol / "EVAL_ARENAS.jsonl")),
        "OUTSIDE_CONFIRMATORY_V2": len(_read_jsonl(protocol / "OUTSIDE_CONFIRMATORY.jsonl")),
    }
    if role_counts != {
        "TRAIN": TRAIN_COUNT,
        "EVAL": EVAL_COUNT,
        "OUTSIDE_CONFIRMATORY_V2": OUTSIDE_COUNT,
    }:
        raise ValueError("V2 protocol role counts mismatch")

    return V2ProtocolVerification(
        hashes=dict(recorded),
        manifest_sha256=hashlib.sha256((protocol / "MANIFEST_SHA256.txt").read_bytes()).hexdigest(),
        train_count=TRAIN_COUNT,
        eval_count=EVAL_COUNT,
        outside_count=OUTSIDE_COUNT,
    )


def freeze_v2_protocol(g1_root: str | Path, out: str | Path) -> None:
    g1_root = Path(g1_root)
    out = Path(out)
    if out.exists():
        verify_v2_protocol(g1_root, out)
        return
    payloads = _build_payloads(g1_root)
    out.mkdir(parents=True, exist_ok=False)
    for name in sorted(payloads):
        (out / name).write_bytes(payloads[name])
