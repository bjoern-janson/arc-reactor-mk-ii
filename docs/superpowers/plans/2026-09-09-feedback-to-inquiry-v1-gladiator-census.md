# ARC-MKII-V1 Gladiator Census Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement only the G1 structural-census machinery for ARC-MKII-V1 GLADIATOR, exhaust the prospectively fixed `2^20` arena stream, and stop before any V1 protocol freeze, fitting, or evaluation.

**Architecture:** Preserve the V0 learner and its four-query `Menu` behavior exactly. Introduce a separate ordered five-query `GladiatorArena` because public query order is operational in V1, generalize only host/planner query-count plumbing, then implement deterministic arena generation, matched-tie admission, five-query structural-family identity, and a streaming census retaining only the 320 lowest prospectively declared split ranks. The G1 executable exposes no fit or evaluation command.

**Tech Stack:** Python 3.13.5; Python standard library only at runtime; `pytest`; exact `fractions.Fraction`; SHA-256; JSON/JSONL.

**Spec:** `docs/superpowers/specs/2026-09-09-feedback-to-inquiry-v1-gladiator-design.md`

## Global Constraints

- Base scientific implementation is frozen at `c9897ae02829aeed31cccdaef662de4c715b312e`.
- V0's eight features, `THETA0`, exact rational arithmetic, ridge learner, `lambda=1/100`, LEARN/SCRAMBLED/FROZEN meanings, repair rule, budgets `{2,3}`, transplant rule, resource vector, and ignition rule are not redesigned here.
- This plan implements **G1 only**. No V1 training, V1 SCRAMBLED fitting, V1 evaluation, or V1 ignition decision is implemented or invoked.
- The hidden fault universe remains exactly `0..7`.
- A V1 arena has exactly five distinct nonconstant normalized binary queries.
- Public query order is operational in V1. `GladiatorArena` preserves tuple order after per-slot normalization.
- Legacy V0 `Menu` remains exactly four queries and continues sorting normalized masks exactly as before.
- The raw V1 universe is exactly `1_048_576` counters with seed `arc-reactor-mk-ii/v1-gladiator/menu-seed/2026-09-09`.
- Admission may inspect only query truth tables, the frozen feature map, `THETA0`/FROZEN choice, and exact planner continuation value.
- The canonical-family threshold is exactly `320` and is not revised after census.
- `<320` canonical families means `ARENA_UNIVERSE_INSUFFICIENT -> STOP`.
- `>=320` means record `PASS`, retain the deterministic top 320 structural records, and STOP. G2 requires a separate plan.

---

## File Map

- Modify: `src/arc_mkii/domain.py` — add `QuerySet` and ordered `GladiatorArena`; preserve V0 `Menu`.
- Modify: `src/arc_mkii/host.py` — derive query IDs from `len(menu.queries)`.
- Modify: `src/arc_mkii/planner.py` — add exact state-level planner entry point and declared query count.
- Create: `src/arc_mkii/gladiator.py` — raw generator and structural admission analysis.
- Create: `src/arc_mkii/gladiator_canonical.py` — five-query structural-family identity.
- Create: `src/arc_mkii/gladiator_census.py` — streaming census and bounded top-320 retention.
- Create: `src/arc_mkii/gladiator_cli.py` — census-only CLI and custody serialization.
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
- Produces: `QuerySet` and `GladiatorArena(queries)`.

- [ ] **Step 1: Write failing tests**

```python
from arc_mkii.domain import GladiatorArena, Menu


def test_gladiator_arena_preserves_public_slot_order():
    arena = GladiatorArena((89, 16, 45, 4, 46))
    assert arena.queries == (89, 16, 45, 4, 46)


def test_gladiator_arena_requires_five_distinct_queries():
    try:
        GladiatorArena((1, 2, 3, 4, 4))
    except ValueError as exc:
        assert "five distinct" in str(exc)
    else:
        raise AssertionError("duplicate Gladiator query was accepted")


def test_legacy_v0_menu_still_sorts_four_queries():
    assert Menu((85, 15, 51, 23)).queries == (15, 23, 51, 85)
```

- [ ] **Step 2: Verify RED**

```bash
python -m pytest tests/test_gladiator_domain.py -q
```

Expected: import failure because `GladiatorArena` does not exist.

- [ ] **Step 3: Implement the separate V1 arena type**

Add to `src/arc_mkii/domain.py` without changing `Menu.__post_init__`:

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
        object.__setattr__(self, "queries", normalized)
```

Do **not** sort `GladiatorArena.queries`.

- [ ] **Step 4: Verify GREEN plus V0 domain regression**

```bash
python -m pytest tests/test_gladiator_domain.py tests/test_domain.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/domain.py tests/test_gladiator_domain.py
git commit -m "feat: add ordered V1 Gladiator arena domain"
```

---

### Task 2: Generalize host/planner query-count plumbing only

**Files:**
- Modify: `src/arc_mkii/host.py`
- Modify: `src/arc_mkii/planner.py`
- Create: `tests/test_gladiator_planner.py`

**Interfaces:**
- Consumes: `QuerySet`, `candidate_child`.
- Produces: `initial_state(menu: QuerySet, ...)`; `planner_state_reference(menu, candidate_mask, remaining_query_ids, budget, resources=None)`; existing planner APIs remain intact.

- [ ] **Step 1: Write failing five-query tests and a V0 control**

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

- [ ] **Step 2: Verify RED**

```bash
python -m pytest tests/test_gladiator_planner.py -q
```

- [ ] **Step 3: Generalize host count without changing semantics**

In `host.py`, change `Menu` annotations to `QuerySet` for selector/host state and replace only:

```python
remaining_query_ids=tuple(range(4))
```

with:

```python
remaining_query_ids=tuple(range(len(menu.queries)))
```

Belief filtering, observations, terminal repair, and resource counters remain byte-for-behavior identical.

- [ ] **Step 4: Expose state-level exact planner**

Implement in `planner.py`:

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
            if value > best:
                best = value
        return best

    success_count = solve(candidate_mask, tuple(remaining_query_ids), budget)
    if resources is not None:
        resources.planner_states_expanded += states_expanded
    return PlannerResult(success_count=success_count, states_expanded=states_expanded)
```

Then make `planner_reference` call it with `FULL_MASK` and `tuple(range(len(menu.queries)))`.

- [ ] **Step 5: Verify focused and full V0 suites**

```bash
python -m pytest tests/test_gladiator_planner.py tests/test_host.py tests/test_planner.py -q
python -m pytest -q
```

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/host.py src/arc_mkii/planner.py tests/test_gladiator_planner.py
git commit -m "refactor: support declared query counts without changing V0"
```

---

### Task 3: Implement prospective raw generation and Gladiator admission

**Files:**
- Create: `src/arc_mkii/gladiator.py`
- Create: `tests/test_gladiator.py`

**Interfaces:**
- Produces: `RAW_COUNTERS`, `SEED`, `CANONICAL_THRESHOLD`, `arena_from_counter(counter)`, `ArenaAnalysis`, `analyze_arena(arena)`.

- [ ] **Step 1: Write deterministic generator and exact witness tests**

```python
from arc_mkii.domain import GladiatorArena
from arc_mkii.gladiator import CANONICAL_THRESHOLD, RAW_COUNTERS, arena_from_counter, analyze_arena

WITNESS = GladiatorArena((16, 46, 89, 4, 45))


def test_raw_universe_constants_are_frozen():
    assert RAW_COUNTERS == 1_048_576
    assert CANONICAL_THRESHOLD == 320


def test_counter_zero_has_exact_public_query_slots():
    arena = arena_from_counter(0)
    assert arena is not None
    assert arena.queries == (67, 75, 92, 96, 91)


def test_witness_has_tied_greedy_choice_but_better_continuations():
    a = analyze_arena(WITNESS)
    assert a.root_matched_tie
    assert a.tied_queries == (1, 2, 4)
    assert a.frozen_query == 1
    assert dict(a.continuation_values) == {1: 6, 2: 8, 4: 8}
    assert a.planner_gap
    assert a.optimal_tied_queries == (2, 4)
    assert a.feature_representable
    assert a.admitted
```

- [ ] **Step 2: Verify RED**

```bash
python -m pytest tests/test_gladiator.py -q
```

- [ ] **Step 3: Implement raw generation exactly**

```python
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

Use:

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

Root view is:

```python
SelectorView(
    menu=arena,
    candidate_mask=FULL_MASK,
    remaining_query_ids=(0, 1, 2, 3, 4),
    remaining_budget=3,
    observations=(),
)
```

For each query:

```python
b(q) = Fraction(min(child0.bit_count(), child1.bit_count()), 8)
```

Admission algorithm:

1. Require maximum root balance exactly `1/2` and at least two maximizers `T`.
2. Compute the actual frozen root choice with `choose_query(THETA0, root_view)`; it must be in `T`.
3. For each `q in T`, remove `q`, split `FULL_MASK` on its two answers, and sum `planner_state_reference(..., budget=2).success_count` over the two children.
4. Require `max(V2)-V2(q_F) >= 2`.
5. Let `T*` be tied roots attaining max `V2`.
6. Read existing feature indices 6 (`weighted_best_next_split`) and 7 (`worst_child_best_next_split`) at the root. Require some `q* in T*` with greater worst-child score than `q_F`, or equal worst-child and greater weighted score.

Return stage fields even for rejected arenas. Do not import or compute any fitted theta.

- [ ] **Step 5: Verify features/selector are unchanged**

```bash
python -m pytest tests/test_gladiator.py tests/test_features.py tests/test_selector.py -q
```

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/gladiator.py tests/test_gladiator.py
git commit -m "feat: add V1 Gladiator arena admission rule"
```

---

### Task 4: Add five-query structural-family identity

**Files:**
- Create: `src/arc_mkii/gladiator_canonical.py`
- Create: `tests/test_gladiator_canonical.py`

**Interfaces:**
- Produces: `canonical_bytes_v1(arena) -> bytes`; `family_id(arena) -> str`.

- [ ] **Step 1: Write representation-invariance tests**

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
    p = (7, 6, 5, 4, 3, 2, 1, 0)
    renamed = GladiatorArena(tuple(permute_faults(q, p) for q in reversed(base.queries)))
    assert canonical_bytes_v1(base) == canonical_bytes_v1(renamed)
    assert family_id(base) == family_id(renamed)


def test_v1_canonical_bytes_are_exactly_eight_bytes():
    assert len(canonical_bytes_v1(GladiatorArena((16, 46, 89, 4, 45)))) == 8


def test_different_structural_families_can_have_different_ids():
    assert family_id(GladiatorArena((16, 46, 89, 4, 45))) != family_id(
        GladiatorArena((67, 75, 92, 96, 91))
    )
```

- [ ] **Step 2: Verify RED**

```bash
python -m pytest tests/test_gladiator_canonical.py -q
```

- [ ] **Step 3: Implement five-column quotient exactly**

```python
def canonical_bytes_v1(arena: GladiatorArena) -> bytes:
    best: bytes | None = None
    for perm in itertools.permutations(range(5)):
        for complement_bits in range(32):
            rows = []
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
    return hashlib.sha256(
        b"arc-mkii-v1-gladiator-task\0" + canonical_bytes_v1(arena)
    ).hexdigest()
```

Operational arena order is preserved in `GladiatorArena`; only this freshness-family identifier quotients query order.

- [ ] **Step 4: Verify V1 and V0 canonical tests**

```bash
python -m pytest tests/test_gladiator_canonical.py tests/test_canonical.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/gladiator_canonical.py tests/test_gladiator_canonical.py
git commit -m "feat: add V1 Gladiator structural family identity"
```

---

### Task 5: Implement the streaming G1 census

**Files:**
- Create: `src/arc_mkii/gladiator_census.py`
- Create: `tests/test_gladiator_census.py`

**Interfaces:**
- Produces: `split_rank(family_id)`, `CensusCounts`, `SelectedArena`, `CensusResult`, `run_structural_census(raw_counters=RAW_COUNTERS)`.

- [ ] **Step 1: Write deterministic census tests**

```python
from arc_mkii.gladiator import CANONICAL_THRESHOLD
from arc_mkii.gladiator_census import run_structural_census, split_rank


def test_split_rank_is_exact_domain_separated_sha256():
    assert split_rank("00" * 32) == "642f088778039fc447d6915450243a1b75726aa30dd11fafd2f0ea8722e21724"


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

- [ ] **Step 2: Verify RED**

```bash
python -m pytest tests/test_gladiator_census.py -q
```

- [ ] **Step 3: Define exact census records**

```python
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
        return (
            "PASS"
            if self.counts.admitted_canonical >= CANONICAL_THRESHOLD
            else "ARENA_UNIVERSE_INSUFFICIENT"
        )
```

Exact split rank:

```python
def split_rank(canonical_family_id: str) -> str:
    if len(canonical_family_id) != 64:
        raise ValueError("family id must be 64 lowercase hex characters")
    int(canonical_family_id, 16)
    payload = b"arc-mkii-v1-gladiator-split\0" + canonical_family_id.encode("ascii")
    return hashlib.sha256(payload).hexdigest()
```

- [ ] **Step 4: Implement streaming census with bounded complete records**

Use one `seen_families: set[str]` and one sorted list containing at most 320 complete records. Loop counters in ascending order. Increment stage counters in this exact sequence:

```text
grammar_valid
-> root_matched_tie
-> planner_gap
-> feature_representable / admitted_presentations
-> canonical deduplication / admitted_canonical
```

Only after an arena is structurally admitted call `family_id(arena)`.

For each new family, compute `key=(split_rank(fid), fid)`, insert with `bisect.insort`, and if the selected list exceeds 320 remove its largest item. This exactly retains the first 320 by the spec's `(split_rank, family_id)` ordering without storing all admitted arena records.

The final `admitted_canonical` count is `len(seen_families)` even though only up to 320 complete records remain.

- [ ] **Step 5: Verify census tests**

```bash
python -m pytest tests/test_gladiator_census.py -q
```

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/gladiator_census.py tests/test_gladiator_census.py
git commit -m "feat: add bounded V1 Gladiator structural census"
```

---

### Task 6: Add census-only CLI and deterministic custody artifacts

**Files:**
- Create: `src/arc_mkii/gladiator_cli.py`
- Create: `tests/test_gladiator_cli.py`

**Interfaces:**
- Produces only `census --out DIR` and the three G1 custody files.

- [ ] **Step 1: Write CLI-separation and idempotence tests**

```python
import hashlib
import json

from arc_mkii.gladiator_cli import build_parser, write_census


def test_gladiator_cli_exposes_census_only():
    help_text = build_parser().format_help()
    assert "census" in help_text
    assert "fit" not in help_text
    assert "evaluate" not in help_text


def test_small_census_write_is_deterministic_and_self_hashed(tmp_path):
    out = tmp_path / "census"
    write_census(out, raw_counters=64)
    first = {p.name: p.read_bytes() for p in out.iterdir()}
    write_census(out, raw_counters=64)
    second = {p.name: p.read_bytes() for p in out.iterdir()}
    assert first == second
    assert set(first) == {"CENSUS.json", "TOP_320.jsonl", "SHA256.txt"}

    meta = json.loads(first["CENSUS.json"])
    assert meta["schema"] == "arc-reactor-mkii-v1-gladiator-census/v0"
    assert meta["raw_counters"] == 64

    recorded = dict(
        line.split("  ", 1)
        for line in first["SHA256.txt"].decode("ascii").splitlines()
    )
    assert recorded == {
        name: hashlib.sha256(first[name]).hexdigest()
        for name in ("CENSUS.json", "TOP_320.jsonl")
    }
```

- [ ] **Step 2: Verify RED**

```bash
python -m pytest tests/test_gladiator_cli.py -q
```

- [ ] **Step 3: Implement exact serialization**

`TOP_320.jsonl` record keys are exactly:

```text
split_rank
family_id
raw_counter
queries
frozen_query
tied_queries
continuation_values
optimal_tied_queries
```

where `continuation_values` is a list of `{"query_id": int, "value": int}` records.

`CENSUS.json` keys are exactly:

```text
schema = arc-reactor-mkii-v1-gladiator-census/v0
seed = arc-reactor-mk-ii/v1-gladiator/menu-seed/2026-09-09
raw_counters
threshold = 320
status
counts
selected_count
```

`counts` contains exactly `grammar_valid`, `root_matched_tie`, `planner_gap`, `feature_representable`, `admitted_presentations`, `admitted_canonical`.

Use sorted compact JSON with LF endings. `SHA256.txt` hashes `CENSUS.json` and `TOP_320.jsonl` in lexicographic filename order.

- [ ] **Step 4: Implement idempotent census-only execution**

`write_census(out, raw_counters=RAW_COUNTERS)` computes the census only when `out` does not exist. If `out` exists, require exactly the three declared files and verify both retained hashes; on success return without rerunning the census. Any mismatch raises `FileExistsError`.

`gladiator_cli.py` imports no fit, artifact, scramble, evaluate, or V0 CLI module. Parser exposes only:

```text
census --out DIR
```

A completed insufficient census still exits zero; the scientific gate is the frozen `status` field.

- [ ] **Step 5: Verify CLI and complete regression suite**

```bash
python -m pytest tests/test_gladiator_cli.py -q
python -m pytest -q
```

- [ ] **Step 6: Commit**

```bash
git add src/arc_mkii/gladiator_cli.py tests/test_gladiator_cli.py
git commit -m "feat: add V1 Gladiator census-only execution gate"
```

---

### Task 7: Freeze G1 implementation, execute full structural census once, then STOP

**Files created by execution:**
- `experiments/v1/census/CENSUS.json`
- `experiments/v1/census/TOP_320.jsonl`
- `experiments/v1/census/SHA256.txt`

- [ ] **Step 1: Fresh pre-census verification**

```bash
python --version
python -m pytest -q
git status --short
git rev-parse HEAD
```

Require Python `3.13.5`, zero test failures, and clean working tree. Record HEAD as `CENSUS_IMPLEMENTATION_ID_V1`.

- [ ] **Step 2: Execute the fixed million-counter structural census once**

```bash
python -m arc_mkii.gladiator_cli census --out experiments/v1/census
```

This is a structural census, not a learning run.

- [ ] **Step 3: Verify custody without rerunning census**

```bash
python - <<'PY'
import hashlib
import json
from pathlib import Path

root = Path("experiments/v1/census")
meta = json.loads((root / "CENSUS.json").read_text())
recorded = dict(
    line.split("  ", 1)
    for line in (root / "SHA256.txt").read_text(encoding="ascii").splitlines()
)
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

- [ ] **Step 4: Fossilize the census record**

If `PASS`:

```bash
git add experiments/v1/census
git commit -m "record: freeze V1 Gladiator structural census"
```

If `ARENA_UNIVERSE_INSUFFICIENT`:

```bash
git add experiments/v1/census
git commit -m "record: close V1 Gladiator insufficient arena census"
```

- [ ] **Step 5: Final G1 verification and hard stop**

```bash
git rev-parse HEAD
git status --short
python -m pytest -q
```

Record HEAD as `GLADIATOR_G1_RECORD_ID_V1`.

**HARD STOP:**

- Insufficient: do not weaken seed, grammar, threshold, or counter window in this session.
- Pass: do not implement G2, freeze V1 TRAIN/EVAL manifests, generalize training corpus, fit LEARN/SCRAMBLED, or inspect a V1 evaluation. Return the G1 record to the user. G2 gets its own approved plan.

---

## Plan Self-Review Record

- **Spec coverage:** ordered five-query chamber, fixed learner, matched 4/4 tie, actual FROZEN root choice, planner-certified >=2 headroom, frozen-feature representability, structural family quotient, fixed million-counter stream, canonical threshold 320, split rank, census-before-learning, and hard stop are each mapped to a task.
- **V0 preservation:** legacy `Menu` remains separate and unchanged; only query-count plumbing is generalized, with the entire V0 suite run immediately after that change.
- **Economy:** canonicalization happens only after structural admission; census retains only family IDs plus at most 320 complete records; G2-G4 are not implemented before G1 earns them.
- **Outcome independence:** no G1 module imports or computes fitted LEARN/SCRAMBLED state.
- **Fixture audit:** split-rank fixture is frozen as `642f088778039fc447d6915450243a1b75726aa30dd11fafd2f0ea8722e21724`; counter-zero generator fixture is `(67,75,92,96,91)`; hand-checkable structural witness is `(16,46,89,4,45)` with tied roots `(1,2,4)` and continuation values `{1:6,2:8,4:8}`.
- **Placeholder scan:** no `TBD`, `TODO`, deferred implementation, or unspecified test step remains.
- **Type consistency:** `GladiatorArena` satisfies `QuerySet`; host/planner consume `QuerySet`; Gladiator analysis and family identity consume the ordered V1 arena; census records use the exact analysis fields defined earlier.
