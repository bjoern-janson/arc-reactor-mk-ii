from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from .v2_census import CensusResult, run_census
from .v2_gladiator import CANONICAL_THRESHOLD, RAW_COUNTERS, SEED

SCHEMA = "arc-reactor-mkii-v2-g1-census/v0"
PREFLIGHT_BASE = "078b3cfc948262bb71604a631e17972f8ad11a1f"
EXPECTED_FILES = {"CENSUS.json", "FAMILIES.jsonl", "SHA256.txt"}


def _json_line(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _implementation_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _family_record(record) -> dict[str, object]:
    return {
        "canonical_bytes_hex": record.canonical_bytes_hex,
        "family_id": record.family_id,
        "first_counter": record.first_counter,
        "queries": list(record.queries),
    }


def _census_record(result: CensusResult) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "preflight_base": PREFLIGHT_BASE,
        "implementation_commit": _implementation_commit(),
        "seed": SEED.decode("ascii"),
        "raw_counter_count": RAW_COUNTERS,
        "canonical_threshold": CANONICAL_THRESHOLD,
        "status": result.status,
        "counts": {
            "raw_counters": result.raw_counters,
            "grammar_valid": result.grammar_valid,
            "root_matched_tie": result.root_matched_tie,
            "planner_gap": result.planner_gap,
            "feature_representable": result.feature_representable,
            "admitted_presentations": result.admitted_presentations,
            "admitted_canonical": result.admitted_canonical,
        },
    }


def _manifest_bytes(census_bytes: bytes, families_bytes: bytes) -> bytes:
    entries = {
        "CENSUS.json": hashlib.sha256(census_bytes).hexdigest(),
        "FAMILIES.jsonl": hashlib.sha256(families_bytes).hexdigest(),
    }
    return "".join(f"{entries[name]}  {name}\n" for name in sorted(entries)).encode("ascii")


def _validate_existing(out: Path) -> None:
    if not out.is_dir():
        raise ValueError("G1 custody path exists but is not a directory")
    names = {path.name for path in out.iterdir()}
    if names != EXPECTED_FILES:
        raise ValueError("G1 custody file set mismatch")
    try:
        lines = (out / "SHA256.txt").read_text(encoding="ascii").splitlines()
        recorded: dict[str, str] = {}
        for line in lines:
            digest, name = line.split("  ", 1)
            if name in recorded or name not in {"CENSUS.json", "FAMILIES.jsonl"}:
                raise ValueError
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError
            recorded[name] = digest
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError("G1 custody manifest malformed") from exc
    if set(recorded) != {"CENSUS.json", "FAMILIES.jsonl"}:
        raise ValueError("G1 custody manifest file set mismatch")
    for name, expected in recorded.items():
        actual = hashlib.sha256((out / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"G1 custody hash mismatch for {name}")


def _write_result(out: Path, result: CensusResult) -> None:
    census_bytes = _json_line(_census_record(result))
    families_bytes = b"".join(
        _json_line(_family_record(record))
        for record in sorted(result.families, key=lambda item: (item.first_counter, item.family_id))
    )
    manifest_bytes = _manifest_bytes(census_bytes, families_bytes)
    out.mkdir(parents=True, exist_ok=False)
    (out / "CENSUS.json").write_bytes(census_bytes)
    (out / "FAMILIES.jsonl").write_bytes(families_bytes)
    (out / "SHA256.txt").write_bytes(manifest_bytes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m arc_mkii.v2_g1_cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    census = subparsers.add_parser("census", help="run the frozen V2 G1 structural census")
    census.add_argument("--out", type=Path, required=True)
    census.add_argument("--workers", type=int, default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "census":
        raise RuntimeError("unreachable G1 command")
    if args.out.exists():
        _validate_existing(args.out)
        return 0
    result = run_census(workers=args.workers)
    _write_result(args.out, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
