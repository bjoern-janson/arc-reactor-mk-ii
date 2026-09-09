# ARC-MKII-V1 Gladiator Census Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement only the G1 structural-census machinery for ARC-MKII-V1 GLADIATOR, exhaust the prospectively fixed `2^20` arena stream, and stop before any V1 protocol freeze, fitting, or evaluation.

**Architecture:** Preserve the V0 learner and its four-query `Menu` behavior exactly. Introduce a separate ordered five-query `GladiatorArena` because public query order is operational in V1, generalize only the host/planner plumbing needed to handle a declared query count, then implement deterministic arena generation, matched-tie admission, five-query structural family identity, and a streaming census that retains only the 320 lowest prospectively declared split ranks. The census executable contains no fit or evaluation command.

**Tech Stack:** Python 3.13.5; Python standard library only at runtime; `pytest`; exact `fractions.Fraction`; SHA-256; JSON/JSONL.

**Spec:** `docs/superpowers/specs/2026-09-09-feedback-to-inquiry-v1-gladiator-design.md`

## Global Constraints

- Base scientific implementation is frozen at `c9897ae02829aeed31cccdaef662de4c715b312e`.
- The V0 eight-feature schema, `THETA0`, exact rational arithmetic, ridge learner, `lambda=1/100`, LEARN/SCRAMBLED/FROZEN meanings, repair rule, budgets `{2,3}`, transplant rule, resource vector, and ignition rule are not redesigned in this plan.
- This plan implements **G1 only**. It does not implement or invoke V1 training, V1 SCRAMBLED fitting, V1 evaluation, or a V1 ignition decision.
- The hidden fault universe remains exactly `0..7`.
- A V1 arena has exactly five distinct nonconstant normalized binary queries.
- Public query order is operational in V1. `GladiatorArena` must preserve tuple order exactly after per-slot normalization.
- Legacy V0 `Menu` remains exactly four queries and continues sorting normalized query masks exactly as before.
- The raw V1 universe is exactly `2^20 = 1_048_576` counters with seed `arc-reactor-mk-ii/v1-gladiator/menu-seed/2026-09-09`.
- Arena admission may inspect only query truth tables, the frozen feature map, `THETA0`/FROZEN choice, and exact planner continuation value. It may not inspect fitted LEARN or SCRAMBLED state.
- The canonical-family threshold is exactly `320`; it is not changed after census.
- If fewer than 320 canonical families survive, record `ARENA_UNIVERSE_INSUFFICIENT` and stop.
- If at least 320 survive, record `PASS` and the deterministic top 320 structural records, then stop. G2 requires a separate implementation plan.

---

## File Map

- Modify: `src/arc_mkii/domain.py` — add a structural `QuerySet` protocol and ordered five-query `GladiatorArena`; leave V0 `Menu` behavior unchanged.
- Modify: `src/arc_mkii/host.py` — derive available query IDs from `len(menu.queries)` instead of the literal four.
- Modify: `src/arc_mkii/planner.py` — expose exact state-level planner value and derive root query IDs from declared query count.
- Create: `src/arc_mkii/gladiator.py` — V1 raw generator and structural matched-tie admission analysis.
- Create: `src/arc_mkii/gladiator_canonical.py` — five-query family identity, invariant to fault names/query names/answer complement.
- Create: `src/arc_mkii/gladiator_census.py` — streaming G1 census, canonical deduplication, bounded top-320 retention, deterministic records.
- Create: `src/arc_mkii/gladiator_cli.py` — census-only CLI and deterministic census serialization.
- Create: `tests/test_gladiator_domain.py`
- Create: `tests/test_gladiator_planner.py`
- Create: `tests/test_gladiator.py`
- Create: `tests/test_gladiator_canonical.py`
- Create: `tests/test_gladiator_census.py`
- Create: `tests/test_gladiator_cli.py`
- Create during G1 execution: `experiments/v1/census/CENSUS.json`
- Create during G1 execution: `experiments/v1/census/TOP_320.jsonl`
- Create during G1 execution: `experiments/v1/census/SHA256.txt`

---

### Task 1: Preserve V0 `Menu` and add ordered five-query `GladiatorArena`

**Files:**
- Modify: `src/arc_mkii/domain.py`
- Create: `tests/test_gladiator_domain.py`

**Interfaces:**
- Consumes: existing `normalize_partition(mask)`.
- Produces: `QuerySet` protocol and `GladiatorArena(queries)` with exactly five normalized, distinct, order-preserving query masks.

- [ ] **Step 1: Write the failing domain tests**

```python
from arc_mkii.domain import GladiatorArena, Menu


def test_gladiator_arena_preserves_public_slot_order():
    arena = GladiatorArena((89, 16, 45, 4, 46))
    assert arena.queries == (89, 16, 45, 4, 46)


def test_gladiator_arena_requires_five_distinct_nonconstant_queries():
    try:
        GladiatorArena((1, 2, 3, 4, 4))
    except ValueError as exc:
        assert "five distinct" in str(exc)
    else:
        raise AssertionError("duplicate Gladiator query was accepted")


def test_legacy_v0_menu_still_sorts_four_queries():
    menu = Menu((85, 15, 51, 23))
    assert menu.queries == (15, 23, 51, 85)
```

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```bash
python -m pytest tests/test_gladiator_domain.py -q
```

Expected: import failure because `GladiatorArena` does not yet exist.

- [ ] **Step 3: Implement the structural protocol and ordered arena without changing `Menu`**

Add to `src/arc_mkii/domain.py`:

```python
from typing import Protocol, TypeAlias


class QuerySet(Protocol):
    queries: tuple[int, ...]


@dataclass(frozen=True)
class GladiatorArena:
    queries: tuple[int, int, int, int, int]

    def __post_init__(self) -> None:
        if len(self.queries) != 5:
            raise ValueError("Gladiator arena requires exactly five binary partitions")
        normalized = tuple(normalize_partition(q) for q in self.queries)
        if len(set(normalized)) != 5:
            raise ValueError("Gladiator arena requires five distinct binary partitions")
        # Intentionally do not sort: slot order is operational in V1.
        object.__setattr__(self, "queries", normalized)
```

Do not alter the existing `Menu.__post_init__` implementation.

- [ ] **Step 4: Run new and legacy domain tests**

Run:

```bash
python -m pytest tests/test_gladiator_domain.py tests/test_domain.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/domain.py tests/test_gladiator_domain.py
git commit -m "feat: add ordered V1 Gladiator arena domain"
```

---

### Task 2: Generalize host/planner query-count plumbing while preserving V0 behavior

**Files:**
- Modify: `src/arc_mkii/host.py`
- Modify: `src/arc_mkii/planner.py`
- Create: `tests/test_gladiator_planner.py`

**Interfaces:**
- Consumes: `QuerySet`, `Menu`, `GladiatorArena`, `candidate_child`.
- Produces: `initial_state(menu: QuerySet, fault: int, budget: int)`, `planner_state_reference(menu, candidate_mask, remaining_query_ids, budget, resources=None) -> PlannerResult`; existing `planner_reference` and `planner_success_count` remain available.

- [ ] **Step 1: Write failing five-query plumbing tests plus a V0 regression**

```python
from arc_mkii.domain import FULL_MASK, GladiatorArena, Menu, candidate_child
from arc_mkii.host import initial_state
from arc_mkii.planner import planner_state_reference, planner_success_count


WITNESS = GladiatorArena((16, 46, 89, 4, 45))


def test_five_query_host_exposes_all_public_query_ids():
    state = initial_state(WITNESS, fault=0, budget=3)
    assert state.remaining_query_ids == (0, 1, 2, 3, 4)


def test_state_planner_certifies_witness_frozen_route_value_six():
    q_f = 1
    remaining = (0, 2, 3, 4)
    values = [
        planner_state_reference(
            WITNESS,
            candidate_child(FULL_MASK, WITNESS.queries[q_f], bit),
            remaining,
            2,
        ).success_count
        for bit in (0, 1)
    ]
    assert values == [3, 3]
    assert sum(values) == 6


def test_v0_planner_control_remains_eight_of_eight():
    assert planner_success_count(Menu((15, 23, 51, 85)), budget=3) == 8
```

- [ ] **Step 2: Run and verify RED**

Run:

```bash
python -m pytest tests/test_gladiator_planner.py -q
```

Expected: five-query host assertion fails and/or `planner_state_reference` import fails.

- [ ] **Step 3: Generalize host typing/count only**

In `src/arc_mkii/host.py`:

```python
from .domain import FAULTS, FULL_MASK, QuerySet, answer, candidate_child
```

Change the `menu` annotation in `SelectorView` and `HostState` from `Menu` to `QuerySet`, change `initial_state(menu: QuerySet, ...)`, and replace:

```python
remaining_query_ids=tuple(range(4))
```

with:

```python
remaining_query_ids=tuple(range(len(menu.queries)))
```

Do not change belief filtering, observations, repair, resource accounting, or terminal semantics.

- [ ] **Step 4: Refactor planner into state-level exact reference**

In `src/arc_mkii/planner.py`, use `QuerySet` and implement:

```python
def planner_state_reference(
    menu: QuerySet,
    candidate_mask: int,
    remaining_query_ids: tuple[int, ...],
    budget: int,
    resources: ResourceCounter | None = None,
) -> PlannerResult:
    if budget < 0:
        raise ValueError("budget must be nonnegative")
    states_expanded = 0

    @lru_cache(maxsize=None)
    def solve(
        mask: int,
        remaining: tuple[int, ...],
        remaining_budget: int,
    ) -> int:
        nonlocal states_expanded
        states_expanded += 1
        if mask == 0:
            return 0
        if mask.bit_count() == 1 or remaining_budget <= 0 or not remaining:
            return 1
        best = 1
        for query_id in remaining:
            query_mask = menu.queries[query_id]
            if resources is not None:
                resources.public_truth_table_bit_inspections += 2 * mask.bit_count()
            child0 = candidate_child(mask, query_mask, 0)
            child1 = candidate_child(mask, query_mask, 1)
            if child0 == 0 or child1 == 0:
                continue
            next_queries = tuple(q for q in remaining if q != query_id)
            value = solve(child0, next_queries, remaining_budget - 1) + solve(
                child1, next_queries, remaining_budget - 1
            )
            if value > best:
                best = value
        return best

    success_count = solve(candidate_mask, tuple(remaining_query_ids), budget)
    if resources is not None:
        resources.planner_states_expanded += states_expanded
    return PlannerResult(success_count=success_count, states_expanded=states_expanded)
```

Then make existing `planner_reference` a wrapper:

```python
def planner_reference(
    menu: QuerySet,
    budget: int,
    resources: ResourceCounter | None = None,
) -> PlannerResult:
    return planner_state_reference(
        menu,
        FULL_MASK,
        tuple(range(len(menu.queries))),
        budget,
        resources=resources,
    )
```

Do not change `planner_success_count` semantics.

- [ ] **Step 5: Run focused and full V0 tests**

Run:

```bash
python -m pytest tests/test_gladiator_planner.py tests/test_host.py tests/test_planner.py -q
python -m pytest -q
```

Expected: all existing V0 tests and new tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/host.py src/arc_mkii/planner.py tests/test_gladiator_planner.py
git commit -m "refactor: support declared query counts without changing V0"
```

---

### Task 3: Implement the prospective raw generator and Gladiator admission analysis

**Files:**
- Create: `src/arc_mkii/gladiator.py`
- Create: `tests/test_gladiator.py`

**Interfaces:**
- Consumes: `GladiatorArena`, `SelectorView`, `feature_vector`, `THETA0`, `choose_query`, `planner_state_reference`.
- Produces: `arena_from_counter(counter) -> GladiatorArena | None`, `analyze_arena(arena) -> ArenaAnalysis`, and constants `RAW_COUNTERS`, `SEED`, `CANONICAL_THRESHOLD`.

- [ ] **Step 1: Write deterministic-generator and exact-witness tests**

```python
from arc_mkii.domain import GladiatorArena
from arc_mkii.gladiator import (
    CANONICAL_THRESHOLD,
    RAW_COUNTERS,
    arena_from_counter,
    analyze_arena,
)


WITNESS = GladiatorArena((16, 46, 89, 4, 45))


def test_raw_universe_constants_are_frozen():
    assert RAW_COUNTERS == 1_048_576
    assert CANONICAL_THRESHOLD == 320


def test_counter_zero_has_exact_prospective_query_slots():
    arena = arena_from_counter(0)
    assert arena is not None
    assert arena.queries == (67, 75, 92, 96, 91)


def test_hand_checkable_gladiator_witness_has_matched_tie_and_headroom():
    analysis = analyze_arena(WITNESS)
    assert analysis.root_matched_tie
    assert analysis.tied_queries == (1, 2, 4)
    assert analysis.frozen_query == 1
    assert dict(analysis.continuation_values) == {1: 6, 2: 8, 4: 8}
    assert analysis.planner_gap
    assert analysis.optimal_tied_queries == (2, 4)
    assert analysis.feature_representable
    assert analysis.admitted
```

- [ ] **Step 2: Run and verify RED**

Run:

```bash
python -m pytest tests/test_gladiator.py -q
```

Expected: import failure because `arc_mkii.gladiator` does not exist.

- [ ] **Step 3: Implement the exact raw counter generator**

In `src/arc_mkii/gladiator.py`:

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction

from .domain import FULL_MASK, GladiatorArena, candidate_child
from .features import feature_vector
from .host import SelectorView
from .planner import planner_state_reference
from .selector import THETA0, choose_query

RAW_COUNTERS = 1 << 20
CANONICAL_THRESHOLD = 320
SEED = b"arc-reactor-mk-ii/v1-gladiator/menu-seed/2026-09-09"


def _partition_from(counter: int, slot: int) -> int:
    if not 0 <= counter < RAW_COUNTERS:
        raise ValueError("counter outside frozen V1 raw universe")
    if not 0 <= slot < 5:
        raise ValueError("slot must be in 0..4")
    payload = SEED + counter.to_bytes(8, "big") + slot.to_bytes(1, "big")
    digest = hashlib.sha256(payload).digest()
    return 1 + (int.from_bytes(digest[:8], "big") % 127)


def arena_from_counter(counter: int) -> GladiatorArena | None:
    queries = tuple(_partition_from(counter, slot) for slot in range(5))
    if len(set(queries)) != 5:
        return None
    return GladiatorArena(queries)
```

- [ ] **Step 4: Implement exact structural analysis**

Use this frozen record shape:

```python
@dataclass(frozen=True)
class ArenaAnalysis:
    root_matched_tie: bool
    tied_queries: tuple[int, ...]
    frozen_query: int | None
    continuation_values: tuple[tuple[int, int], ...]
    planner_gap: bool
    optimal_tied_queries: tuple[int, ...]
    feature_representable: bool

    @property
    def admitted(self) -> bool:
        return self.root_matched_tie and self.planner_gap and self.feature_representable
```

Implement helpers:

```python
def _root_view(arena: GladiatorArena) -> SelectorView:
    return SelectorView(
        menu=arena,
        candidate_mask=FULL_MASK,
        remaining_query_ids=tuple(range(5)),
        remaining_budget=3,
        observations=(),
    )


def _balance(arena: GladiatorArena, query_id: int) -> Fraction:
    q = arena.queries[query_id]
    n0 = candidate_child(FULL_MASK, q, 0).bit_count()
    n1 = candidate_child(FULL_MASK, q, 1).bit_count()
    return Fraction(min(n0, n1), 8)


def _continuation_value(arena: GladiatorArena, query_id: int) -> int:
    remaining = tuple(q for q in range(5) if q != query_id)
    query = arena.queries[query_id]
    return sum(
        planner_state_reference(
            arena,
            candidate_child(FULL_MASK, query, bit),
            remaining,
            2,
        ).success_count
        for bit in (0, 1)
    )
```

`analyze_arena` must:

1. Compute all five root balances.
2. Return a non-admitted `ArenaAnalysis` immediately unless the maximum balance is exactly `1/2` and at least two queries share it.
3. Build the root view and compute `frozen_query = choose_query(THETA0, view)`. Assert it belongs to the tied maximum set; raise `RuntimeError` if not.
4. Compute continuation values only for tied maximum queries.
5. Set `planner_gap` iff `max(V2)-V2(frozen_query) >= 2`.
6. If no planner gap, return without feature gating.
7. Let `optimal_tied_queries` be tied queries attaining the maximum continuation value.
8. Compare frozen root features `weighted_best_next_split` (index 6) and `worst_child_best_next_split` (index 7) against each continuation-optimal tied query. Set `feature_representable` iff some optimal query has strictly greater worst-child score, or equal worst-child score and strictly greater weighted score.

No fitted coefficient or feedback value is loaded anywhere in this module.

- [ ] **Step 5: Run witness tests and existing feature/selector controls**

Run:

```bash
python -m pytest tests/test_gladiator.py tests/test_features.py tests/test_selector.py -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/gladiator.py tests/test_gladiator.py
git commit -m "feat: add V1 Gladiator arena admission rule"
```

---

### Task 4: Add five-query structural family identity

**Files:**
- Create: `src/arc_mkii/gladiator_canonical.py`
- Create: `tests/test_gladiator_canonical.py`

**Interfaces:**
- Consumes: `GladiatorArena`, `answer`.
- Produces: `canonical_bytes_v1(arena) -> bytes`, `family_id(arena) -> str`.

- [ ] **Step 1: Write invariance and non-equivalence tests**

```python
from arc_mkii.domain import GladiatorArena
from arc_mkii.gladiator_canonical import canonical_bytes_v1, family_id


def permute_faults(mask: int, permutation: tuple[int, ...]) -> int:
    out = 0
    for old_fault, new_fault in enumerate(permutation):
        if (mask >> old_fault) & 1:
            out |= 1 << new_fault
    return out


def test_v1_family_identity_ignores_query_and_fault_names():
    base = GladiatorArena((16, 46, 89, 4, 45))
    fault_permutation = (7, 6, 5, 4, 3, 2, 1, 0)
    renamed = GladiatorArena(
        tuple(
            permute_faults(q, fault_permutation)
            for q in reversed(base.queries)
        )
    )
    assert canonical_bytes_v1(base) == canonical_bytes_v1(renamed)
    assert family_id(base) == family_id(renamed)


def test_v1_canonical_bytes_are_eight_row_bytes():
    assert len(canonical_bytes_v1(GladiatorArena((16, 46, 89, 4, 45)))) == 8


def test_structurally_different_five_query_arenas_can_differ():
    left = GladiatorArena((16, 46, 89, 4, 45))
    right = GladiatorArena((67, 75, 92, 96, 91))
    assert family_id(left) != family_id(right)
```

- [ ] **Step 2: Run and verify RED**

Run:

```bash
python -m pytest tests/test_gladiator_canonical.py -q
```

Expected: import failure because `gladiator_canonical` does not exist.

- [ ] **Step 3: Implement exhaustive five-column canonicalization**

Create `src/arc_mkii/gladiator_canonical.py`:

```python
from __future__ import annotations

import hashlib
import itertools

from .domain import GladiatorArena, answer


def canonical_bytes_v1(arena: GladiatorArena) -> bytes:
    best: bytes | None = None
    for perm in itertools.permutations(range(5)):
        for complement_bits in range(32):
            rows: list[int] = []
            for fault in range(8):
                row = 0
                for out_col, source_col in enumerate(perm):
                    bit = answer(arena.queries[source_col], fault)
                    if (complement_bits >> out_col) & 1:
                        bit ^= 1
                    row |= bit << out_col
                rows.append(row)
            candidate = bytes(sorted(rows))
            if best is None or candidate < best:
                best = candidate
    if best is None:
        raise RuntimeError("V1 canonicalization produced no candidate")
    return best


def family_id(arena: GladiatorArena) -> str:
    payload = b"arc-mkii-v1-gladiator-task\0" + canonical_bytes_v1(arena)
    return hashlib.sha256(payload).hexdigest()
```

Sorting row signatures supplies fault-name invariance; column permutation supplies query-name invariance; complement enumeration supplies binary-answer-convention invariance. Operational query order remains preserved in the `GladiatorArena`; only the family identifier quotients it out for train/eval freshness.

- [ ] **Step 4: Run canonical tests and V0 canonical regression**

Run:

```bash
python -m pytest tests/test_gladiator_canonical.py tests/test_canonical.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/gladiator_canonical.py tests/test_gladiator_canonical.py
git commit -m "feat: add V1 Gladiator structural family identity"
```

---

### Task 5: Implement streaming census and bounded top-320 retention

**Files:**
- Create: `src/arc_mkii/gladiator_census.py`
- Create: `tests/test_gladiator_census.py`

**Interfaces:**
- Consumes: `arena_from_counter`, `analyze_arena`, `family_id`, `RAW_COUNTERS`, `CANONICAL_THRESHOLD`.
- Produces: `split_rank(family_id: str) -> str`, `CensusCounts`, `SelectedArena`, `CensusResult`, `run_structural_census(raw_counters=RAW_COUNTERS) -> CensusResult`.

- [ ] **Step 1: Write real deterministic census invariants on a small prefix**

```python
from arc_mkii.gladiator import CANONICAL_THRESHOLD
from arc_mkii.gladiator_census import run_structural_census, split_rank


def test_split_rank_is_exact_domain_separated_sha256():
    fid = "00" * 32
    assert split_rank(fid) == "9f96bd1162804db47faec400796ed45d73ea835fa802b4720ca0096999a1c185"


def test_small_real_census_is_deterministic_and_stage_counts_are_monotone():
    left = run_structural_census(raw_counters=64)
    right = run_structural_census(raw_counters=64)
    assert left == right
    c = left.counts
    assert c.raw_counters == 64
    assert 0 <= c.grammar_valid <= c.raw_counters
    assert 0 <= c.root_matched_tie <= c.grammar_valid
    assert 0 <= c.planner_gap <= c.root_matched_tie
    assert 0 <= c.feature_representable <= c.planner_gap
    assert 0 <= c.admitted_canonical <= c.feature_representable
    assert len(left.selected) <= min(CANONICAL_THRESHOLD, c.admitted_canonical)
```

The expected split-rank literal above is the SHA-256 hex digest of:

```python
b"arc-mkii-v1-gladiator-split\0" + ("00" * 32).encode("ascii")
```

Before implementing, independently calculate that digest with a one-line Python command and correct the test literal if the displayed value is inconsistent. This is a test-fixture calculation only; it does not inspect any arena outcome.

- [ ] **Step 2: Run and verify RED**

Run:

```bash
python -m pytest tests/test_gladiator_census.py -q
```

Expected: import failure because `gladiator_census` does not exist.

- [ ] **Step 3: Implement census records and split rank**

Create:

```python
from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass

from .gladiator import CANONICAL_THRESHOLD, RAW_COUNTERS, arena_from_counter, analyze_arena
from .gladiator_canonical import family_id


@dataclass(frozen=True)
class CensusCounts:
    raw_counters: int
    grammar_valid: int
    root_matched_tie: int
    planner_gap: int
    feature_representable: int
    admitted_presentations: int
    admitted_canonical: int


@dataclass(frozen=True)
class SelectedArena:
    split_rank: str
    family_id: str
    raw_counter: int
    queries: tuple[int, int, int, int, int]
    frozen_query: int
    tied_queries: tuple[int, ...]
    continuation_values: tuple[tuple[int, int], ...]
    optimal_tied_queries: tuple[int, ...]


@dataclass(frozen=True)
class CensusResult:
    counts: CensusCounts
    selected: tuple[SelectedArena, ...]

    @property
    def status(self) -> str:
        if self.counts.admitted_canonical >= CANONICAL_THRESHOLD:
            return "PASS"
        return "ARENA_UNIVERSE_INSUFFICIENT"


def split_rank(canonical_family_id: str) -> str:
    if len(canonical_family_id) != 64:
        raise ValueError("family id must be 64 lowercase hex characters")
    int(canonical_family_id, 16)
    payload = b"arc-mkii-v1-gladiator-split\0" + canonical_family_id.encode("ascii")
    return hashlib.sha256(payload).hexdigest()
```

- [ ] **Step 4: Implement streaming census without retaining the raw universe**

`run_structural_census` must:

```python
def run_structural_census(raw_counters: int = RAW_COUNTERS) -> CensusResult:
    if not 0 <= raw_counters <= RAW_COUNTERS:
        raise ValueError("raw_counters outside frozen V1 universe")

    grammar_valid = 0
    root_matched_tie = 0
    planner_gap = 0
    feature_representable = 0
    admitted_presentations = 0
    seen_families: set[str] = set()
    selected: list[tuple[tuple[str, str], SelectedArena]] = []

    for counter in range(raw_counters):
        arena = arena_from_counter(counter)
        if arena is None:
            continue
        grammar_valid += 1

        analysis = analyze_arena(arena)
        if not analysis.root_matched_tie:
            continue
        root_matched_tie += 1
        if not analysis.planner_gap:
            continue
        planner_gap += 1
        if not analysis.feature_representable:
            continue
        feature_representable += 1
        admitted_presentations += 1

        fid = family_id(arena)
        if fid in seen_families:
            continue
        seen_families.add(fid)

        rank = split_rank(fid)
        if analysis.frozen_query is None:
            raise RuntimeError("admitted arena has no frozen root query")
        record = SelectedArena(
            split_rank=rank,
            family_id=fid,
            raw_counter=counter,
            queries=arena.queries,
            frozen_query=analysis.frozen_query,
            tied_queries=analysis.tied_queries,
            continuation_values=analysis.continuation_values,
            optimal_tied_queries=analysis.optimal_tied_queries,
        )
        key = (rank, fid)
        bisect.insort(selected, (key, record))
        if len(selected) > CANONICAL_THRESHOLD:
            selected.pop()

    counts = CensusCounts(
        raw_counters=raw_counters,
        grammar_valid=grammar_valid,
        root_matched_tie=root_matched_tie,
        planner_gap=planner_gap,
        feature_representable=feature_representable,
        admitted_presentations=admitted_presentations,
        admitted_canonical=len(seen_families),
    )
    return CensusResult(counts=counts, selected=tuple(record for _, record in selected))
```

This retains only the set of seen 64-hex family IDs plus at most 320 full arena records. It never retains one million raw arenas.

- [ ] **Step 5: Run census unit tests**

Run:

```bash
python -m pytest tests/test_gladiator_census.py -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/gladiator_census.py tests/test_gladiator_census.py
git commit -m "feat: add bounded V1 Gladiator structural census"
```

---

### Task 6: Add a census-only CLI and deterministic custody artifacts

**Files:**
- Create: `src/arc_mkii/gladiator_cli.py`
- Create: `tests/test_gladiator_cli.py`

**Interfaces:**
- Consumes: `run_structural_census()`.
- Produces: `census --out DIR`; deterministic `CENSUS.json`, `TOP_320.jsonl`, `SHA256.txt`.

- [ ] **Step 1: Write CLI separation and serialization tests**

```python
import hashlib
import json

from arc_mkii.gladiator_cli import build_parser, write_census


def test_gladiator_cli_exposes_census_only():
    parser = build_parser()
    help_text = parser.format_help()
    assert "census" in help_text
    assert "fit" not in help_text
    assert "evaluate" not in help_text


def test_small_census_write_is_deterministic_and_self_hashed(tmp_path):
    out = tmp_path / "census"
    write_census(out, raw_counters=64)
    first = {path.name: path.read_bytes() for path in out.iterdir()}
    write_census(out, raw_counters=64)
    second = {path.name: path.read_bytes() for path in out.iterdir()}
    assert first == second
    assert set(first) == {"CENSUS.json", "TOP_320.jsonl", "SHA256.txt"}

    meta = json.loads(first["CENSUS.json"])
    assert meta["schema"] == "arc-reactor-mkii-v1-gladiator-census/v0"
    assert meta["raw_counters"] == 64

    recorded = {}
    for line in first["SHA256.txt"].decode("ascii").splitlines():
        digest, name = line.split("  ", 1)
        recorded[name] = digest
    assert recorded == {
        name: hashlib.sha256(first[name]).hexdigest()
        for name in ("CENSUS.json", "TOP_320.jsonl")
    }
```

- [ ] **Step 2: Run and verify RED**

Run:

```bash
python -m pytest tests/test_gladiator_cli.py -q
```

Expected: import failure because `gladiator_cli` does not exist.

- [ ] **Step 3: Implement deterministic record conversion**

`TOP_320.jsonl` records must have exactly these keys:

```python
{
    "split_rank": record.split_rank,
    "family_id": record.family_id,
    "raw_counter": record.raw_counter,
    "queries": list(record.queries),
    "frozen_query": record.frozen_query,
    "tied_queries": list(record.tied_queries),
    "continuation_values": [
        {"query_id": query_id, "value": value}
        for query_id, value in record.continuation_values
    ],
    "optimal_tied_queries": list(record.optimal_tied_queries),
}
```

Serialize JSON with `sort_keys=True`, compact separators, UTF-8, and one LF terminator per record.

`CENSUS.json` must contain exactly:

```python
{
    "schema": "arc-reactor-mkii-v1-gladiator-census/v0",
    "seed": "arc-reactor-mk-ii/v1-gladiator/menu-seed/2026-09-09",
    "raw_counters": result.counts.raw_counters,
    "threshold": 320,
    "status": result.status,
    "counts": {
        "grammar_valid": result.counts.grammar_valid,
        "root_matched_tie": result.counts.root_matched_tie,
        "planner_gap": result.counts.planner_gap,
        "feature_representable": result.counts.feature_representable,
        "admitted_presentations": result.counts.admitted_presentations,
        "admitted_canonical": result.counts.admitted_canonical,
    },
    "selected_count": len(result.selected),
}
```

`SHA256.txt` contains the SHA-256 of `CENSUS.json` and `TOP_320.jsonl` in lexicographic filename order.

- [ ] **Step 4: Implement idempotent census-only command**

`write_census(out, raw_counters=RAW_COUNTERS)` must compute the complete result when `out` does not exist. If `out` exists, it must verify the exact three-file set and both hashes from `SHA256.txt`; if valid, return without rerunning the million-counter census. Any mismatch raises `FileExistsError`.

`build_parser()` exposes one subcommand only:

```text
census --out DIR
```

`main()` invokes `write_census(args.out)` and returns zero whether census status is `PASS` or `ARENA_UNIVERSE_INSUFFICIENT`; scientific gating is read from the immutable `status` field, not from shell-error semantics.

Do not import `fit`, `artifact`, `scramble`, `evaluate`, or the V0 `cli` module in `gladiator_cli.py`.

- [ ] **Step 5: Run CLI and full regression tests**

Run:

```bash
python -m pytest tests/test_gladiator_cli.py -q
python -m pytest -q
```

Expected: all V0 and V1-G1 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/gladiator_cli.py tests/test_gladiator_cli.py
git commit -m "feat: add V1 Gladiator census-only execution gate"
```

---

### Task 7: Freeze G1 implementation, execute the full structural census once, and STOP

**Files:**
- Create at execution time: `experiments/v1/census/CENSUS.json`
- Create at execution time: `experiments/v1/census/TOP_320.jsonl`
- Create at execution time: `experiments/v1/census/SHA256.txt`

**Interfaces:**
- Consumes: the completed G1 implementation only.
- Produces: a frozen structural census result and exact gate status. No learner output.

- [ ] **Step 1: Fresh verification before the million-counter execution**

Run:

```bash
python --version
python -m pytest -q
git status --short
git rev-parse HEAD
```

Required Python: `3.13.5`.
Required tests: zero failures.
Required working tree: clean.
Record the exact HEAD in the handoff as `CENSUS_IMPLEMENTATION_ID_V1`.

- [ ] **Step 2: Execute the frozen structural census exactly once**

Run:

```bash
python -m arc_mkii.gladiator_cli census --out experiments/v1/census
```

This command may inspect only structural arena data. It must not fit or load LEARN/SCRAMBLED artifacts.

- [ ] **Step 3: Verify census custody without rerunning it**

Run:

```bash
python - <<'PY'
import hashlib
import json
from pathlib import Path

root = Path("experiments/v1/census")
meta = json.loads((root / "CENSUS.json").read_text())
lines = (root / "SHA256.txt").read_text(encoding="ascii").splitlines()
recorded = dict(line.split("  ", 1) for line in lines)
for name in ("CENSUS.json", "TOP_320.jsonl"):
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    assert recorded[name] == actual, (name, recorded[name], actual)

selected = [line for line in (root / "TOP_320.jsonl").read_text().splitlines() if line]
assert len(selected) == meta["selected_count"]
assert meta["raw_counters"] == 1_048_576
assert meta["threshold"] == 320
assert meta["status"] in {"PASS", "ARENA_UNIVERSE_INSUFFICIENT"}
if meta["status"] == "PASS":
    assert meta["counts"]["admitted_canonical"] >= 320
    assert meta["selected_count"] == 320
else:
    assert meta["counts"]["admitted_canonical"] < 320
    assert meta["selected_count"] == meta["counts"]["admitted_canonical"]
print(json.dumps(meta, sort_keys=True, indent=2))
PY
```

- [ ] **Step 4: Commit the census record, with outcome-neutral commit logic**

If status is `PASS`:

```bash
git add experiments/v1/census
git commit -m "record: freeze V1 Gladiator structural census"
```

If status is `ARENA_UNIVERSE_INSUFFICIENT`:

```bash
git add experiments/v1/census
git commit -m "record: close V1 Gladiator insufficient arena census"
```

The commit records the structural gate; neither path authorizes training.

- [ ] **Step 5: Record final G1 custody and STOP**

Run:

```bash
git rev-parse HEAD
git status --short
python -m pytest -q
```

Record the exact HEAD as `GLADIATOR_G1_RECORD_ID_V1`.

**HARD STOP:**

- If `ARENA_UNIVERSE_INSUFFICIENT`, do not weaken the grammar, threshold, seed, or counter window in this execution session. There is no V1 learning result.
- If `PASS`, do not implement G2, do not freeze TRAIN/EVAL manifests, do not build a five-query training corpus, and do not fit LEARN or SCRAMBLED. Return the G1 census to the user. A separate approved G2 implementation plan is required.

---

## Plan Self-Review Record

**Spec coverage:**

- Fixed learner / changed chamber: preserved; no learner code is redesigned.
- Five primitive queries with operational public order: Task 1 uses a separate order-preserving `GladiatorArena` rather than changing V0 `Menu` semantics.
- V0 behavior preservation: Tasks 1–2 keep legacy `Menu` sorting and run the full V0 test suite after query-count plumbing changes.
- Frozen raw universe and seed: Task 3.
- Root 4/4 matched tie: Task 3.
- Frozen FROZEN tie decision: Task 3 calls the actual `THETA0` selector.
- Exact two-query continuation value and >=2 headroom: Tasks 2–3.
- Frozen-feature representability gate: Task 3.
- Five-query structural family identity: Task 4.
- Canonicalization only after structural admission: Task 5 loop order.
- Fixed 320 census threshold: Tasks 3, 5, 7.
- Prospectively declared split rank: Task 5.
- Memory economy: Task 5 retains only seen family IDs and the best 320 complete records.
- Census-only execution surface: Task 6 contains no fit/evaluate command.
- G1 structural census before any training: Task 7.
- Stop on insufficient universe; separate G2 after pass: Task 7.

**Placeholder scan:** no `TBD`, `TODO`, “implement later”, or unspecified test/code step remains.

**Type consistency:** `GladiatorArena` satisfies `QuerySet`; `SelectorView`, host, and planner consume `QuerySet`; V1 analysis passes `GladiatorArena` directly; family identity consumes the same arena type; census records use the exact `ArenaAnalysis` fields defined in Task 3.

**Deliberate scope reduction:** this plan stops at G1 rather than implementing G2–G4 prematurely. If the arena universe fails the frozen `>=320` gate, no training/protocol implementation work has been wasted. If it passes, the retained deterministic top 320 records are sufficient input for the subsequent G2 plan without rerunning or storing the entire million-arena stream.
