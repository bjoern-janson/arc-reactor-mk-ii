# V2 G2 Protocol Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Constitute and fossilize the V2 G2 protocol from the already committed 436 G1 families without fitting a coefficient, evaluating an arm, or computing a root-autopsy value.

**Architecture:** Add a G2-only protocol module and CLI that consume the G1 fossil, deterministically rank/split the 436 retained families, derive V0-compatible six-query training row identities solely to freeze the existing SCRAMBLED descriptor, write the exact V2 protocol payload set, and fail closed on any provenance or hash mismatch. The G2 module must not import `arc_mkii.fit` or `arc_mkii.evaluate`.

**Tech Stack:** Python 3.13, standard library only, `fractions.Fraction`, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-10-feedback-to-inquiry-v2-g2-protocol-freeze-design.md`

## Global Constraints

- Parent scientific record: `1edf919be5a9810d8e670ed26c0174642b3e7756`.
- G1 implementation freeze: `9ba2e6e8ad448e72702ade6af23f4a1a25fbe932`.
- G1 hashes must equal the frozen `CENSUS.json` and `FAMILIES.jsonl` SHA-256 values in the spec.
- Consume `experiments/v2/g1-census/FAMILIES.jsonl`; never run the V2 census.
- TRAIN/EVAL/outside counts are exactly 256/64/116.
- Preserve V0 row-ID serialization and V0 SCRAMBLED offset/strata semantics.
- No import of `arc_mkii.fit` or `arc_mkii.evaluate` from G2 code.
- No fitted theta, EVAL execution, ignition, or root-autopsy values.

---

### Task 1: RED tests for deterministic G2 split and provenance

**Files:**
- Create: `tests/test_v2_g2_protocol.py`

**Interfaces:**
- Consumes future functions `load_g1_custody(path)`, `rank_families(records)`, `split_families(records)` from `arc_mkii.v2_g2_protocol`.
- Produces executable requirements for exact provenance, ranking, and role counts.

- [ ] **Step 1: Write failing tests**

Create tests that import the not-yet-existing module and assert:

```python
from arc_mkii.v2_g2_protocol import (
    EXPECTED_G1_CENSUS_SHA256,
    EXPECTED_G1_FAMILIES_SHA256,
    split_rank,
    split_families,
)


def test_split_rank_uses_frozen_prefix():
    family_id = "00" * 32
    expected = hashlib.sha256(
        b"arc-mkii-v2-six-query-gladiator-split\0" + family_id.encode("ascii")
    ).hexdigest()
    assert split_rank(family_id) == expected


def test_split_counts_on_436_unique_records():
    records = [fixture_family(i) for i in range(436)]
    split = split_families(records)
    assert len(split.train) == 256
    assert len(split.eval) == 64
    assert len(split.outside) == 116
    assert [row.rank for row in split.all_rows] == list(range(436))
```

Add negative tests for duplicate family IDs, malformed family IDs, non-six-query records, and wrong G1 payload hashes.

- [ ] **Step 2: Verify RED in GitHub Actions**

Push only the test file on `impl/v2-g2-protocol-freeze` and run `pytest -q tests/test_v2_g2_protocol.py` through the branch CI. Expected: collection failure because `arc_mkii.v2_g2_protocol` does not exist.

---

### Task 2: GREEN split/provenance implementation

**Files:**
- Create: `src/arc_mkii/v2_g2_protocol.py`

**Interfaces:**
- `split_rank(family_id: str) -> str`
- `load_g1_custody(root: Path) -> tuple[dict[str, object], tuple[FamilyInput, ...]]`
- `rank_families(records: Iterable[FamilyInput]) -> tuple[RankedFamily, ...]`
- `split_families(records: Iterable[FamilyInput]) -> ProtocolSplit`

- [ ] **Step 1: Implement constants and immutable records**

Define exact G1 IDs/hashes, split prefix, counts, schemas, and frozen role names. `load_g1_custody` must hash raw G1 bytes before parsing and require `G1_PASS`, `admitted_canonical=436`, the implementation SHA, and the exact existing field set.

- [ ] **Step 2: Implement ranking and split**

`split_rank` must be exactly:

```python
def split_rank(family_id: str) -> str:
    _require_hex64(family_id, "family_id")
    return hashlib.sha256(SPLIT_PREFIX + family_id.encode("ascii")).hexdigest()
```

Sort `(split_rank, family_id)`, assign contiguous ranks, and roles by frozen rank intervals.

- [ ] **Step 3: Run focused tests**

Run `pytest -q tests/test_v2_g2_protocol.py`. Expected: current split/provenance tests pass; later row-ID tests not yet present.

---

### Task 3: RED/GREEN V0-compatible six-query row identities and SCRAMBLED descriptor

**Files:**
- Modify: `tests/test_v2_g2_protocol.py`
- Modify: `src/arc_mkii/v2_g2_protocol.py`

**Interfaces:**
- `training_row_identity_records(arenas: Iterable[RankedFamily]) -> Iterator[RowIdentity]`
- `scramble_descriptor_for_train(arenas: Iterable[RankedFamily]) -> dict[str, object]`

- [ ] **Step 1: Write row-ID compatibility test first**

Build one existing four-query `Menu`, obtain an existing V0 `TrainingRow` from `build_training_rows([menu])`, and construct the equivalent G2 row-identity payload from its public fields. Assert the G2 serializer produces exactly `row.row_id`.

Add a six-query fixture test asserting query IDs `0..5` are traversed and strata are exactly `(2,0),(2,1),(3,0),(3,1),(3,2)`.

- [ ] **Step 2: Verify RED**

Run focused tests; expected failure because generic row identity helpers do not exist.

- [ ] **Step 3: Implement generic row-ID serializer**

Reuse `initial_state`, `execute_query`, `terminal_repair`, and `feature_vector`. Do not call `build_training_rows`, `fit_theta`, `scramble_feedback`, or evaluator code. Serialize the exact V0 row-ID fields and prefix `b"arc-mkii-training-row-v0\0"`.

- [ ] **Step 4: Implement descriptor**

Group row IDs by `(budget,decision_depth)`, sort IDs, use the frozen V0 `_offset` formula locally or through a non-fitting helper, and hash with prefix `b"arc-mkii-row-id-list-v0\0"`. Emit schema `arc-reactor-mkii-scramble/v0` and only `budget`, `decision_depth`, `size`, `offset`, `row_ids_sha256`.

- [ ] **Step 5: Verify GREEN**

Run focused tests, then full `pytest -q`.

---

### Task 4: RED/GREEN protocol writer and fail-closed verifier

**Files:**
- Modify: `tests/test_v2_g2_protocol.py`
- Modify: `src/arc_mkii/v2_g2_protocol.py`
- Create: `src/arc_mkii/v2_g2_cli.py`

**Interfaces:**
- `freeze_v2_protocol(g1_root: Path, out: Path) -> None`
- `verify_v2_protocol(g1_root: Path, protocol: Path) -> V2ProtocolVerification`
- CLI: `python -m arc_mkii.v2_g2_cli freeze --g1-root experiments/v2/g1-census --out <path>`
- CLI: `python -m arc_mkii.v2_g2_cli verify --g1-root experiments/v2/g1-census --protocol <path>`

- [ ] **Step 1: Write failing writer/verifier tests**

Assert exact payload set, canonical JSON formatting, exact 256/64/116 role files, all-436 `SPLIT_RANKS.jsonl`, no fitted/output fields, idempotence for byte-identical directory, rejection of altered payload, missing payload, role overlap, split-rank mutation, and malformed root-autopsy contract.

- [ ] **Step 2: Verify RED**

Run focused tests; expected failure on missing writer/verifier.

- [ ] **Step 3: Implement writer**

Generate only the eight exact files from the spec. `ROOT_AUTOPSY_CONTRACT.json` contains names/definitions/status/algorithm steps but no diagnostic values. Hash the seven non-manifest payloads in lexical filename order.

- [ ] **Step 4: Implement verifier**

Require exact file set, manifest syntax, hashes, protocol schema/provenance/counts, exact role partition, recomputed split ranks/order, recomputed SCRAMBLED descriptor from TRAIN row identities, and unevaluated autopsy status.

- [ ] **Step 5: Implement isolated CLI**

The CLI imports only `v2_g2_protocol`. Add a source-inspection test asserting `v2_g2_protocol.py` and `v2_g2_cli.py` contain no import of `.fit`/`.evaluate` and no call to `run_census`.

- [ ] **Step 6: Verify GREEN**

Run focused tests and full suite.

---

### Task 5: Freeze implementation and execute G2 constitution once

**Files:**
- Create: `.github/workflows/v2-g2-ci.yml`
- Create: `.github/workflows/v2-g2-official-freeze.yml`
- Generated by official workflow: `experiments/v2/protocol/*`
- Generated by official workflow: `experiments/v2/G2_RECORD.md`

**Interfaces:**
- Branch CI proves the code/tests are green without writing protocol custody.
- Official freeze workflow verifies the exact implementation SHA and G1 provenance, constructs protocol once into a clean path, verifies it without regeneration, scans outputs for forbidden fields/values, and fossilizes the result on `freeze/v2-g2-protocol`.

- [ ] **Step 1: Add CI workflow**

On pushes to `impl/v2-g2-protocol-freeze` and the eventual implementation freeze branch, run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q
PYTHONDONTWRITEBYTECODE=1 python -m py_compile src/arc_mkii/v2_g2_protocol.py src/arc_mkii/v2_g2_cli.py
```

- [ ] **Step 2: Add official freeze workflow only after code review**

The workflow must run the full suite, check a clean tree, verify the G1 input hashes, construct `experiments/v2/protocol`, call the independent verifier, assert counts 256/64/116 and no forbidden G2 outputs, write `G2_RECORD.md`, and commit the generated protocol plus record to `freeze/v2-g2-protocol` with the implementation freeze as its parent.

- [ ] **Step 3: Create implementation freeze ref**

After CI is green, point `freeze/v2-g2-implementation` at the exact final implementation commit.

- [ ] **Step 4: Run official G2 freeze**

Execute the official workflow at the frozen implementation SHA. Do not fit or evaluate any arm.

- [ ] **Step 5: Verify fossil**

Confirm remotely that `freeze/v2-g2-protocol` is a direct child of the implementation freeze; read `PROTOCOL.json`, `SCRAMBLE.json`, `ROOT_AUTOPSY_CONTRACT.json`, `MANIFEST_SHA256.txt`, and `G2_RECORD.md`; verify the recorded hashes and terminal authorization boundary.

- [ ] **Step 6: STOP**

The only terminal scientific statement is `PROTOCOL_FROZEN`; G3 implementation freeze is authorized only. Do not enter G3 or G4 in this task.
