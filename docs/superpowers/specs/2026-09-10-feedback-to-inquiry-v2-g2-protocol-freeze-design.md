# ARC-MKII-V2 G2 Protocol Constitution / Freeze Design

**Status:** `POST_G1_DESIGN_FREEZE / NO_FIT / NO_EVAL / NO_V2_SCIENTIFIC_RESULT`

**Parent scientific record:** `record/v2-g1-census@1edf919be5a9810d8e670ed26c0174642b3e7756`

**G1 implementation freeze:** `9ba2e6e8ad448e72702ade6af23f4a1a25fbe932`

This document is a post-G1 amendment to the already frozen September 9 V2 six-query design. It does not rewrite that design or claim that the analytic objects below were preregistered before G1. G2 computes protocol structure but reveals no scientific outcome.

## 1. G2 authorization boundary

G1 recorded `G1_PASS` with 436 canonical families. G2 is authorized only to constitute and freeze the future V2 protocol. G2 may compute deterministic split ranks, TRAIN/EVAL membership, row identities required by the frozen SCRAMBLED construction, protocol constants, and hashes.

G2 must not compute or expose:

- fitted LEARN coefficients;
- fitted SCRAMBLED coefficients;
- EVAL behavior under any arm;
- ignition;
- `C_tie_max`;
- `C_tie_learn`;
- `T_retention_learn`;
- `C_actual_learn`.

The G2 implementation must not import `arc_mkii.fit` or `arc_mkii.evaluate`. No output file may contain a fitted `theta`, arm success count, EVAL repair result, or root-autopsy value.

## 2. Frozen G1 provenance input

The constructor consumes the committed G1 custody only. It must fail closed unless all of the following are true:

```text
G1_RECORD_ID = 1edf919be5a9810d8e670ed26c0174642b3e7756
G1_IMPLEMENTATION_FREEZE_ID_V2 = 9ba2e6e8ad448e72702ade6af23f4a1a25fbe932
G1_STATUS = G1_PASS
N_CANONICAL = 436
```

and the G1 payload hashes are exactly:

```text
d0959d5794f3d398cae226050f48c2e68b8032819991536b9aadbdc8683dcd54  CENSUS.json
213a5133208c1f4ca19edd500e9f68b40ef13ed47959fdc2921a4daf3e951057  FAMILIES.jsonl
```

The constructor must read `experiments/v2/g1-census/FAMILIES.jsonl`; it must not regenerate or traverse the frozen `2^20` counter universe.

Each family record must have exactly the existing G1 fields:

```text
canonical_bytes_hex
family_id
first_counter
queries
```

with six distinct normalized query masks and a unique 64-hex-character family ID.

## 3. Deterministic split

For every one of the 436 retained families compute:

```text
split_rank = SHA256(
  b"arc-mkii-v2-six-query-gladiator-split\0" + family_id.encode("ascii")
)
```

Sort by `(split_rank, family_id)`.

Freeze roles exactly:

```text
rank   0..255  -> TRAIN
rank 256..319  -> EVAL
rank 320..435  -> OUTSIDE_CONFIRMATORY_V2
```

Use the first admitted ordered presentation already retained in the G1 family record. No discretionary exclusions or substitutions are permitted.

## 4. G2 protocol payloads

The exact machine payload set is:

```text
PROTOCOL.json
TRAIN_ARENAS.jsonl
EVAL_ARENAS.jsonl
OUTSIDE_CONFIRMATORY.jsonl
SPLIT_RANKS.jsonl
SCRAMBLE.json
ROOT_AUTOPSY_CONTRACT.json
MANIFEST_SHA256.txt
```

`MANIFEST_SHA256.txt` hashes the other seven payloads and nothing else. The verifier requires the exact file set and recomputes every SHA-256.

`PROTOCOL.json` uses schema `arc-reactor-mkii-v2-protocol/v0` and records at least:

- G1 record ID and implementation freeze ID;
- the two frozen G1 custody hashes;
- V2 fresh seed;
- query count 6;
- fault count 8;
- budgets `[2,3]`;
- feature count 8;
- ridge lambda `1/100`;
- TRAIN count 256;
- EVAL count 64;
- outside-confirmatory count 116;
- canonical family count 436;
- split-prefix literal;
- SCRAMBLED schema and interpretation ceiling;
- replay/transplant interpretation ceiling;
- root-autopsy status `POST_G1_PRE_G4_UNEVALUATED_NONACCEPTANCE`.

Every arena JSONL record contains exactly:

```text
rank
role
split_rank
family_id
canonical_bytes_hex
first_counter
queries
```

`SPLIT_RANKS.jsonl` contains all 436 records in rank order. The three role-specific JSONL files are exact partitions of that ordered set.

## 5. Frozen SCRAMBLED constitution

G2 preserves the V0 corruption construction exactly on the V2 TRAIN row population:

- strata are `(budget, decision_depth)`;
- rows within each stratum are ordered by the frozen V0 row ID;
- offset is the existing V0 function of `(budget, depth, stratum_size)`;
- `SCRAMBLE.json` remains schema `arc-reactor-mkii-scramble/v0`;
- interpretation remains only `prospectively fixed matched corrupted-feedback control with preserved within-stratum feedback marginals`.

G2 needs row identities, not fitted coefficients. The row-identity constructor must reproduce the V0 row-ID serialization exactly while allowing six query masks and six public query IDs. For each TRAIN arena, each budget in `{2,3}`, each fault `0..7`, and every ordered sequence of distinct query IDs of length `budget`, execute the fixed sequence until singleton or budget exhaustion. For each actually executed state/action row, construct the V0 row-ID payload with:

```text
canonical_task_id
query_masks
budget
fault
planned_sequence
decision_depth
candidate_mask
remaining_query_ids
action_query_id
features
terminal_repair
```

Feedback is intentionally excluded from the row ID exactly as in V0. G2 may compute terminal repair because it is part of row identity; it must not write training feedback labels or fit them.

The G2 row-ID implementation must have a regression test proving byte-identical row IDs to the existing V0 `TrainingRow.row_id` on four-query fixtures before being trusted for the six-query population.

`SCRAMBLE.json` records for each stratum exactly:

```text
budget
decision_depth
size
offset
row_ids_sha256
```

No learned coefficient or permuted feedback vector is materialized at G2.

## 6. Post-G1 analytic objects

G2 freezes, but does not evaluate, three post-G1 objects in separate human-readable records:

1. `ROOT-CONDITIONAL-TO-FULL-EXTENSION-V0` — post-G1 derived theorem, no G1 result-data dependency.
2. `ROOT-SUCCESS-FACTORIZATION-V0` — post-G1 derived analytic identity, no learned values observed.
3. `ROOT-AUTOPSY-CONTRACT-V0` — post-G1 / pre-G4 diagnostic freeze, values unevaluated, nonacceptance only.

The machine-readable `ROOT_AUTOPSY_CONTRACT.json` freezes only diagnostic definitions and algorithm metadata. It contains no evaluated diagnostic value.

## 7. Root-autopsy exact algorithm contract

For each frozen EVAL arena, after G4 is opened, define `T_a` as the immediate-information tied roots, `O_a` as the continuation-optimal subset, `z=(w,r)`, and the frozen minimum-public-ID tie rule.

`C_tie_max` is evaluated exactly over the finite homogeneous line arrangement induced by pairwise `d = z_i-z_j` inside `T_a`:

1. construct all pairwise `d`;
2. discard `d=0`;
3. deduplicate coincident homogeneous lines;
4. evaluate one exact rational witness for every open sector, both oriented rays of every line, and `beta=0`;
5. use exact `Fraction` arithmetic and the actual minimum-public-ID tie rule.

Freeze definitions of:

```text
C_tie_max
C_tie_learn
T_retention_learn
C_actual_learn
```

All are nonacceptance diagnostics. G2 must not evaluate them.

## 8. Analytic scope and claim ceilings

The root-extension theorem is stated on its minimal structural domain, not merely by reference to the whole V2 admission rule. It assumes:

- eight root candidates;
- `T` is the set of 4/4 useful root queries;
- every useful root query outside `T` has balance at most `3/8`;
- `0 <= w,r <= 1/2`;
- the first six frozen feature coordinates are equal among queries in `T`;
- root selection uses exact linear scores and the frozen public-ID tie rule.

The theorem does not depend on the G1 family count, split, seed, planner-gap threshold, or feature-representability result.

The historical executable field/name `TRANSPLANT` is not changed in V2. Its scientific interpretation ceiling remains `fresh-host serialized-artifact replay equivalence`. Stronger portability requires a separate prospective experiment.

## 9. G1 multiplicity custody omission

The September 9 design prospectively requested exact family multiplicities as a structural-diversity diagnostic. The contemporaneous G1 fossil retains the aggregate `984` admitted presentations, 436 first-admitted canonical family records, and no per-family alias count.

This omission does not affect the G1 acceptance decision `436 >= 320`. G2 records the omission without reconstructing multiplicities. Any later deterministic reconstruction must be labeled:

```text
RETROSPECTIVE_DETERMINISTIC_RECONSTRUCTION
NOT_G1_EXECUTION_CUSTODY
NOT_USED_FOR_G1_ACCEPTANCE
NOT_USED_TO_CHANGE_V2
```

## 10. Fail-closed verification

The G2 verifier must reject:

- wrong or missing payload files;
- wrong G1 provenance IDs or hashes;
- malformed/duplicate family IDs;
- role counts other than 256/64/116;
- noncontiguous ranks 0..435;
- split-rank mismatch;
- any overlap or omission across role manifests;
- a `SPLIT_RANKS.jsonl` order inconsistent with `(split_rank,family_id)`;
- malformed SCRAMBLED strata or a descriptor inconsistent with recomputed TRAIN row identities;
- wrong root-autopsy schema/status;
- any payload hash mismatch.

The constructor is idempotent only for a byte-identical existing protocol directory. If an existing directory differs, it fails rather than overwriting it.

## 11. G2 terminal state

A successful G2 freeze may claim only:

```text
V2 G2 PROTOCOL CONSTITUTION: PASS
TRAIN families: 256
EVAL families: 64
outside confirmatory run: 116
protocol hashes: VERIFIED
scramble constitution: FROZEN
root autopsy definitions: FROZEN / UNEVALUATED
NO LEARN FIT
NO SCRAMBLED FIT
NO EVAL EXECUTION
NO ROOT-AUTOPSY VALUES
NO SCIENTIFIC RESULT
G3 IMPLEMENTATION FREEZE AUTHORIZED ONLY
```

Then STOP.
