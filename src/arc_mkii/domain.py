from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeAlias

Fault: TypeAlias = int
QueryMask: TypeAlias = int

FULL_MASK = 0xFF
FAULTS = tuple(range(8))


class QuerySet(Protocol):
    queries: tuple[int, ...]


def normalize_partition(mask: int) -> int:
    if not 0 <= mask <= FULL_MASK:
        raise ValueError("query mask must fit eight faults")
    if mask in (0, FULL_MASK):
        raise ValueError("query must be nonconstant")
    complement = mask ^ FULL_MASK
    return min(mask, complement)


def answer(mask: int, fault: int) -> int:
    if fault not in FAULTS:
        raise ValueError("fault must be in 0..7")
    return (mask >> fault) & 1


def candidate_child(candidate_mask: int, query: int, bit: int) -> int:
    if not 0 <= candidate_mask <= FULL_MASK:
        raise ValueError("candidate mask must fit eight faults")
    if bit not in (0, 1):
        raise ValueError("bit must be 0 or 1")
    kept = 0
    for candidate in FAULTS:
        if ((candidate_mask >> candidate) & 1) and answer(query, candidate) == bit:
            kept |= 1 << candidate
    return kept


@dataclass(frozen=True)
class Menu:
    queries: tuple[int, int, int, int]

    def __post_init__(self) -> None:
        if len(self.queries) != 4:
            raise ValueError("menu requires exactly four binary partitions")
        normalized = tuple(normalize_partition(q) for q in self.queries)
        if len(set(normalized)) != 4:
            raise ValueError("menu requires four distinct binary partitions")
        object.__setattr__(self, "queries", tuple(sorted(normalized)))


@dataclass(frozen=True)
class SixQueryArena:
    queries: tuple[int, int, int, int, int, int]

    def __post_init__(self) -> None:
        if len(self.queries) != 6:
            raise ValueError("V2 arena requires exactly six binary partitions")
        normalized = tuple(normalize_partition(q) for q in self.queries)
        if len(set(normalized)) != 6:
            raise ValueError("V2 arena requires six distinct binary partitions")
        object.__setattr__(self, "queries", normalized)
