from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Iterator

from .domain import SixQueryArena
from .v2_g2_protocol import RankedFamily, RowIdentity, training_row_identity_records

G2_RECORD_ID = "5689645287c41a71e109f1b022529e8b98f2006d"
DESIGN_FREEZE_ID_V2_G3 = "b6d520eafd81b367c81c145d05c4702dac94b74c"
EXPECTED_G2_MANIFEST_SHA256 = "419b7be408a5a37ab6a7ee304ac58646683a6fc4771b503e0b0f475002b4d075"
EXPECTED_TRAIN_ROWS = 817_105
ROW_ID_LIST_PREFIX = b"arc-mkii-row-id-list-v0\0"

EXPECTED_PROTOCOL_HASHES = {
    "EVAL_ARENAS.jsonl": "9fcc2a802ff95dc3186810dfa95710bf9b87057953e58c4800c2ebd3ba13bd4a",
    "OUTSIDE_CONFIRMATORY.jsonl": "f5e4849e5f61d8607aa497896b7637bba33f79d665e66070e50bbea7e36f33ff",
    "PROTOCOL.json": "0c874f5c76a1f38040e9535dd25812c96cf7ee0e6d113dda413fdf9be0f3d322",
    "ROOT_AUTOPSY_CONTRACT.json": "2959fd3a137a6e16053903e6a2736dd74a1735ff57efcc5f1b5b74392eaca011",
    "SCRAMBLE.json": "e35533e08bac9a0ae4bcfe6645db4d1d8b977811d40945896d607a9782e15a94",
    "SPLIT_RANKS.jsonl": "59eee26e4de62e819b0dfac5af27506c1361cc111fc4d01b1688c589bd5aacd6",
    "TRAIN_ARENAS.jsonl": "6b590ab3b4f88df7da407e605719eacdb6808d6d7b9dac52f8f85b8903691c99",
}
EXPECTED_PROTOCOL_FILES = set(EXPECTED_PROTOCOL_HASHES) | {"MANIFEST_SHA256.txt"}
EXPECTED_TRAIN_STRATA = {
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
class FrozenG2Verification:
    manifest_sha256: str
    train_count: int
    eval_count: int
    outside_count: int
    root_autopsy_values_present: bool


@dataclass(frozen=True)
class V2TrainingRow:
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
    feedback: int
    row_id: str


@dataclass(frozen=True)
class TrainCorpusVerification:
    total_rows: int
    strata: dict[tuple[int, int], dict[str, object]]
    fit_performed: bool = False
    eval_performed: bool = False
    autopsy_performed: bool = False
    ignition_computed: bool = False


@dataclass(frozen=True)
class G3Verification:
    g2: FrozenG2Verification
    train: TrainCorpusVerification


def _require_hex(value: object, length: int, label: str) -> str:
    if not isinstance(value, str) or len(value) != length:
        raise ValueError(f"invalid {label}")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"invalid {label}")
    return value


def _parse_manifest(protocol: Path) -> dict[str, str]:
    recorded: dict[str, str] = {}
    try:
        for line in (protocol / "MANIFEST_SHA256.txt").read_text(encoding="ascii").splitlines():
            digest, name = line.split("  ", 1)
            if name in recorded or name not in EXPECTED_PROTOCOL_HASHES:
                raise ValueError
            recorded[name] = _require_hex(digest, 64, "G2 protocol digest")
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError("G2 protocol manifest malformed") from exc
    if recorded != EXPECTED_PROTOCOL_HASHES:
        raise ValueError("G2 protocol manifest does not match frozen payload hashes")
    return recorded


def verify_frozen_g2_protocol(protocol_root: str | Path) -> FrozenG2Verification:
    protocol = Path(protocol_root)
    if not protocol.is_dir():
        raise ValueError("frozen G2 protocol directory does not exist")
    if {path.name for path in protocol.iterdir()} != EXPECTED_PROTOCOL_FILES:
        raise ValueError("frozen G2 protocol file set mismatch")

    manifest_bytes = (protocol / "MANIFEST_SHA256.txt").read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_sha256 != EXPECTED_G2_MANIFEST_SHA256:
        raise ValueError("G2 protocol manifest SHA-256 mismatch")
    recorded = _parse_manifest(protocol)
    for name, expected in recorded.items():
        actual = hashlib.sha256((protocol / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"frozen G2 protocol hash mismatch: {name}")

    try:
        meta = json.loads((protocol / "PROTOCOL.json").read_text(encoding="utf-8"))
        autopsy = json.loads((protocol / "ROOT_AUTOPSY_CONTRACT.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("frozen G2 protocol JSON malformed") from exc

    required_meta = {
        "schema": "arc-reactor-mkii-v2-protocol/v0",
        "query_count": 6,
        "feature_count": 8,
        "fault_count": 8,
        "budgets": [2, 3],
        "train_count": 256,
        "eval_count": 64,
        "outside_confirmatory_count": 116,
        "canonical_family_count": 436,
        "canonical_task_identity": "family_id",
        "ridge_lambda": {"n": 1, "d": 100},
        "replay_interpretation_ceiling": "fresh-host serialized-artifact replay equivalence",
        "root_autopsy_status": "POST_G1_PRE_G4_UNEVALUATED_NONACCEPTANCE",
    }
    for key, expected in required_meta.items():
        if meta.get(key) != expected:
            raise ValueError(f"frozen G2 protocol metadata mismatch: {key}")

    diagnostics = autopsy.get("diagnostics")
    expected_diagnostics = {
        "C_tie_max",
        "C_tie_learn",
        "T_retention_learn",
        "C_actual_learn",
    }
    if (
        autopsy.get("schema") != "arc-reactor-mkii-v2-root-autopsy-contract/v0"
        or autopsy.get("status") != "POST_G1_PRE_G4_UNEVALUATED_NONACCEPTANCE"
        or not isinstance(diagnostics, dict)
        or set(diagnostics) != expected_diagnostics
        or any(value != "UNEVALUATED" for value in diagnostics.values())
        or "values" in autopsy
    ):
        raise ValueError("frozen G2 root-autopsy contract is not unevaluated")

    return FrozenG2Verification(
        manifest_sha256=manifest_sha256,
        train_count=256,
        eval_count=64,
        outside_count=116,
        root_autopsy_values_present=False,
    )


def _parse_train_record(raw: object) -> RankedFamily:
    if not isinstance(raw, dict) or set(raw) != _ARENA_KEYS:
        raise ValueError("TRAIN arena field set mismatch")
    if raw.get("role") != "TRAIN":
        raise ValueError("TRAIN arena role mismatch")
    rank = raw.get("rank")
    first_counter = raw.get("first_counter")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 0:
        raise ValueError("TRAIN arena rank malformed")
    if not isinstance(first_counter, int) or isinstance(first_counter, bool) or first_counter < 0:
        raise ValueError("TRAIN arena first_counter malformed")
    family_id = _require_hex(raw.get("family_id"), 64, "TRAIN family_id")
    split_rank = _require_hex(raw.get("split_rank"), 64, "TRAIN split_rank")
    canonical_bytes_hex = _require_hex(raw.get("canonical_bytes_hex"), 16, "TRAIN canonical bytes")
    queries_raw = raw.get("queries")
    if not isinstance(queries_raw, list) or len(queries_raw) != 6:
        raise ValueError("TRAIN arena requires six ordered query masks")
    if any(not isinstance(value, int) or isinstance(value, bool) for value in queries_raw):
        raise ValueError("TRAIN arena query masks must be integers")
    queries = tuple(queries_raw)
    arena = SixQueryArena(queries)
    if arena.queries != queries:
        raise ValueError("TRAIN arena query ordering/normalization drift")
    return RankedFamily(
        rank=rank,
        role="TRAIN",
        split_rank=split_rank,
        family_id=family_id,
        canonical_bytes_hex=canonical_bytes_hex,
        first_counter=first_counter,
        queries=queries,
    )


def load_train_arenas(
    protocol_root: str | Path,
    *,
    require_count: int | None = 256,
) -> tuple[RankedFamily, ...]:
    path = Path(protocol_root) / "TRAIN_ARENAS.jsonl"
    records: list[RankedFamily] = []
    seen: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            record = _parse_train_record(json.loads(line))
            if record.family_id in seen:
                raise ValueError("duplicate TRAIN family_id")
            seen.add(record.family_id)
            records.append(record)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("TRAIN arena JSONL malformed") from exc
    if require_count is not None and len(records) != require_count:
        raise ValueError(f"TRAIN arena count mismatch: expected {require_count}, got {len(records)}")
    if [record.rank for record in records] != list(range(len(records))):
        raise ValueError("TRAIN arena ranks are not the frozen contiguous prefix")
    return tuple(records)


def _row_from_identity(identity: RowIdentity) -> V2TrainingRow:
    return V2TrainingRow(
        canonical_task_id=identity.canonical_task_id,
        query_masks=identity.query_masks,
        budget=identity.budget,
        fault=identity.fault,
        planned_sequence=identity.planned_sequence,
        decision_depth=identity.decision_depth,
        candidate_mask=identity.candidate_mask,
        remaining_query_ids=identity.remaining_query_ids,
        action_query_id=identity.action_query_id,
        features=identity.features,
        terminal_repair=identity.terminal_repair,
        feedback=int(identity.terminal_repair == identity.fault),
        row_id=identity.row_id,
    )


def iter_v2_training_rows(arenas: Iterable[RankedFamily]) -> Iterator[V2TrainingRow]:
    for identity in training_row_identity_records(arenas):
        yield _row_from_identity(identity)


def _offset(budget: int, depth: int, n: int) -> int:
    if n <= 1:
        return 0
    seed = f"arc-reactor-mk-ii/v0/scramble/{budget}/{depth}".encode()
    return 1 + (int.from_bytes(hashlib.sha256(seed).digest()[:8], "big") % (n - 1))


def _read_scramble(protocol: Path) -> dict[tuple[int, int], dict[str, object]]:
    try:
        raw = json.loads((protocol / "SCRAMBLE.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("frozen SCRAMBLE descriptor malformed") from exc
    if not isinstance(raw, dict) or raw.get("schema") != "arc-reactor-mkii-scramble/v0":
        raise ValueError("frozen SCRAMBLE schema mismatch")
    strata_raw = raw.get("strata")
    if not isinstance(strata_raw, list):
        raise ValueError("frozen SCRAMBLE strata malformed")
    parsed: dict[tuple[int, int], dict[str, object]] = {}
    for item in strata_raw:
        if not isinstance(item, dict) or set(item) != {
            "budget",
            "decision_depth",
            "size",
            "offset",
            "row_ids_sha256",
        }:
            raise ValueError("frozen SCRAMBLE stratum field set mismatch")
        key = (item["budget"], item["decision_depth"])
        if key in parsed:
            raise ValueError("duplicate frozen SCRAMBLE stratum")
        parsed[key] = {
            "size": item["size"],
            "offset": item["offset"],
            "row_ids_sha256": item["row_ids_sha256"],
        }
    if parsed != EXPECTED_TRAIN_STRATA:
        raise ValueError("frozen SCRAMBLE descriptor differs from G2 custody")
    return parsed


def verify_train_corpus_against_scramble(protocol_root: str | Path) -> TrainCorpusVerification:
    protocol = Path(protocol_root)
    verify_frozen_g2_protocol(protocol)
    arenas = load_train_arenas(protocol)
    family_ids = {arena.family_id for arena in arenas}
    frozen = _read_scramble(protocol)

    grouped: dict[tuple[int, int], list[str]] = defaultdict(list)
    total_rows = 0
    for row in iter_v2_training_rows(arenas):
        if row.canonical_task_id not in family_ids:
            raise RuntimeError("V2 TRAIN row lost frozen family identity")
        grouped[(row.budget, row.decision_depth)].append(row.row_id)
        total_rows += 1

    if total_rows != EXPECTED_TRAIN_ROWS:
        raise ValueError(f"V2 TRAIN row count mismatch: {total_rows}")
    if set(grouped) != set(EXPECTED_TRAIN_STRATA):
        raise ValueError("V2 TRAIN strata set mismatch")

    actual: dict[tuple[int, int], dict[str, object]] = {}
    for key in sorted(grouped):
        ordered_ids = sorted(grouped[key])
        budget, depth = key
        payload = b"\n".join(identifier.encode("ascii") for identifier in ordered_ids)
        item = {
            "size": len(ordered_ids),
            "offset": _offset(budget, depth, len(ordered_ids)),
            "row_ids_sha256": hashlib.sha256(ROW_ID_LIST_PREFIX + payload).hexdigest(),
        }
        actual[key] = item
        if item != frozen[key]:
            raise ValueError(f"V2 TRAIN custody mismatch for stratum {key}")

    if actual != EXPECTED_TRAIN_STRATA:
        raise ValueError("V2 TRAIN corpus differs from frozen G2 SCRAMBLED constitution")

    return TrainCorpusVerification(total_rows=total_rows, strata=actual)


def g3_verify(protocol_root: str | Path) -> G3Verification:
    g2 = verify_frozen_g2_protocol(protocol_root)
    train = verify_train_corpus_against_scramble(protocol_root)
    return G3Verification(g2=g2, train=train)
