# V2 G3 Execution Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use test-driven development and verification-before-completion. Execute task-by-task with review gates.

**Goal:** Make the G2-frozen V2 experiment executable without producing any V2 learned or evaluated result.

**Architecture:** Add V2-specific adapters around byte-unchanged scientific primitives. The official G3 verifier may construct the 817,105 frozen TRAIN row identities and validate custody, but cannot call result-bearing fitting/evaluation/autopsy paths. A separate dormant G4 entry point and workflow encode the future result order but are not executed during G3.

**Tech Stack:** Python 3.13, stdlib, `Fraction`, pytest, GitHub Actions.

**Spec:** `experiments/v2/G3_EXECUTION_FREEZE_DESIGN.md`

## Global constraints

- Base executable ancestry: `5689645287c41a71e109f1b022529e8b98f2006d`.
- Frozen G2 protocol manifest SHA-256: `419b7be408a5a37ab6a7ee304ac58646683a6fc4771b503e0b0f475002b4d075`.
- Exact TRAIN row count: 817,105.
- No V2 fitting, EVAL execution, ignition, replay result, or root-autopsy value during G3.
- Preserve `features.py`, `selector.py`, `fit.py`, `artifact.py`, and the frozen G2 protocol payloads byte-for-byte.
- `canonical_task_id = family_id` for V2 TRAIN and EVAL identities.
- G4 lock must precede first V2 fit; primary result fossil must precede real root-autopsy computation.

---

### Task 1: G3 verification contract and RED tests

**Files:**
- Create: `tests/test_v2_g3_execution.py`
- Create: `.github/workflows/v2-g3-ci.yml`

**Interfaces:**
- Expected future module: `arc_mkii.v2_g3_execution`
- Expected future CLI: `python -m arc_mkii.v2_g3_cli verify ...`

- [ ] Add tests that require exact G2 manifest provenance and immutable frozen payloads.
- [ ] Add tests for six-query TRAIN row construction and exact row-ID compatibility with the G2 row identity contract.
- [ ] Add tests that the real frozen TRAIN protocol yields the five exact sizes, offsets, row-ID-list hashes, and total 817,105 rows.
- [ ] Add tests that forbidden result modules/functions are not reachable from the G3 verification entry point.
- [ ] Add tests that G3 verification leaves no result-bearing files.
- [ ] Add synthetic EVAL identity tests proving `CaseTrace.canonical_task_id = family_id` without loading the frozen 64 EVAL arenas.
- [ ] Add synthetic tests for artifact round-trip, unchanged ridge semantics, unchanged SCRAMBLED mapping semantics, and frozen ignition predicate compatibility.
- [ ] Run CI and verify RED because `arc_mkii.v2_g3_execution` does not yet exist.

### Task 2: V2 TRAIN executable adapter

**Files:**
- Create: `src/arc_mkii/v2_g3_execution.py`

**Interfaces:**
- `V2TrainingRow` with the same fit-facing attributes as V0 `TrainingRow` plus frozen V2 identity.
- `load_frozen_g2_protocol(...)`
- `iter_v2_training_rows(...)`
- `verify_train_corpus_against_scramble(...)`
- `g3_verify(...)`

- [ ] Implement a six-query `V2TrainingRow` whose `row_id` is exactly the G2-frozen row serialization.
- [ ] Build rows only from frozen `TRAIN_ARENAS.jsonl` family records.
- [ ] Reproduce V0 semantics: ordered query permutations, staged pre-action state/features, terminal repair, terminal binary feedback copied to staged rows.
- [ ] Group by `(budget, decision_depth)`, sort by `row_id`, and compare exact sizes/offsets/list hashes to frozen `SCRAMBLE.json`.
- [ ] Refuse corpus admission on any mismatch.
- [ ] Ensure G3 verification never imports/calls V2 fitting/evaluation/autopsy execution.
- [ ] Run focused tests then full suite.

### Task 3: Dormant V2 result-capable adapters on synthetic fixtures only

**Files:**
- Create: `src/arc_mkii/v2_g4_execution.py`
- Create: `tests/test_v2_g4_synthetic.py`

**Interfaces:**
- `evaluate_v2_theta(...)` accepts explicit V2 arena records and preserves frozen `family_id` as trace identity.
- `build_scrambled_rows(...)` applies exact frozen within-stratum permutation semantics to V2 rows.
- `execute_primary_result(...)` is result-capable but never called by G3 verifier/tests on frozen V2 EVAL.
- `compute_root_autopsy(...)` accepts an already-durable primary-result receipt and is callable only downstream.

- [ ] Implement V2 evaluation adapter without recanonicalization or arena substitution.
- [ ] Implement SCRAMBLED feedback replacement using frozen offsets and row ordering.
- [ ] Reuse `fit_theta`, `THETA0`, artifact serialization, host/selector/features, and `ignition_pass` unchanged.
- [ ] Test only on tiny synthetic six-query fixtures and already-public non-V2 behavior.
- [ ] Add guards requiring a primary-result receipt before autopsy execution.
- [ ] Verify no real V2 EVAL payload is loaded in tests.

### Task 4: Freeze future G4 execution topology

**Files:**
- Create: `.github/workflows/v2-g4-official-execution.yml`
- Create: `experiments/v2/G4_EXECUTION_ORDER_CONTRACT.md`

**Interfaces:**
- Workflow is triggered only from a future frozen G3 implementation branch/ref and must not trigger during G3 implementation.

- [ ] Encode exact implementation/protocol verification before result-bearing work.
- [ ] Refuse if a G4 start lock or result branch already exists.
- [ ] Create exactly-once G4 start lock before first V2 fit.
- [ ] Fit LEARN/SCRAMBLED and materialize FROZEN only after the lock.
- [ ] Serialize artifacts/receipts, evaluate frozen EVAL, perform replay-equivalence check, compute frozen ignition.
- [ ] Fossilize the primary result before invoking root-autopsy diagnostics.
- [ ] Fossilize autopsy separately as downstream nonacceptance record.
- [ ] Do not run this workflow in G3.

### Task 5: G3 official freeze workflow and record

**Files:**
- Create: `.github/workflows/v2-g3-official-freeze.yml`

**Interfaces:**
- Trigger only on `freeze/v2-g3-implementation`.
- Emit `freeze/v2-g3-executable` / G3 record as a direct child of the implementation freeze.

- [ ] Verify exact G3 implementation SHA, G2 ancestry, G2 protocol manifest, and frozen G2 payload hashes.
- [ ] Run full repository suite and the isolated G3 verifier.
- [ ] Verify 817,105-row corpus bridge and all five frozen SCRAMBLED strata.
- [ ] Verify forbidden result artifacts are absent before and after verification.
- [ ] Verify frozen G2 protocol/autopsy files remain byte-identical.
- [ ] Write a bounded `G3_RECORD.md` containing only executability/custody facts.
- [ ] Fossilize direct child with authorization boundary `G4 RESULT-BEARING EXECUTION AUTHORIZED ONLY`.

### Task 6: Final verification and STOP

- [ ] Compare frozen G2 protocol to G3 implementation diff and confirm only G3 adapters/tests/workflows/docs were added.
- [ ] Confirm byte identities of `features.py`, `selector.py`, `fit.py`, `artifact.py`, and all G2 protocol payloads.
- [ ] Confirm no V2 theta/result/eval/autopsy/ignition artifact exists.
- [ ] Confirm G3 implementation CI green at final SHA.
- [ ] Create `freeze/v2-g3-implementation` only after green CI.
- [ ] Let the official G3 workflow fossilize the executable record.
- [ ] Verify direct-parent lineage and bounded G3 record.
- [ ] STOP. Do not trigger G4.
