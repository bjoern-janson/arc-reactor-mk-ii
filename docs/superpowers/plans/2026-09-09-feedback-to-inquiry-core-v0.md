# Feedback-to-Inquiry Core V0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest inspectable feedback-to-inquiry core whose eight-coefficient selector artifact can be trained from informative feedback, transplanted into a fresh host, and evaluated on frozen unseen query configurations without changing primitive tools, belief update, repair rules, or evaluation cases.

**Architecture:** The implementation is a clean-room finite Python package. A hidden-world host owns the true fault; a fixed belief updater owns candidate filtering; a selector ranks only the currently available public queries; a fixed repair rule terminates on a singleton or budget exhaustion. Training uses a policy-independent exhaustive corpus, exact rational ridge regression, and a prospectively fixed within-stratum scrambled-feedback control. Evaluation loads only serialized selector coefficients into an otherwise identical fresh host and compares LEARN, SCRAMBLED, FROZEN, and an exact dynamic-programming planner reference.

**Tech Stack:** Python 3.13.5; Python standard library at runtime; `pytest` for tests; exact arithmetic via `fractions.Fraction`; JSON/JSONL for manifests and artifacts; SHA-256 for canonical IDs and deterministic manifest generation.

**Spec:** `docs/superpowers/specs/2026-09-09-feedback-to-inquiry-core-design.md`

## Global Constraints

- V0 intentionally assumes public query truth tables. It does not study unknown sensor semantics.
- The fault universe is exactly the eight integers `0..7`, interpreted as the eight 3-bit strings.
- Each problem contains exactly four distinct nonconstant binary partitions of the eight faults.
- Every primitive query costs exactly one unit; terminal repair has the same fixed charge in every arm.
- Evaluation budgets are exactly `2` and `3`; all eight faults are enumerated for every evaluation menu.
- Training and evaluation problem identity is canonical under fault-name permutation, query-name permutation, and answer complement.
- Training set size is exactly `256` canonical menus; evaluation set size is exactly `64` disjoint canonical menus.
- No repair outcome, learned score, planner score, or control advantage may affect manifest inclusion.
- FROZEN is the competent greedy balanced-splitting selector: coefficient `1` on `smaller_child_fraction`, `0` on the other seven features.
- LEARN and SCRAMBLED use the same exploration rows, features, primitive tools, storage schema, and evaluation cases.
- SCRAMBLED uses one deterministic prospectively fixed permutation of feedback within equal `(budget, decision_depth)` strata and is never redrawn.
- The learned state is exactly eight selector coefficients plus the feature schema. Training rows, caches, RNG state, problem identifiers, and evaluation labels are not part of the portable artifact.
- Arithmetic for features, fitting, and selector scoring is exact `Fraction` arithmetic. Ridge regularization is exactly `1/100` toward the frozen initial coefficient vector.
- Evaluation is read-only: selector parameters cannot change during evaluation.
- Primary scientific acceptance is deterministic paired repair success on the frozen evaluation family plus successful bidirectional selector-state transplant.
- A positive V0 result does not establish a novel active-learning algorithm, learned primitive sensors, hidden-change detection, safe forgetting, protected corrective-frontier expansion, general intelligence, or compatibility with MATRIX/OpenCore/Revisics/neural systems.
- Resource use is reported as a vector; no hidden scalarization of bytes, working memory, public-table inspections, query executions, terminal actions, or wall-clock time is permitted.
- Implementation completion does not authorize the scientific run. After implementation, tests and frozen manifests must be reviewed and committed; then STOP before full fitting/evaluation until explicitly authorized.

---

## File Map

- `pyproject.toml` — package metadata, Python floor, pytest configuration.
- `src/arc_mkii/domain.py` — immutable finite problem types and query-mask validation.
- `src/arc_mkii/canonical.py` — task canonicalization and canonical identity.
- `src/arc_mkii/manifests.py` — deterministic outcome-independent train/eval manifest generation and protocol serialization.
- `src/arc_mkii/host.py` — hidden-world query execution, fixed belief update, and fixed repair rule.
- `src/arc_mkii/features.py` — exact eight-feature construction from public candidate/query structure.
- `src/arc_mkii/selector.py` — frozen selector schema, exact scoring, deterministic tie-breaking, STOP rule.
- `src/arc_mkii/corpus.py` — exhaustive policy-independent training-row generation.
- `src/arc_mkii/scramble.py` — deterministic within-stratum feedback permutation.
- `src/arc_mkii/fit.py` — exact rational ridge normal equations and exact 8x8 Gaussian elimination.
- `src/arc_mkii/artifact.py` — minimal portable selector serialization/deserialization.
- `src/arc_mkii/planner.py` — exact dynamic-programming planner reference.
- `src/arc_mkii/resources.py` — explicit counters and peak/wall-clock measurement helpers.
- `src/arc_mkii/evaluate.py` — paired deterministic evaluation, traces, transplant checks, acceptance calculation.
- `src/arc_mkii/cli.py` — protocol-freeze, fit, and evaluate entry points.
- `experiments/v0/protocol/` — committed protocol, train/eval manifests, scramble descriptor, and hashes generated before fitting.
- `tests/` — one focused test module per implementation unit plus an end-to-end miniature control.

---

### Task 1: Package skeleton and finite problem domain

**Files:**
- Create: `pyproject.toml`
- Create: `src/arc_mkii/__init__.py`
- Create: `src/arc_mkii/domain.py`
- Test: `tests/test_domain.py`

**Interfaces:**
- Consumes: none.
- Produces: `Fault=int`, `QueryMask=int`, `Menu`, `normalize_partition(mask)`, `answer(mask, fault)`, `candidate_child(mask, query, bit)`.

- [ ] **Step 1: Write the failing domain tests**

```python
from arc_mkii.domain import Menu, answer, normalize_partition


def test_partition_normalization_identifies_answer_complements():
    assert normalize_partition(0b11110000) == 0b00001111
    assert normalize_partition(0b00001111) == 0b00001111


def test_menu_requires_four_distinct_nonconstant_partitions():
    menu = Menu((15, 23, 51, 85))
    assert menu.queries == (15, 23, 51, 85)


def test_query_answer_reads_fault_bit_from_truth_mask():
    assert answer(0b00001000, 3) == 1
    assert answer(0b00001000, 2) == 0
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -m pytest tests/test_domain.py -q`

Expected: import failure because `arc_mkii.domain` does not exist.

- [ ] **Step 3: Implement the minimal finite domain**

```python
from __future__ import annotations

from dataclasses import dataclass

FULL_MASK = 0xFF
FAULTS = tuple(range(8))


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


@dataclass(frozen=True)
class Menu:
    queries: tuple[int, int, int, int]

    def __post_init__(self) -> None:
        normalized = tuple(normalize_partition(q) for q in self.queries)
        if len(set(normalized)) != 4:
            raise ValueError("menu requires four distinct binary partitions")
        object.__setattr__(self, "queries", tuple(sorted(normalized)))
```

`pyproject.toml` must set `requires-python = ">=3.13,<3.14"`, use `src` layout, and configure pytest with `pythonpath = ["src"]`.

- [ ] **Step 4: Run the domain tests and verify GREEN**

Run: `python -m pytest tests/test_domain.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/arc_mkii/__init__.py src/arc_mkii/domain.py tests/test_domain.py
git commit -m "feat: define Mk II finite diagnostic domain"
```

---

### Task 2: Canonical task identity

**Files:**
- Create: `src/arc_mkii/canonical.py`
- Test: `tests/test_canonical.py`

**Interfaces:**
- Consumes: `Menu` from Task 1.
- Produces: `canonical_bytes(menu) -> bytes`, `canonical_id(menu) -> str`.

- [ ] **Step 1: Write invariance tests before implementation**

```python
from arc_mkii.canonical import canonical_bytes, canonical_id
from arc_mkii.domain import Menu


def permute_faults(mask: int, permutation: tuple[int, ...]) -> int:
    out = 0
    for old_fault, new_fault in enumerate(permutation):
        if (mask >> old_fault) & 1:
            out |= 1 << new_fault
    return out


def test_identity_ignores_fault_renaming_query_order_and_answer_complement():
    base = Menu((15, 23, 51, 85))
    renamed = Menu(tuple(permute_faults(q, (7, 6, 5, 4, 3, 2, 1, 0)) for q in reversed(base.queries)))
    complemented = Menu(tuple(q ^ 0xFF for q in base.queries))
    assert canonical_bytes(base) == canonical_bytes(renamed)
    assert canonical_bytes(base) == canonical_bytes(complemented)
    assert canonical_id(base) == canonical_id(renamed)


def test_canonical_bytes_are_exactly_eight_row_bytes():
    assert len(canonical_bytes(Menu((15, 23, 51, 85)))) == 8
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -m pytest tests/test_canonical.py -q`

Expected: import failure for `arc_mkii.canonical`.

- [ ] **Step 3: Implement exhaustive canonicalization exactly as specified**

```python
from __future__ import annotations

import hashlib
import itertools

from .domain import Menu, answer


def canonical_bytes(menu: Menu) -> bytes:
    best: bytes | None = None
    for perm in itertools.permutations(range(4)):
        for complement_bits in range(16):
            rows: list[int] = []
            for fault in range(8):
                row = 0
                for out_col, source_col in enumerate(perm):
                    bit = answer(menu.queries[source_col], fault)
                    if (complement_bits >> out_col) & 1:
                        bit ^= 1
                    row |= bit << out_col
                rows.append(row)
            candidate = bytes(sorted(rows))
            if best is None or candidate < best:
                best = candidate
    if best is None:
        raise RuntimeError("canonicalization produced no candidate")
    return best


def canonical_id(menu: Menu) -> str:
    return hashlib.sha256(b"arc-mkii-task-v0\0" + canonical_bytes(menu)).hexdigest()
```

- [ ] **Step 4: Add a non-equivalence control and rerun**

Add:

```python
def test_structurally_different_menus_can_have_different_ids():
    assert canonical_id(Menu((15, 23, 51, 85))) != canonical_id(Menu((1, 2, 4, 8)))
```

Run: `python -m pytest tests/test_canonical.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/canonical.py tests/test_canonical.py
git commit -m "feat: add representation-invariant task identity"
```

---

### Task 3: Outcome-independent train/evaluation manifests

**Files:**
- Create: `src/arc_mkii/manifests.py`
- Test: `tests/test_manifests.py`

**Interfaces:**
- Consumes: `Menu`, `canonical_id`.
- Produces: `generate_protocol_menus() -> tuple[list[Menu], list[Menu]]`, `protocol_record() -> dict`.

- [ ] **Step 1: Write tests for exact counts, disjoint identities, determinism, and grammar-only selection**

```python
from arc_mkii.canonical import canonical_id
from arc_mkii.manifests import generate_protocol_menus


def test_protocol_split_is_exact_disjoint_and_deterministic():
    train_a, eval_a = generate_protocol_menus()
    train_b, eval_b = generate_protocol_menus()
    assert train_a == train_b
    assert eval_a == eval_b
    assert len(train_a) == 256
    assert len(eval_a) == 64
    train_ids = {canonical_id(m) for m in train_a}
    eval_ids = {canonical_id(m) for m in eval_a}
    assert len(train_ids) == 256
    assert len(eval_ids) == 64
    assert train_ids.isdisjoint(eval_ids)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m pytest tests/test_manifests.py -q`

Expected: import failure for `arc_mkii.manifests`.

- [ ] **Step 3: Implement deterministic hash-counter generation without outcome access**

Use exactly this seed and selection rule:

```python
SEED = b"arc-reactor-mk-ii/v0/menu-seed/2026-09-09"
TRAIN_COUNT = 256
EVAL_COUNT = 64


def _partition_from(seed: bytes, counter: int, slot: int) -> int:
    payload = seed + counter.to_bytes(8, "big") + slot.to_bytes(1, "big")
    digest = hashlib.sha256(payload).digest()
    return 1 + (int.from_bytes(digest[:8], "big") % 127)


def generate_protocol_menus() -> tuple[list[Menu], list[Menu]]:
    accepted: list[Menu] = []
    seen: set[str] = set()
    counter = 0
    while len(accepted) < TRAIN_COUNT + EVAL_COUNT:
        parts = tuple(_partition_from(SEED, counter, slot) for slot in range(4))
        counter += 1
        if len(set(parts)) != 4:
            continue
        menu = Menu(parts)
        cid = canonical_id(menu)
        if cid in seen:
            continue
        seen.add(cid)
        accepted.append(menu)
    return accepted[:TRAIN_COUNT], accepted[TRAIN_COUNT:]
```

`protocol_record()` must return the literal scientific constants: schema `arc-reactor-mkii-protocol/v0`, fault count `8`, query count `4`, budgets `[2, 3]`, train count `256`, eval count `64`, seed string, feature count `8`, ridge lambda numerator/denominator `1/100`, and the explicit scope statement that evaluation novelty is limited to unseen canonical query configurations over the same eight-fault universe.

- [ ] **Step 4: Add a test proving the generator does not accept an outcome callback**

The public signature must remain zero-argument:

```python
import inspect
from arc_mkii.manifests import generate_protocol_menus


def test_manifest_generator_has_no_outcome_or_learner_input():
    assert list(inspect.signature(generate_protocol_menus).parameters) == []
```

Run: `python -m pytest tests/test_manifests.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/manifests.py tests/test_manifests.py
git commit -m "feat: add outcome-independent protocol manifests"
```

---

### Task 4: Hidden-world host, belief update, and fixed repair rule

**Files:**
- Create: `src/arc_mkii/host.py`
- Test: `tests/test_host.py`

**Interfaces:**
- Consumes: `Menu`, `answer`.
- Produces: `HostState`, `initial_state(menu, fault, budget)`, `execute_query(state, query_id)`, `terminal_repair(state)`.

- [ ] **Step 1: Write tests enforcing the information boundary**

```python
from arc_mkii.domain import Menu
from arc_mkii.host import execute_query, initial_state, terminal_repair


def test_query_filters_candidates_without_exposing_hidden_fault_to_selector_state():
    state = initial_state(Menu((15, 23, 51, 85)), fault=6, budget=3)
    next_state = execute_query(state, 0)
    assert next_state.candidate_mask != 0xFF
    assert 6 in next_state.candidates
    assert next_state.remaining_budget == 2


def test_terminal_repair_is_singleton_or_lowest_remaining_fault():
    state = initial_state(Menu((15, 23, 51, 85)), fault=6, budget=0)
    assert terminal_repair(state) == 0
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_host.py -q`

Expected: import failure for `arc_mkii.host`.

- [ ] **Step 3: Implement the immutable host state**

`HostState` must contain `menu`, private scientific-run field `fault`, `candidate_mask`, `remaining_query_ids`, `remaining_budget`, and a tuple of public `(query_id, observed_bit)` observations. The selector-facing projection must omit `fault`.

Core filtering logic:

```python
def execute_query(state: HostState, query_id: int) -> HostState:
    if query_id not in state.remaining_query_ids:
        raise ValueError("query is not available")
    if state.remaining_budget <= 0:
        raise ValueError("query budget exhausted")
    qmask = state.menu.queries[query_id]
    observed = answer(qmask, state.fault)
    kept = 0
    for candidate in range(8):
        if ((state.candidate_mask >> candidate) & 1) and answer(qmask, candidate) == observed:
            kept |= 1 << candidate
    return HostState(
        menu=state.menu,
        fault=state.fault,
        candidate_mask=kept,
        remaining_query_ids=tuple(q for q in state.remaining_query_ids if q != query_id),
        remaining_budget=state.remaining_budget - 1,
        observations=state.observations + ((query_id, observed),),
    )
```

`terminal_repair` returns the unique candidate for a singleton, otherwise the lowest numbered remaining candidate. It must not inspect any information other than `candidate_mask`.

- [ ] **Step 4: Add a selector-view test**

```python
def test_selector_view_contains_no_hidden_fault():
    state = initial_state(Menu((15, 23, 51, 85)), fault=6, budget=3)
    view = state.selector_view()
    assert not hasattr(view, "fault")
    assert view.candidate_mask == 0xFF
```

Run: `python -m pytest tests/test_host.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/arc_mkii/host.py tests/test_host.py
git commit -m "feat: add fixed hidden-world diagnostic host"
```

---

### Task 5: Exact feature construction and FROZEN selector

**Files:**
- Create: `src/arc_mkii/features.py`
- Create: `src/arc_mkii/selector.py`
- Test: `tests/test_features.py`
- Test: `tests/test_selector.py`

**Interfaces:**
- Consumes: selector-facing host state.
- Produces: `FEATURE_NAMES`, `feature_vector(view, query_id) -> tuple[Fraction, ...]`, `Theta`, `THETA0`, `choose_query(theta, view) -> int | None`.

- [ ] **Step 1: Write exact feature tests**

```python
from fractions import Fraction

from arc_mkii.domain import Menu
from arc_mkii.features import FEATURE_NAMES, feature_vector
from arc_mkii.host import initial_state


def test_feature_schema_is_exact_and_public_only():
    assert FEATURE_NAMES == (
        "intercept",
        "remaining_budget_over_3",
        "candidate_count_over_8",
        "smaller_child_fraction",
        "child_fraction_product",
        "singleton_child_candidate_fraction",
        "weighted_best_next_split",
        "worst_child_best_next_split",
    )
    view = initial_state(Menu((15, 23, 51, 85)), fault=0, budget=3).selector_view()
    f = feature_vector(view, 0)
    assert len(f) == 8
    assert f[0] == Fraction(1, 1)
    assert f[1] == Fraction(1, 1)
    assert f[2] == Fraction(1, 1)
    assert f[3] == Fraction(1, 2)
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_features.py -q`

Expected: import failure for `arc_mkii.features`.

- [ ] **Step 3: Implement the eight features exactly**

For proposed query `q`, form nonempty child candidate masks `C0` and `C1`. Let `n=|C|`, `n0=|C0|`, `n1=|C1|`.

- `smaller_child_fraction = min(n0,n1)/n`.
- `child_fraction_product = (n0/n)*(n1/n)`.
- `singleton_child_candidate_fraction = (sum size(child) for child with size 1)/n`.
- If the current `remaining_budget <= 1`, both next-query features are exactly zero.
- Otherwise define branch score as `1/2` for singleton child; for non-singleton child, the maximum smaller-child fraction induced by any remaining query other than the proposed query, or `0` if no query splits it.
- `weighted_best_next_split` is the candidate-count-weighted mean of branch scores across nonempty children.
- `worst_child_best_next_split` is the minimum branch score across nonempty children.

All intermediate values must be `Fraction` objects.

- [ ] **Step 4: Write the FROZEN selector tests**

```python
from arc_mkii.domain import Menu
from arc_mkii.host import initial_state
from arc_mkii.selector import THETA0, choose_query


def test_theta0_has_one_balance_weight_and_seven_zero_weights():
    assert tuple(THETA0) == (0, 0, 0, 1, 0, 0, 0, 0)


def test_frozen_control_uses_public_query_order_for_exact_ties():
    view = initial_state(Menu((15, 23, 51, 85)), fault=0, budget=3).selector_view()
    assert choose_query(THETA0, view) == 0
```

- [ ] **Step 5: Implement exact selector scoring and structural STOP**

`choose_query` must return `None` only when candidate count is one, budget is zero, no queries remain, or no remaining query changes the current candidate set. Otherwise score every useful remaining query by exact dot product of `theta` and `feature_vector`, choose the maximum, and break exact ties by the smallest public query ID.

- [ ] **Step 6: Add the hand-checkable control menu test**

For `Menu((15, 23, 51, 85))`, verify by exact host execution that the three coordinate partitions can identify all eight faults within budget 3, while beginning with the majority partition (`23`) cannot exceed `6/8` repair success with two coordinate queries remaining. This test proves only that query order can matter.

Run: `python -m pytest tests/test_features.py tests/test_selector.py -q`

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/arc_mkii/features.py src/arc_mkii/selector.py tests/test_features.py tests/test_selector.py
git commit -m "feat: add exact query features and frozen selector"
```

---

### Task 6: Policy-independent exhaustive training corpus and fixed scramble

**Files:**
- Create: `src/arc_mkii/corpus.py`
- Create: `src/arc_mkii/scramble.py`
- Test: `tests/test_corpus.py`
- Test: `tests/test_scramble.py`

**Interfaces:**
- Consumes: training menus, host, feature vectors.
- Produces: immutable `TrainingRow`; `build_training_rows(menus)`; `scramble_feedback(rows)`; compact `scramble_descriptor(rows)`.

- [ ] **Step 1: Write a corpus completeness test on one menu**

```python
from arc_mkii.corpus import build_training_rows
from arc_mkii.domain import Menu


def test_corpus_uses_every_ordered_distinct_query_sequence_for_each_budget_and_fault():
    rows = build_training_rows([Menu((15, 23, 51, 85))])
    assert {row.budget for row in rows} == {2, 3}
    assert {row.fault for row in rows} == set(range(8))
    assert all(row.feedback in (0, 1) for row in rows)
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_corpus.py -q`

Expected: import failure for `arc_mkii.corpus`.

- [ ] **Step 3: Implement exhaustive collection with no selector involvement**

For each training menu sorted by canonical ID, budget in `(2,3)`, fault in `0..7`, and lexicographically ordered permutation of distinct query IDs of length `budget`, execute that fixed sequence until a singleton is reached or the sequence/budget ends. Record one row for every actually executed `(state, query)` pair. After terminal repair, assign the same binary terminal success to every preceding row from that sequence.

`TrainingRow` must include only reconstructible provenance and public selector input plus the feedback label: canonical task ID, representative query masks, budget, fault for corpus provenance, full planned sequence, decision depth, candidate mask before action, remaining query IDs, action query ID, exact feature vector, terminal repair, and feedback. The fitting layer may read `features` and `feedback`; it may not read `fault` or terminal repair.

Define `row_id` as SHA-256 over canonical JSON of all row provenance fields except `feedback`, domain-separated by `b"arc-mkii-training-row-v0\0"`.

- [ ] **Step 4: Write scramble conservation and non-redraw tests**

```python
from collections import Counter, defaultdict

from arc_mkii.corpus import build_training_rows
from arc_mkii.domain import Menu
from arc_mkii.scramble import scramble_feedback


def test_scramble_preserves_feedback_multiset_within_each_budget_depth_stratum():
    rows = build_training_rows([Menu((15, 23, 51, 85)), Menu((1, 2, 4, 8))])
    scrambled_a = scramble_feedback(rows)
    scrambled_b = scramble_feedback(rows)
    assert scrambled_a == scrambled_b
    for key in {(r.budget, r.decision_depth) for r in rows}:
        original = [r.feedback for r in rows if (r.budget, r.decision_depth) == key]
        changed = [s.feedback for s in scrambled_a if (s.budget, s.decision_depth) == key]
        assert Counter(original) == Counter(changed)
```

- [ ] **Step 5: Implement the exact fixed permutation**

Within each `(budget, decision_depth)` stratum, sort rows by `row_id`. Let `n` be stratum size. For `n>1`, compute:

```python
seed = f"arc-reactor-mk-ii/v0/scramble/{budget}/{depth}".encode()
offset = 1 + (int.from_bytes(hashlib.sha256(seed).digest()[:8], "big") % (n - 1))
```

Assign destination row `i` the feedback from source row `(i + offset) % n`. For `n==1`, offset is `0`. `scramble_descriptor` stores schema, every stratum size and offset, and the SHA-256 of the ordered row-ID list. This descriptor is sufficient to reconstruct the exact permutation and is the retained prospective control; no redraw is possible without changing the descriptor.

- [ ] **Step 6: Run corpus and scramble tests**

Run: `python -m pytest tests/test_corpus.py tests/test_scramble.py -q`

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/arc_mkii/corpus.py src/arc_mkii/scramble.py tests/test_corpus.py tests/test_scramble.py
git commit -m "feat: add exhaustive training corpus and fixed scramble"
```

---

### Task 7: Exact ridge fitter and minimal selector artifact

**Files:**
- Create: `src/arc_mkii/fit.py`
- Create: `src/arc_mkii/artifact.py`
- Test: `tests/test_fit.py`
- Test: `tests/test_artifact.py`

**Interfaces:**
- Consumes: training rows, `THETA0`, feature schema.
- Produces: `fit_theta(rows) -> tuple[Fraction, ...]`, `save_artifact(path, theta)`, `load_artifact(path) -> tuple[Fraction, ...]`.

- [ ] **Step 1: Write exact normal-equation tests**

```python
from fractions import Fraction

from arc_mkii.fit import solve_linear_system


def test_fraction_solver_returns_exact_solution():
    a = [
        [Fraction(2), Fraction(1)],
        [Fraction(1), Fraction(3)],
    ]
    b = [Fraction(1), Fraction(2)]
    assert solve_linear_system(a, b) == [Fraction(1, 5), Fraction(3, 5)]
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_fit.py -q`

Expected: import failure for `arc_mkii.fit`.

- [ ] **Step 3: Implement exact ridge fitting**

Accumulate the 8x8 normal matrix and 8-vector exactly:

```python
LAMBDA = Fraction(1, 100)


def fit_theta(rows: Sequence[TrainingRow]) -> tuple[Fraction, ...]:
    p = 8
    a = [[Fraction(0) for _ in range(p)] for _ in range(p)]
    b = [Fraction(0) for _ in range(p)]
    for row in rows:
        x = row.features
        y = Fraction(row.feedback)
        for i in range(p):
            b[i] += x[i] * y
            for j in range(p):
                a[i][j] += x[i] * x[j]
    for i in range(p):
        a[i][i] += LAMBDA
        b[i] += LAMBDA * THETA0[i]
    return tuple(solve_linear_system(a, b))
```

`solve_linear_system` uses deterministic Gauss-Jordan elimination: at each column choose the first row at or below the diagonal with a nonzero pivot, swap it into place, normalize the pivot row exactly, then eliminate that column from every other row. Raise `ValueError` on singularity. No floats are permitted.

- [ ] **Step 4: Write artifact isolation tests**

```python
import json
from fractions import Fraction

from arc_mkii.artifact import load_artifact, save_artifact
from arc_mkii.selector import THETA0


def test_artifact_round_trip_contains_only_schema_features_and_theta(tmp_path):
    path = tmp_path / "theta.json"
    save_artifact(path, tuple(Fraction(x) for x in THETA0))
    raw = json.loads(path.read_text())
    assert set(raw) == {"schema", "features", "theta"}
    assert load_artifact(path) == tuple(Fraction(x) for x in THETA0)
```

- [ ] **Step 5: Implement exact rational JSON serialization**

Each coefficient is serialized as `{"n": numerator, "d": denominator}`. Schema is exactly `arc-reactor-mkii-selector/v0`; feature list must equal `FEATURE_NAMES`. `load_artifact` rejects any unknown top-level key, schema mismatch, feature-order mismatch, nonpositive denominator, or coefficient count other than eight.

- [ ] **Step 6: Run fitter and artifact tests**

Run: `python -m pytest tests/test_fit.py tests/test_artifact.py -q`

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/arc_mkii/fit.py src/arc_mkii/artifact.py tests/test_fit.py tests/test_artifact.py
git commit -m "feat: add exact selector fitting and portable artifact"
```

---

### Task 8: Exact planner, resource counters, paired evaluator, and acceptance rule

**Files:**
- Create: `src/arc_mkii/planner.py`
- Create: `src/arc_mkii/resources.py`
- Create: `src/arc_mkii/evaluate.py`
- Test: `tests/test_planner.py`
- Test: `tests/test_evaluate.py`

**Interfaces:**
- Consumes: menus, artifacts/selectors, host.
- Produces: planner reference result, per-case traces, per-budget exact success counts, resource vectors, transplant checks, deterministic acceptance decision.

- [ ] **Step 1: Write planner controls**

```python
from arc_mkii.domain import Menu
from arc_mkii.planner import planner_success_count


def test_exact_planner_solves_coordinate_menu_with_budget_three():
    menu = Menu((15, 23, 51, 85))
    assert planner_success_count(menu, budget=3) == 8
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_planner.py -q`

Expected: import failure for `arc_mkii.planner`.

- [ ] **Step 3: Implement planner as a pure dynamic program**

State key is `(candidate_mask, remaining_query_ids, remaining_budget)`. Terminal value is `1` for any nonempty candidate set when budget is zero/no useful query remains, because the fixed repair rule can be correct for exactly one remaining fault; singleton value is also `1`. For each useful query, recurse on both nonempty child masks and sum their correct-state counts. Select the query with maximum summed count, breaking ties by smallest public query ID. Memoize only within planner evaluation and report number of unique states expanded.

- [ ] **Step 4: Write evaluator and transplant tests using synthetic thetas**

```python
from fractions import Fraction

from arc_mkii.domain import Menu
from arc_mkii.evaluate import evaluate_theta, transplant_equivalent
from arc_mkii.selector import THETA0


def test_same_theta_in_fresh_hosts_has_identical_traces_and_scores():
    menus = [Menu((15, 23, 51, 85))]
    theta = tuple(Fraction(x) for x in THETA0)
    left = evaluate_theta("left", theta, menus)
    right = evaluate_theta("right", theta, menus)
    assert left.case_traces == right.case_traces
    assert left.success_by_budget == right.success_by_budget


def test_transplant_equivalence_compares_behavior_not_object_identity():
    menus = [Menu((15, 23, 51, 85))]
    theta = tuple(Fraction(x) for x in THETA0)
    assert transplant_equivalent(theta, theta, menus)
```

- [ ] **Step 5: Implement exact paired evaluation**

For each menu in manifest order, budget in `(2,3)`, and fault in `0..7`, start a fresh host, repeatedly call the selector until structural STOP, then execute fixed repair. Record canonical task ID, budget, fault, selected query IDs, observed bits, candidate masks after each query, repair, success, query count, and exact selector scores for all candidate actions at each decision. Training is disabled and no caches survive between artifact evaluations.

Return exact integer success counts per budget and exact paired per-case outcomes. Do not compute a p-value or treat the 1,024 correlated cases as independent replications.

- [ ] **Step 6: Implement the acceptance rule literally**

Given LEARN, SCRAMBLED, and FROZEN results:

```python
def ignition_pass(learn, scrambled, frozen, transplant_ok: bool) -> bool:
    if not transplant_ok:
        return False
    strict_budget = any(
        learn.success_by_budget[b] > scrambled.success_by_budget[b]
        and learn.success_by_budget[b] > frozen.success_by_budget[b]
        for b in (2, 3)
    )
    no_loss = all(
        learn.success_by_budget[b] >= scrambled.success_by_budget[b]
        and learn.success_by_budget[b] >= frozen.success_by_budget[b]
        for b in (2, 3)
    )
    return strict_budget and no_loss
```

A gain at one budget plus a loss at the other returns `False` and remains a recorded tradeoff.

- [ ] **Step 7: Add resource-vector instrumentation**

`ResourceReport` must contain: `artifact_bytes`, `peak_python_bytes` from `tracemalloc`, `wall_time_ns` from `perf_counter_ns`, `training_rows_consumed`, `feature_vectors_computed`, `public_truth_table_bit_inspections`, `primitive_query_executions`, `terminal_actions`, and `planner_states_expanded`. Counters are raw quantities. No weighted total is computed in V0.

- [ ] **Step 8: Run planner/evaluator tests**

Run: `python -m pytest tests/test_planner.py tests/test_evaluate.py -q`

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add src/arc_mkii/planner.py src/arc_mkii/resources.py src/arc_mkii/evaluate.py tests/test_planner.py tests/test_evaluate.py
git commit -m "feat: add exact planner and deterministic evaluation"
```

---

### Task 9: CLI, protocol freeze artifacts, and preflight gate

**Files:**
- Create: `src/arc_mkii/cli.py`
- Create: `tests/test_cli.py`
- Create during this task: `experiments/v0/protocol/PROTOCOL.json`
- Create during this task: `experiments/v0/protocol/TRAIN_MENUS.jsonl`
- Create during this task: `experiments/v0/protocol/EVAL_MENUS.jsonl`
- Create during this task: `experiments/v0/protocol/SCRAMBLE.json`
- Create during this task: `experiments/v0/protocol/MANIFEST_SHA256.txt`

**Interfaces:**
- Consumes: all preceding modules.
- Produces: three commands: `freeze-protocol`, `fit`, `evaluate`.

- [ ] **Step 1: Write CLI tests for command separation**

```python
from arc_mkii.cli import build_parser


def test_cli_has_separate_protocol_fit_and_evaluate_commands():
    parser = build_parser()
    help_text = parser.format_help()
    assert "freeze-protocol" in help_text
    assert "fit" in help_text
    assert "evaluate" in help_text
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_cli.py -q`

Expected: import failure for `arc_mkii.cli`.

- [ ] **Step 3: Implement `freeze-protocol` only as an outcome-free operation**

`freeze-protocol --out experiments/v0/protocol` must:

1. Generate exactly 256 train and 64 evaluation menus using Task 3.
2. Serialize one canonical JSON record per menu containing `canonical_id` and the four representative normalized query masks.
3. Build training rows only to derive the compact deterministic SCRAMBLE stratum offsets and ordered-row-list hashes; it must not fit coefficients.
4. Write `PROTOCOL.json`, `TRAIN_MENUS.jsonl`, `EVAL_MENUS.jsonl`, and `SCRAMBLE.json` with UTF-8, LF newlines, sorted JSON keys, and compact separators.
5. Write `MANIFEST_SHA256.txt` with SHA-256 for those four files in lexicographic filename order.
6. Refuse to overwrite an existing protocol directory unless every byte it would write is identical.

- [ ] **Step 4: Implement `fit` as a separate command without evaluation access**

`fit --protocol DIR --arm learn|scrambled --out ARTIFACT` loads only `PROTOCOL.json`, `TRAIN_MENUS.jsonl`, and `SCRAMBLE.json`; it must never open `EVAL_MENUS.jsonl`. LEARN fits actual labels; SCRAMBLED fits the fixed permuted labels. FROZEN artifact creation is a separate zero-training path that serializes `THETA0` exactly. Each fit writes the minimal selector artifact plus a separate provenance receipt containing implementation commit, protocol hashes, arm, training row count, raw resource vector, and artifact SHA-256.

- [ ] **Step 5: Implement `evaluate` as read-only and artifact-swappable**

`evaluate --protocol DIR --learn LEARN.json --scrambled SCRAMBLED.json --frozen FROZEN.json --out DIR` loads the committed evaluation manifest and the three minimal artifacts into fresh host instances. It writes per-case traces, aggregate exact success counts, planner reference, resource reports, bidirectional transplant comparison, and `IGNITION_PASS` from Task 8. It performs no fitting and rejects artifacts with schema mismatch.

- [ ] **Step 6: Run all tests before generating protocol files**

Run: `python -m pytest -q`

Expected: entire suite passes.

- [ ] **Step 7: Generate the prospective protocol files**

Run:

```bash
python -m arc_mkii.cli freeze-protocol --out experiments/v0/protocol
```

Then immediately run the same command again.

Expected: second invocation reports byte-identical existing protocol and exits successfully without mutation.

- [ ] **Step 8: Verify frozen protocol invariants without fitting**

Run a small validation command or test that asserts:

- 256 unique train canonical IDs.
- 64 unique evaluation canonical IDs.
- zero train/eval identity overlap.
- every menu has exactly four distinct nonconstant partitions.
- budgets are exactly `[2,3]`.
- protocol feature schema and lambda match the spec.
- SCRAMBLE contains exactly one deterministic descriptor per observed `(budget, depth)` stratum.
- all four protocol file SHA-256 values match `MANIFEST_SHA256.txt`.

No `fit` or `evaluate` command may be invoked in this task.

- [ ] **Step 9: Commit implementation and frozen protocol together**

```bash
git add src/arc_mkii/cli.py tests/test_cli.py experiments/v0/protocol
git commit -m "freeze: add Mk II V0 protocol and execution gates"
```

- [ ] **Step 10: Record the implementation freeze identity and STOP**

Run:

```bash
git rev-parse HEAD
git status --short
python -m pytest -q
```

Record the exact HEAD as `IMPLEMENTATION_FREEZE_ID_V0` in the execution handoff. Expected working tree: clean. Expected tests: all pass.

**STOP CONDITION:** Do not invoke `fit` on the 256-menu corpus and do not inspect any 64-menu evaluation result in this implementation session. Full fitting/evaluation is the scientific run and requires explicit authorization after this freeze is reviewed.

---

## Plan Self-Review Record

This plan covers every section of the approved design:

- Public-query semantics and selector information boundary: Tasks 4–5.
- Eight-fault/four-query finite apparatus and budgets 2/3: Tasks 1, 4, 8.
- Canonical identity and train/evaluation separation: Tasks 2–3, 9.
- Eight-feature linear selector and competent FROZEN baseline: Task 5.
- Shared exhaustive policy-independent exploration corpus: Task 6.
- Exact ridge fit toward the initial coefficients: Task 7.
- LEARN/SCRAMBLED/FROZEN controls and one fixed scramble: Tasks 6–7, 9.
- Minimal standalone selector artifact and bidirectional transplant: Tasks 7–8.
- Exact planner reference: Task 8.
- Paired repair outcomes, wins/losses/traces, no false independent-replication claim: Task 8.
- Literal acceptance rule including no-loss-at-other-budget condition: Task 8.
- Resource accounting without forced equal spending or hidden scalarization: Task 8.
- Portability only to a fresh identical host in V0: Tasks 7–9.
- Prospective freeze before learned-result inspection and explicit stop before the scientific run: Task 9.

No implementation task claims transfer to other repositories, hidden-change detection, safe forgetting, learned sensors, frontier expansion, or general intelligence.
