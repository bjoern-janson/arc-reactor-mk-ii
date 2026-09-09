# ARC-MKII-V2 G1 Six-Query Census Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and execute only the V2 G1 structural census over the prospectively frozen six-query universe, decide whether at least 320 canonical structural families exist, fossilize that construction-gate result, and stop before G2, fitting, or evaluation.

**Architecture:** Create the implementation branch/worktree **directly from** frozen executable preflight base `078b3cfc948262bb71604a631e17972f8ad11a1f`; do not merge the planning branch into executable ancestry. Preserve the four-query V0 `Menu` exactly, add a separate order-preserving six-query arena type, generalize only query-count-dependent host/planner plumbing, then implement the frozen V2 generator, structural admission, exact six-query family quotient, deterministic shardable census, and a census-only CLI. The G1 executable imports no fitting/evaluation/corpus/scramble/artifact machinery and exposes no command other than `census`.

**Tech Stack:** Python 3.13; Python standard library only at runtime; `pytest`; exact `fractions.Fraction`; SHA-256; JSON/JSONL; `concurrent.futures.ProcessPoolExecutor` for deterministic execution sharding only.

**Spec:** `docs/superpowers/specs/2026-09-09-feedback-to-inquiry-v2-six-query-gladiator-design.md`

## Global Constraints

- Immutable executable ancestry: `freeze/v2-preflight-base@078b3cfc948262bb71604a631e17972f8ad11a1f`.
- Implementation branch must be created from that SHA itself. The plan branch is documentation only and must not become executable ancestry.
- Frozen V0 scientific mechanism remains `c9897ae02829aeed31cccdaef662de4c715b312e`; G0.5 already certifies its scientific observable vector against the preflight base.
- This plan implements **V2 G1 only**. It must not freeze a TRAIN/EVAL split, build V2 training rows, fit LEARN/SCRAMBLED, evaluate any arm, or compute V2 ignition.
- The hidden fault universe remains exactly `0..7`.
- A V2 arena contains exactly six distinct nonconstant normalized binary queries.
- Public query order is operational and must be preserved by the V2 arena type.
- Legacy V0 `Menu` remains exactly four queries and continues sorting normalized masks exactly as before.
- The frozen V2 raw universe is exactly `1_048_576` counters.
- Frozen V2 seed: `arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001`.
- Do not inspect V2 admission/canonical-family yield on any prefix before the official G1 result-bearing census. Generator fixtures may verify raw mask derivation only.
- Admission may inspect only public query truth tables, the frozen feature map, `THETA0`/FROZEN root choice, and exact planner continuation values.
- Canonical-family threshold is exactly `320` and cannot change after census.
- `<320` canonical families means `ARENA_UNIVERSE_INSUFFICIENT -> STOP -> NO TRAINING -> NO V2 RESULT`.
- `>=320` means `G1_PASS -> G2_AUTHORIZED_ONLY`; it does **not** authorize fitting or evaluation.
- Historical V0 resource numbers remain historical. Corrected resource accounting applies prospectively and must not be back-written into V0 records.
- The existing G0.5 fossil/workflow remains untouched. V2 G1 gets a separate V0 semantic-regression check because G1 necessarily adds new query-count plumbing.

---

## File Map

- Modify: `src/arc_mkii/domain.py` — add `QuerySet` protocol and separate ordered `SixQueryArena`; leave V0 `Menu` behavior unchanged.
- Modify: `src/arc_mkii/host.py` — derive available query IDs from `len(menu.queries)` only.
- Modify: `src/arc_mkii/planner.py` — add state-level exact planner entry point and generic query-count root plumbing.
- Create: `src/arc_mkii/v2_gladiator.py` — frozen V2 generator and structural admission.
- Create: `src/arc_mkii/v2_canonical.py` — exact six-query structural-family quotient and family ID.
- Create: `src/arc_mkii/v2_census.py` — deterministic scan, shard merge, first-admitted-family retention, and G1 status.
- Create: `src/arc_mkii/v2_g1_cli.py` — census-only CLI and custody serialization.
- Create: `scripts/v2_g1_v0_semantic_regression.py` — exhaustive V0 semantic-equivalence check from preflight base to G1 implementation.
- Create: `tests/test_v2_domain.py`
- Create: `tests/test_v2_planner.py`
- Create: `tests/test_v2_gladiator.py`
- Create: `tests/test_v2_canonical.py`
- Create: `tests/test_v2_census.py`
- Create: `tests/test_v2_g1_cli.py`
- Create: `tests/test_v2_g1_semantic_regression.py`
- Create during official G1 execution: `experiments/v2/g1-census/CENSUS.json`
- Create during official G1 execution: `experiments/v2/g1-census/FAMILIES.jsonl`
- Create during official G1 execution: `experiments/v2/g1-census/SHA256.txt`
- Create after official G1 execution: `experiments/v2/G1_RECORD.md` — outside the three-file census directory so CLI custody remains exact.

---

### Task 1: Preserve V0 `Menu`; add ordered six-query arena

**Files:**
- Modify: `src/arc_mkii/domain.py`
- Create: `tests/test_v2_domain.py`

**Interfaces:**
- Consumes: existing `normalize_partition(mask)`.
- Produces: `QuerySet` protocol and `SixQueryArena(queries)`.

- [ ] **Step 1: Write failing tests**

```python
from arc_mkii.domain import Menu, SixQueryArena


def test_six_query_arena_preserves_public_slot_order():
    arena = SixQueryArena((16, 46, 89, 4, 45, 1))
    assert arena.queries == (16, 46, 89, 4, 45, 1)


def test_six_query_arena_requires_six_distinct_queries():
    try:
        SixQueryArena((1, 2, 3, 4, 5, 5))
    except ValueError as exc:
        assert "six distinct" in str(exc)
    else:
        raise AssertionError("duplicate V2 query was accepted")


def test_legacy_v0_menu_still_sorts_exactly_four_queries():
    assert Menu((85, 15, 51, 23)).queries == (15, 23, 51, 85)
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_v2_domain.py -q
```

Expected: import failure because `SixQueryArena` does not yet exist.

- [ ] **Step 3: Implement the separate arena type without changing `Menu`**

Add to `src/arc_mkii/domain.py`:

```python
from typing import Protocol, TypeAlias


class QuerySet(Protocol):
    queries: tuple[int, ...]


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
```

Do not sort `SixQueryArena.queries`. Do not edit `Menu.__post_init__`.

- [ ] **Step 4: Run GREEN plus legacy domain regression**

```bash
python -m pytest tests/test_v2_domain.py tests/test_domain.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/domain.py tests/test_v2_domain.py
git commit -m "feat: add ordered V2 six-query arena"
```

---

### Task 2: Generalize only host/planner query-count plumbing

**Files:**
- Modify: `src/arc_mkii/host.py`
- Modify: `src/arc_mkii/planner.py`
- Create: `tests/test_v2_planner.py`

**Interfaces:**
- Consumes: `QuerySet`, `candidate_child`.
- Produces: `initial_state(menu: QuerySet, ...)`; `planner_state_reference(menu, candidate_mask, remaining_query_ids, budget, resources=None)`.
- Existing V0 `planner_reference` and `planner_success_count` remain public and behavior-compatible.

- [ ] **Step 1: Write failing six-query tests plus V0 controls**

```python
from arc_mkii.domain import FULL_MASK, Menu, SixQueryArena, candidate_child
from arc_mkii.host import initial_state
from arc_mkii.planner import planner_state_reference, planner_success_count

WITNESS = SixQueryArena((16, 46, 89, 4, 45, 1))


def test_v2_host_exposes_all_six_public_query_ids():
    state = initial_state(WITNESS, fault=0, budget=3)
    assert state.remaining_query_ids == (0, 1, 2, 3, 4, 5)


def test_state_planner_certifies_witness_bad_root_value_six():
    q_f = 1
    remaining = (0, 2, 3, 4, 5)
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


def test_v0_planner_reference_remains_eight_of_eight():
    assert planner_success_count(Menu((15, 23, 51, 85)), budget=3) == 8
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_v2_planner.py -q
```

Expected: the host still exposes only four IDs and `planner_state_reference` is absent.

- [ ] **Step 3: Generalize host annotations/count only**

In `host.py`, use `QuerySet` for `SelectorView.menu`, `HostState.menu`, and `initial_state(menu, ...)`. Replace only:

```python
remaining_query_ids=tuple(range(4))
```

with:

```python
remaining_query_ids=tuple(range(len(menu.queries)))
```

Do not change belief filtering, observations, execution semantics, terminal repair, or resource-accounting behavior.

- [ ] **Step 4: Add state-level exact planner**

Implement:

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
    def solve(mask: int, remaining: tuple[int, ...], remaining_budget: int) -> int:
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
            best = max(best, value)
        return best

    success_count = solve(candidate_mask, tuple(remaining_query_ids), budget)
    if resources is not None:
        resources.planner_states_expanded += states_expanded
    return PlannerResult(success_count=success_count, states_expanded=states_expanded)
```

Then make `planner_reference(menu, budget, resources=None)` call it with `FULL_MASK` and `tuple(range(len(menu.queries)))`.

- [ ] **Step 5: Verify focused tests and the full suite**

```bash
python -m pytest tests/test_v2_planner.py tests/test_host.py tests/test_planner.py -q
python -m pytest -q
```

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/host.py src/arc_mkii/planner.py tests/test_v2_planner.py
git commit -m "refactor: support declared query counts for V2"
```

---

### Task 3: Implement the frozen V2 generator and structural admission

**Files:**
- Create: `src/arc_mkii/v2_gladiator.py`
- Create: `tests/test_v2_gladiator.py`

**Interfaces:**
- Produces: `RAW_COUNTERS`, `SEED`, `CANONICAL_THRESHOLD`, `arena_from_counter(counter)`, `ArenaAnalysis`, `analyze_arena(arena)`.
- Does not import `fit`, `evaluate`, `corpus`, `scramble`, or `artifact`.

- [ ] **Step 1: Write generator-only fixture and hand-constructed admission witness**

```python
from fractions import Fraction

from arc_mkii.domain import SixQueryArena
from arc_mkii.v2_gladiator import (
    CANONICAL_THRESHOLD,
    RAW_COUNTERS,
    SEED,
    analyze_arena,
    arena_from_counter,
)

WITNESS = SixQueryArena((16, 46, 89, 4, 45, 1))


def test_v2_raw_universe_constants_are_exactly_frozen():
    assert RAW_COUNTERS == 1_048_576
    assert CANONICAL_THRESHOLD == 320
    assert SEED == b"arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001"


def test_counter_zero_derivation_checks_generator_only():
    arena = arena_from_counter(0)
    assert arena is not None
    assert arena.queries == (20, 8, 17, 13, 117, 61)


def test_hand_witness_has_same_six_to_eight_route_preservation_conflict():
    analysis = analyze_arena(WITNESS)
    assert analysis.root_matched_tie
    assert analysis.tied_queries == (1, 2, 4)
    assert analysis.frozen_query == 1
    assert dict(analysis.continuation_values) == {1: 6, 2: 8, 4: 8}
    assert analysis.optimal_tied_queries == (2, 4)
    assert dict(analysis.feature_pairs)[1] == (Fraction(1, 4), Fraction(1, 4))
    assert dict(analysis.feature_pairs)[2] == (Fraction(1, 2), Fraction(1, 2))
    assert analysis.planner_gap
    assert analysis.feature_representable
    assert analysis.admitted
```

The counter-zero test must not call `analyze_arena`; it verifies only the prospectively frozen SHA-256 generator.

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_v2_gladiator.py -q
```

- [ ] **Step 3: Implement exact raw generation**

```python
RAW_COUNTERS = 1 << 20
CANONICAL_THRESHOLD = 320
SEED = b"arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001"


def _partition_from(counter: int, slot: int) -> int:
    if not 0 <= counter < RAW_COUNTERS:
        raise ValueError("counter outside frozen V2 raw universe")
    if not 0 <= slot < 6:
        raise ValueError("slot must be in 0..5")
    payload = SEED + counter.to_bytes(8, "big") + slot.to_bytes(1, "big")
    digest = hashlib.sha256(payload).digest()
    return 1 + (int.from_bytes(digest[:8], "big") % 127)


def arena_from_counter(counter: int) -> SixQueryArena | None:
    queries = tuple(_partition_from(counter, slot) for slot in range(6))
    if len(set(queries)) != 6:
        return None
    return SixQueryArena(queries)
```

- [ ] **Step 4: Implement structural analysis with frozen V0 features/THETA0**

Define:

```python
@dataclass(frozen=True)
class ArenaAnalysis:
    root_matched_tie: bool
    tied_queries: tuple[int, ...]
    frozen_query: int | None
    continuation_values: tuple[tuple[int, int], ...]
    planner_gap: bool
    optimal_tied_queries: tuple[int, ...]
    feature_pairs: tuple[tuple[int, tuple[Fraction, Fraction]], ...]
    feature_representable: bool

    @property
    def admitted(self) -> bool:
        return self.root_matched_tie and self.planner_gap and self.feature_representable
```

Use the exact root view:

```python
SelectorView(
    menu=arena,
    candidate_mask=FULL_MASK,
    remaining_query_ids=(0, 1, 2, 3, 4, 5),
    remaining_budget=3,
    observations=(),
)
```

Admission algorithm:

```text
1. Compute b(q)=min(|S0|,|S1|)/8 for all six roots.
2. Require max b(q)=1/2 and at least two maximizers T.
3. Compute q_F with choose_query(THETA0, root_view); require q_F in T.
4. For each q in T, remove q and sum planner_state_reference(..., budget=2) over its two root children.
5. Require max(V2)-V2(q_F) >= 2.
6. Let T* be all tied roots attaining max(V2).
7. For q in T, compute frozen feature indices 6 and 7 as (weighted_best_next_split, worst_child_best_next_split).
8. Require some q* in T* with larger worst-child score than q_F, or equal worst-child and larger weighted score.
```

Rejected arenas still return stage fields needed for exact census stage counts. No fitted theta is imported or computed.

- [ ] **Step 5: Verify witness and frozen selector/feature regressions**

```bash
python -m pytest tests/test_v2_gladiator.py tests/test_selector.py tests/test_features.py -q
```

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/v2_gladiator.py tests/test_v2_gladiator.py
git commit -m "feat: add frozen V2 Gladiator admission"
```

---

### Task 4: Implement exact six-query structural-family identity

**Files:**
- Create: `src/arc_mkii/v2_canonical.py`
- Create: `tests/test_v2_canonical.py`

**Interfaces:**
- Produces: `canonical_bytes(arena) -> bytes`; `family_id(arena) -> str`.
- Scientific equivalence: fault permutations, six query-name permutations, and independent answer complements.

- [ ] **Step 1: Write exact fixture, invariance tests, and brute-force oracle test**

```python
from arc_mkii.domain import SixQueryArena
from arc_mkii.v2_canonical import canonical_bytes, family_id

WITNESS = SixQueryArena((16, 46, 89, 4, 45, 1))


def test_witness_has_exact_canonical_bytes_and_family_id():
    assert canonical_bytes(WITNESS) == bytes([0, 1, 2, 4, 9, 11, 26, 43])
    assert family_id(WITNESS) == "9444534fc7a1171614925bb2fee464aaf28835bb24dbd1e61454de6891c1b942"


def test_query_permutation_does_not_change_family():
    permuted = SixQueryArena(tuple(WITNESS.queries[i] for i in (5, 2, 0, 4, 1, 3)))
    assert family_id(permuted) == family_id(WITNESS)
```

Also implement in the test file a deliberately slow explicit oracle that enumerates all `6!` column permutations and all `2^6` answer-complement vectors, sorts the eight row signatures, and returns the lexicographic minimum. Assert optimized `canonical_bytes` equals the oracle on these synthetic arenas:

```python
SixQueryArena((16, 46, 89, 4, 45, 1))
SixQueryArena((15, 23, 51, 85, 1, 3))
SixQueryArena((7, 11, 13, 19, 37, 73))
```

These are synthetic fixtures, not sampled V2 confirmatory counters.

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_v2_canonical.py -q
```

- [ ] **Step 3: Implement the exact optimized quotient**

Represent each hidden fault as one six-bit row. Row/fault permutations disappear by sorting rows. Independent answer complements are a common XOR translation of every row by a six-bit vector. The lexicographic minimum must contain row `0`, so it is sufficient and exact to consider translations by one of the eight observed rows, rather than all 64 translations. Then enumerate all `6!` query permutations.

Use:

```python
FAMILY_PREFIX = b"arc-mkii-v2-six-query-gladiator-family\0"
_QUERY_PERMS = tuple(itertools.permutations(range(6)))


def _permute_row(row: int, perm: tuple[int, ...]) -> int:
    out = 0
    for out_col, source_col in enumerate(perm):
        out |= ((row >> source_col) & 1) << out_col
    return out


_PERM_TABLE = tuple(
    tuple(_permute_row(row, perm) for row in range(64))
    for perm in _QUERY_PERMS
)
```

For each distinct observed anchor row `a`, translate rows by `row ^ a`; for each precomputed query permutation map, sort the mapped eight rows and minimize `bytes(...)` lexicographically.

Then:

```python
def family_id(arena: SixQueryArena) -> str:
    return hashlib.sha256(FAMILY_PREFIX + canonical_bytes(arena)).hexdigest()
```

- [ ] **Step 4: Verify optimized quotient against the explicit oracle**

```bash
python -m pytest tests/test_v2_canonical.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/v2_canonical.py tests/test_v2_canonical.py
git commit -m "feat: add exact V2 six-query family quotient"
```

---

### Task 5: Implement deterministic G1 census and exact shard merge

**Files:**
- Create: `src/arc_mkii/v2_census.py`
- Create: `tests/test_v2_census.py`

**Interfaces:**
- Produces: `FamilyRecord`, `CensusPart`, `CensusResult`, `scan_records(records)`, `scan_range(start, stop)`, `merge_parts(parts)`, `run_census(workers=4)`.
- `run_census` always covers exactly `[0, RAW_COUNTERS)`; `workers` changes execution only, not scientific semantics.

- [ ] **Step 1: Write synthetic census-stage and merge tests**

Do not use a confirmatory-seed prefix for expected counts. Use hand-built synthetic `(counter, arena)` records.

```python
from arc_mkii.domain import SixQueryArena
from arc_mkii.v2_census import merge_parts, scan_records

ADMITTED = SixQueryArena((16, 46, 89, 4, 45, 1))
ADMITTED_ALIAS = SixQueryArena((16, 46, 89, 4, 1, 45))
REJECTED = SixQueryArena((1, 2, 4, 8, 16, 32))


def test_first_admitted_counter_is_retained_for_family():
    part = scan_records([(9, ADMITTED), (12, ADMITTED_ALIAS)])
    assert part.admitted_presentations == 2
    assert len(part.first_families) == 1
    record = next(iter(part.first_families.values()))
    assert record.first_counter == 9
    assert record.queries == ADMITTED.queries


def test_shard_merge_is_order_independent_and_keeps_global_first_counter():
    left = scan_records([(12, ADMITTED_ALIAS)])
    right = scan_records([(9, ADMITTED)])
    merged_a = merge_parts([left, right])
    merged_b = merge_parts([right, left])
    assert merged_a == merged_b
    record = next(iter(merged_a.first_families.values()))
    assert record.first_counter == 9
```

`ADMITTED_ALIAS` is a query permutation of the same canonical family that still satisfies the operational admission rule; this is why it is safe for the first-admitted-family fixture.

Add a rejected synthetic arena test verifying it increments grammar-valid and whichever structural stages it reaches but not `admitted_presentations`.

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_v2_census.py -q
```

- [ ] **Step 3: Implement stage accounting and first-family retention**

Use dataclasses:

```python
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
```

For each record/counter:

```text
raw_counters += 1
arena is None -> stop this record
grammar_valid += 1
analyze_arena(arena)
if root_matched_tie: root_matched_tie += 1
if planner_gap: planner_gap += 1
if feature_representable: feature_representable += 1
if admitted:
    admitted_presentations += 1
    canonicalize only now
    keep the smallest counter for each family ID
```

Canonicalization must never run on a structurally rejected arena.

- [ ] **Step 4: Implement exact shard merge**

`merge_parts(parts)` must:

1. sum all scalar stage counts;
2. union family IDs;
3. for a duplicate family ID, keep the `FamilyRecord` with smaller `first_counter`;
4. return the same value independent of completion/merge order.

- [ ] **Step 5: Implement full-range runner without changing the scientific interval**

Use four contiguous ranges by default:

```python
[(0, 262_144), (262_144, 524_288), (524_288, 786_432), (786_432, 1_048_576)]
```

`scan_range(start, stop)` calls `arena_from_counter(counter)` and performs the same logic as `scan_records`. `run_census(workers=4)` may use `ProcessPoolExecutor(max_workers=4)` but must merge returned parts with `merge_parts` and assert final `raw_counters == RAW_COUNTERS`.

Add a unit test that manually partitions the same synthetic record sequence into several `CensusPart`s and proves the merged result exactly equals a single `scan_records` pass.

- [ ] **Step 6: Run GREEN**

```bash
python -m pytest tests/test_v2_census.py -q
```

- [ ] **Step 7: Commit**

```bash
git add src/arc_mkii/v2_census.py tests/test_v2_census.py
git commit -m "feat: add deterministic V2 G1 census engine"
```

---

### Task 6: Add a census-only CLI, custody outputs, and G1 isolation tests

**Files:**
- Create: `src/arc_mkii/v2_g1_cli.py`
- Create: `tests/test_v2_g1_cli.py`

**Interfaces:**
- Command: `python -m arc_mkii.v2_g1_cli census --out <dir>`.
- Output files: exactly `CENSUS.json`, `FAMILIES.jsonl`, `SHA256.txt`.
- No fit/evaluate/train/scramble command exists.

- [ ] **Step 1: Write failing parser/import-isolation/output tests**

```python
import subprocess
import sys

from arc_mkii import v2_g1_cli


def test_g1_parser_exposes_only_census():
    parser = v2_g1_cli.build_parser()
    help_text = parser.format_help()
    assert "census" in help_text
    assert "fit" not in help_text
    assert "evaluate" not in help_text
    assert "train" not in help_text


def test_g1_cli_import_graph_excludes_learning_and_evaluation_modules():
    code = r'''
import sys
import arc_mkii.v2_g1_cli
forbidden = {
    "arc_mkii.fit",
    "arc_mkii.evaluate",
    "arc_mkii.corpus",
    "arc_mkii.scramble",
    "arc_mkii.artifact",
}
assert forbidden.isdisjoint(sys.modules), forbidden.intersection(sys.modules)
'''
    subprocess.run([sys.executable, "-c", code], check=True)
```

Use a subprocess so the full pytest collection cannot contaminate `sys.modules` with unrelated legacy modules.

For output tests, patch only `v2_g1_cli.run_census` to return a tiny synthetic `CensusResult`; this test is specifically for serialization/CLI behavior, not census science. Assert exact three-file output, deterministic byte identity on a second invocation, and fail-closed behavior if any retained file is altered.

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_v2_g1_cli.py -q
```

- [ ] **Step 3: Implement minimal census-only CLI**

`v2_g1_cli.py` imports only standard library plus `v2_census`/`v2_gladiator`. It must not import V0 `cli.py` because that transitively exposes fitting/evaluation machinery.

`CENSUS.json` schema:

```json
{
  "schema": "arc-reactor-mkii-v2-g1-census/v0",
  "preflight_base": "078b3cfc948262bb71604a631e17972f8ad11a1f",
  "implementation_commit": "<git rev-parse HEAD>",
  "seed": "arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001",
  "raw_counter_count": 1048576,
  "canonical_threshold": 320,
  "status": "G1_PASS or ARENA_UNIVERSE_INSUFFICIENT",
  "counts": {
    "raw_counters": 1048576,
    "grammar_valid": 0,
    "root_matched_tie": 0,
    "planner_gap": 0,
    "feature_representable": 0,
    "admitted_presentations": 0,
    "admitted_canonical": 0
  }
}
```

`FAMILIES.jsonl` contains every first-admitted canonical family, sorted by `(first_counter, family_id)`, one record per line:

```json
{"canonical_bytes_hex":"...","family_id":"...","first_counter":123,"queries":[1,2,3,4,5,6]}
```

`SHA256.txt` uses standard format:

```text
<sha256>  CENSUS.json
<sha256>  FAMILIES.jsonl
```

Do not hash `SHA256.txt` into itself.

If the output directory already exists, accept it only if its exact file set and both recorded hashes validate; then return without rerunning the census. Otherwise fail closed.

- [ ] **Step 4: Verify CLI isolation and deterministic custody**

```bash
python -m pytest tests/test_v2_g1_cli.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/v2_g1_cli.py tests/test_v2_g1_cli.py
git commit -m "feat: add isolated V2 G1 census command"
```

---

### Task 7: Add exhaustive V0 semantic regression for the G1 implementation

**Files:**
- Create: `scripts/v2_g1_v0_semantic_regression.py`
- Create: `tests/test_v2_g1_semantic_regression.py`

**Interfaces:**
- Compares frozen preflight executable base `078b3cfc948262bb71604a631e17972f8ad11a1f` against the current G1 implementation over the complete frozen V0 scientific observable vector.
- Expected unchanged semantic-vector hash remains `4aa007b39b060a954695b0d484a28723f9eb0c1949fc98e10c9c6c7ded4c20f0`.

- [ ] **Step 1: Write a failing test for the regression script constants**

```python
from pathlib import Path


def test_v2_g1_semantic_regression_is_bound_to_frozen_preflight_base():
    text = Path("scripts/v2_g1_v0_semantic_regression.py").read_text(encoding="utf-8")
    assert "078b3cfc948262bb71604a631e17972f8ad11a1f" in text
    assert "4aa007b39b060a954695b0d484a28723f9eb0c1949fc98e10c9c6c7ded4c20f0" in text
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_v2_g1_semantic_regression.py -q
```

- [ ] **Step 3: Implement the G1 regression driver from the existing G0.5 collector**

Reuse the existing `scripts/g05_semantic_equivalence.py` semantic object **including the exact schema string used there**, so the unchanged semantic vector retains the G0.5 hash. The object covers frozen TRAIN/EVAL membership, 189,177 training rows, exact LEARN/SCRAMBLED/FROZEN theta, full scramble assignment digest, all query scores/choices/transitions/repairs/successes over all 320 menus × both budgets × eight faults, EVAL success counts, and ignition decision.

Use:

```python
BASE_COMMIT = "078b3cfc948262bb71604a631e17972f8ad11a1f"
EXPECTED_SEMANTIC_VECTOR_SHA256 = "4aa007b39b060a954695b0d484a28723f9eb0c1949fc98e10c9c6c7ded4c20f0"
```

Do **not** require `src/arc_mkii/` to be byte-identical to the preflight base; G1 intentionally adds generic query-count plumbing and new V2 modules. Materialize `BASE_COMMIT` into a temporary directory, collect the same semantic record under base and current code, compare the records exactly, and additionally require the current semantic-vector hash equals the expected G0.5 hash.

The script prints on success:

```text
V2 G1 V0 SEMANTIC REGRESSION: PASS
base=078b3cfc948262bb71604a631e17972f8ad11a1f
frozen_menus=320 (256 TRAIN + 64 EVAL)
training_rows=189177
semantic_vector_sha256=4aa007b39b060a954695b0d484a28723f9eb0c1949fc98e10c9c6c7ded4c20f0
```

- [ ] **Step 4: Run the complete semantic regression**

```bash
python scripts/v2_g1_v0_semantic_regression.py
```

Expected: PASS with the exact hash above.

- [ ] **Step 5: Run the complete repository suite**

```bash
python -m pytest -q
```

- [ ] **Step 6: Commit**

```bash
git add scripts/v2_g1_v0_semantic_regression.py tests/test_v2_g1_semantic_regression.py
git commit -m "test: certify V0 semantics across V2 G1 plumbing"
```

---

### Task 8: Freeze G1 implementation, execute the official census once, fossilize, and HARD STOP

**Files:**
- Create during execution: `experiments/v2/g1-census/CENSUS.json`
- Create during execution: `experiments/v2/g1-census/FAMILIES.jsonl`
- Create during execution: `experiments/v2/g1-census/SHA256.txt`
- Create after verification: `experiments/v2/G1_RECORD.md`

**Interfaces:**
- Consumes: frozen V2 design and all prior G1 implementation tasks.
- Produces: one G1 construction-gate result only.

- [ ] **Step 1: Pre-census implementation-freeze verification**

Run:

```bash
python --version
python -m pytest -q
python scripts/v2_g1_v0_semantic_regression.py
git status --short
git rev-parse HEAD
```

Requirements:

```text
Python 3.13.x
all tests PASS
V2 G1 V0 SEMANTIC REGRESSION: PASS
working tree clean
```

Record the resulting HEAD as:

```text
G1_IMPLEMENTATION_FREEZE_ID_V2=<sha>
```

No implementation edit is legal after this point without creating a new implementation freeze and rerunning all pre-census verification **before** any result-bearing census.

- [ ] **Step 2: Execute the official full frozen universe exactly once to a fresh output directory**

```bash
PYTHONPATH=src python -m arc_mkii.v2_g1_cli census --out experiments/v2/g1-census
```

Do not run a prefix census first. Do not inspect partial in-memory counts while execution is running. Do not fit or evaluate anything.

- [ ] **Step 3: Verify retained custody without rerunning the census**

Check exact census-directory file set and SHA-256 values from `SHA256.txt`, then parse `CENSUS.json` and require:

```python
assert census["counts"]["raw_counters"] == 1_048_576
assert census["counts"]["admitted_canonical"] == sum(
    1 for _ in open("experiments/v2/g1-census/FAMILIES.jsonl", encoding="utf-8")
)
assert census["status"] in {"G1_PASS", "ARENA_UNIVERSE_INSUFFICIENT"}
```

- [ ] **Step 4: Write the bounded G1 record outside the census directory**

`experiments/v2/G1_RECORD.md` must include:

```text
preflight base: 078b3cfc948262bb71604a631e17972f8ad11a1f
G1_IMPLEMENTATION_FREEZE_ID_V2: <sha>
seed: arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001
raw counters: 1,048,576
all seven census counts
canonical threshold: 320
status: G1_PASS or ARENA_UNIVERSE_INSUFFICIENT
```

It must also state exactly one corresponding authorization boundary.

If `<320`:

```text
ARENA_UNIVERSE_INSUFFICIENT
NO G2
NO TRAINING
NO V2 SCIENTIFIC RESULT
```

If `>=320`:

```text
G1 CONSTRUCTION GATE PASS
G2 PROTOCOL-FREEZE DESIGN/IMPLEMENTATION AUTHORIZED ONLY
NO TRAINING
NO EVALUATION
NO V2 SCIENTIFIC RESULT
```

- [ ] **Step 5: Commit the G1 fossil**

If insufficient:

```bash
git add experiments/v2/g1-census experiments/v2/G1_RECORD.md
git commit -m "record: close V2 G1 insufficient arena census"
```

If pass:

```bash
git add experiments/v2/g1-census experiments/v2/G1_RECORD.md
git commit -m "record: freeze V2 G1 six-query census"
```

Record final HEAD as `V2_G1_RECORD_ID`.

- [ ] **Step 6: Final verification and HARD STOP**

Run:

```bash
python -m pytest -q
python scripts/v2_g1_v0_semantic_regression.py
git status --short
git rev-parse HEAD
```

Then stop regardless of G1 outcome.

Do **not** in this plan/session:

```text
compute split ranks for selecting TRAIN/EVAL
freeze 256 TRAIN / 64 EVAL
build V2 training rows
compute a V2 scramble descriptor
fit LEARN
fit SCRAMBLED
serialize V2 learner artifacts
evaluate FROZEN/LEARN/SCRAMBLED
compute V2 ignition
change seed / threshold / raw interval / admission grammar
```

G2 requires a separate approved plan even if G1 passes.

---

## Self-Review

### 1. Spec coverage

- Direct executable ancestry from frozen preflight base, without plan-branch ancestry: Architecture and Global Constraints.
- Six distinct ordered queries: Task 1.
- Generic query-count host/planner plumbing while preserving V0: Tasks 2 and 7.
- Frozen fresh seed and exact `2^20` counter grammar: Task 3.
- No confirmatory prefix inspection before official census: Global Constraints and Task 8.
- Matched 4/4 tie, FROZEN root, exact two-query continuation, gap `>=2`, frozen-feature representability: Task 3.
- Exact family quotient under fault/query/complement invariances: Task 4.
- First-admitted-family rule and all seven required G1 counts: Task 5.
- No fitted selector during G1 and no learning/evaluation command surface: Tasks 3 and 6.
- Hard threshold `320`, fail/pass interpretation, and no post-census redesign: Tasks 5, 6, and 8.
- G1 retains all first-admitted family records but does not compute/select the G2 TRAIN/EVAL split: Tasks 5, 6, and 8.
- Full preflight semantic preservation of V0 observable vector: Task 7.
- Historical resource boundary remains intact: Global Constraints and Task 8.
- Census directory remains an exact three-file custody object; narrative G1 fossil is separate: Tasks 6 and 8.

No G2, training, or evaluation requirement is implemented by this plan.

### 2. Placeholder scan

No `TODO`, `TBD`, “implement later”, unspecified validation, or “similar to” instructions remain. All execution gates, schemas, file names, constants, commands, and claim boundaries are explicit.

### 3. Type consistency and fixture audit

- `QuerySet.queries` is `tuple[int, ...]`.
- `SixQueryArena.queries` is a six-int tuple and preserves operational order.
- `planner_state_reference` consumes `QuerySet` and explicit remaining IDs.
- `ArenaAnalysis.continuation_values` and `feature_pairs` are immutable tuples suitable for deterministic testing.
- `FamilyRecord` carries only structural/custody data; no learner outcome enters it.
- `CensusPart.first_families` maps family ID to globally first admitted record after merge.
- `CENSUS.json` `admitted_canonical` equals the number of retained `FAMILIES.jsonl` records.
- Generator fixture is frozen and checked without running admission on counter 0.
- Hand witness `(16,46,89,4,45,1)` has `q_F=1`, continuation `6`, alternatives `8`, and feature pairs `(1/4,1/4)` versus `(1/2,1/2)`.
- Census alias fixture `(16,46,89,4,1,45)` remains admitted and belongs to the same canonical family as the witness.
- Canonical fixture bytes are `00 01 02 04 09 0b 1a 2b`; family ID is `9444534fc7a1171614925bb2fee464aaf28835bb24dbd1e61454de6891c1b942`.

The plan is internally consistent and stops at G1.
