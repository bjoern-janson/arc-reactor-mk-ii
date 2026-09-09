from __future__ import annotations

import hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Iterable

from .domain import SixQueryArena
from .v2_canonical import FAMILY_PREFIX, canonical_bytes
from .v2_gladiator import CANONICAL_THRESHOLD, RAW_COUNTERS, analyze_arena, arena_from_counter


@dataclass(frozen=True)
class FamilyRecord:
    family_id: str
    canonical_bytes_hex: str
    first_counter: int
    queries: tuple[int, int, int, int, int, int]


@dataclass
class CensusPart:
    raw_counters: int = 0
    grammar_valid: int = 0
    root_matched_tie: int = 0
    planner_gap: int = 0
    feature_representable: int = 0
    admitted_presentations: int = 0
    first_families: dict[str, FamilyRecord] = field(default_factory=dict)


@dataclass(frozen=True)
class CensusResult:
    raw_counters: int
    grammar_valid: int
    root_matched_tie: int
    planner_gap: int
    feature_representable: int
    admitted_presentations: int
    families: tuple[FamilyRecord, ...]

    @property
    def admitted_canonical(self) -> int:
        return len(self.families)

    @property
    def status(self) -> str:
        return "G1_PASS" if self.admitted_canonical >= CANONICAL_THRESHOLD else "ARENA_UNIVERSE_INSUFFICIENT"


def _family_record(counter: int, arena: SixQueryArena) -> FamilyRecord:
    canonical = canonical_bytes(arena)
    identifier = hashlib.sha256(FAMILY_PREFIX + canonical).hexdigest()
    return FamilyRecord(
        family_id=identifier,
        canonical_bytes_hex=canonical.hex(),
        first_counter=counter,
        queries=arena.queries,
    )


def scan_records(records: Iterable[tuple[int, SixQueryArena | None]]) -> CensusPart:
    part = CensusPart()
    for counter, arena in records:
        part.raw_counters += 1
        if arena is None:
            continue
        part.grammar_valid += 1
        analysis = analyze_arena(arena)
        if analysis.root_matched_tie:
            part.root_matched_tie += 1
        if analysis.planner_gap:
            part.planner_gap += 1
        if analysis.feature_representable:
            part.feature_representable += 1
        if not analysis.admitted:
            continue
        part.admitted_presentations += 1
        record = _family_record(counter, arena)
        existing = part.first_families.get(record.family_id)
        if existing is None or record.first_counter < existing.first_counter:
            part.first_families[record.family_id] = record
    return part


def merge_parts(parts: Iterable[CensusPart]) -> CensusPart:
    merged = CensusPart()
    for part in parts:
        merged.raw_counters += part.raw_counters
        merged.grammar_valid += part.grammar_valid
        merged.root_matched_tie += part.root_matched_tie
        merged.planner_gap += part.planner_gap
        merged.feature_representable += part.feature_representable
        merged.admitted_presentations += part.admitted_presentations
        for identifier, record in part.first_families.items():
            existing = merged.first_families.get(identifier)
            if existing is None or record.first_counter < existing.first_counter:
                merged.first_families[identifier] = record
    return merged


def scan_range(start: int, stop: int) -> CensusPart:
    if not 0 <= start <= stop <= RAW_COUNTERS:
        raise ValueError("range must lie inside the frozen V2 counter interval")
    return scan_records((counter, arena_from_counter(counter)) for counter in range(start, stop))


def _ranges(workers: int) -> tuple[tuple[int, int], ...]:
    if workers <= 0:
        raise ValueError("workers must be positive")
    base, remainder = divmod(RAW_COUNTERS, workers)
    ranges = []
    start = 0
    for index in range(workers):
        width = base + (1 if index < remainder else 0)
        stop = start + width
        ranges.append((start, stop))
        start = stop
    return tuple(ranges)


def _result_from_part(part: CensusPart) -> CensusResult:
    families = tuple(sorted(part.first_families.values(), key=lambda record: (record.first_counter, record.family_id)))
    return CensusResult(
        raw_counters=part.raw_counters,
        grammar_valid=part.grammar_valid,
        root_matched_tie=part.root_matched_tie,
        planner_gap=part.planner_gap,
        feature_representable=part.feature_representable,
        admitted_presentations=part.admitted_presentations,
        families=families,
    )


def run_census(workers: int = 4) -> CensusResult:
    ranges = _ranges(workers)
    if workers == 1:
        merged = scan_range(*ranges[0])
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            parts = tuple(pool.map(_scan_range_args, ranges))
        merged = merge_parts(parts)
    if merged.raw_counters != RAW_COUNTERS:
        raise RuntimeError("V2 G1 census did not cover the complete frozen counter interval")
    return _result_from_part(merged)


def _scan_range_args(bounds: tuple[int, int]) -> CensusPart:
    return scan_range(*bounds)
