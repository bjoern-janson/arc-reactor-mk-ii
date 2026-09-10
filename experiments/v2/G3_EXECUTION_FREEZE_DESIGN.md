# ARC-MKII V2 G3 Execution Freeze Design

**Status:** `POST-G2 DESIGN / NO_FIT / NO_EVAL / NO_V2_SCIENTIFIC_RESULT`

## Frozen base

```text
V2_G2_RECORD_ID
= 5689645287c41a71e109f1b022529e8b98f2006d

G2_PROTOCOL_MANIFEST_SHA256
= 419b7be408a5a37ab6a7ee304ac58646683a6fc4771b503e0b0f475002b4d075
```

G3 exists only to make the already-frozen V2 experiment executable without producing any V2 learned or evaluated result.

## Scientific-delta rule

Prefer byte-identical reuse of the already-frozen scientific primitives. G3 must not alter the meaning of the experiment frozen by G2.

Preferred unchanged primitives:

- `src/arc_mkii/features.py`
- `src/arc_mkii/selector.py`
- `src/arc_mkii/fit.py`
- `src/arc_mkii/artifact.py`
- host transition semantics
- core within-stratum SCRAMBLED permutation semantics
- ignition predicate

V2-specific executable adapters may be added for protocol loading, six-query training rows, V2 evaluation identity, result serialization, post-result root autopsy, and G4 orchestration.

## TRAIN corpus gate

The only admissible V2 TRAIN source is the frozen G2 `TRAIN_ARENAS.jsonl` payload.

The V2 six-query row constructor must use:

```text
canonical_task_id = family_id
query_masks = the frozen first-admitted ordered six-query presentation
budgets = 2,3
faults = 0..7
planned sequences = ordered permutations of six public query IDs at the frozen budget
terminal feedback = int(terminal_repair == fault)
row-id serialization = the G2-frozen V0-compatible row identity contract
```

The complete TRAIN row population must contain exactly 817,105 rows and reproduce all five G2-frozen strata exactly:

```text
(budget=2, decision_depth=0):  61,440
(budget=2, decision_depth=1):  60,805
(budget=3, decision_depth=0): 245,760
(budget=3, decision_depth=1): 243,220
(budget=3, decision_depth=2): 205,880
```

Each stratum must reproduce the exact `row_ids_sha256` and offset frozen in `experiments/v2/protocol/SCRAMBLE.json`.

A corpus failing any frozen size, offset, or row-ID-list hash is inadmissible for fitting.

## LEARN

Future G4 LEARN fitting must consume exact terminal feedback from the admissible V2 TRAIN rows and reuse:

```text
exact Fraction arithmetic
p = 8 features
lambda = 1/100
THETA0 unchanged
fit_theta semantics unchanged
```

G3 may verify compatibility of the generic fitter on synthetic or already-public fixtures. G3 must not call `fit_theta` on the frozen V2 TRAIN corpus.

## SCRAMBLED

Future G4 SCRAMBLED fitting must use the exact same admissible V2 TRAIN row population, sorted by `row_id` inside `(budget, decision_depth)`, with the exact G2-frozen offsets. Only the feedback field is permuted. No alternate corruption construction is allowed.

G3 may verify the mapping logic against synthetic fixtures and frozen descriptor metadata. G3 must not fit the V2 SCRAMBLED arm.

## FROZEN

The FROZEN arm is exactly `THETA0` and performs no training.

## EVAL identity bridge

The only admissible V2 EVAL source is the frozen G2 `EVAL_ARENAS.jsonl` payload.

For every future V2 case trace:

```text
CaseTrace.canonical_task_id = frozen EVAL family_id
```

The evaluator must use the frozen first-admitted ordered six-query presentation directly. It must not recanonicalize, regenerate, substitute, or reorder the arena.

G3 tests may exercise the V2 evaluator on synthetic six-query fixtures only. The official G3 verification path must not load the frozen 64 EVAL families into an evaluator.

## Replay / TRANSPLANT ceiling

The legacy executable/schema field may remain `TRANSPLANT` for compatibility.

Its scientific meaning remains capped at:

```text
fresh-host serialized-artifact replay equivalence
```

G3 must not strengthen this into an independent-host portability claim.

## Acceptance

The future primary result must use the already-frozen ignition predicate without modification.

Root-autopsy diagnostics are nonacceptance diagnostics and cannot alter ignition, dataset membership, the learner, features, coefficients, thresholds, or arena inclusion.

## Root autopsy

G3 may implement root-autopsy machinery, but:

- tests during G3 use synthetic fixtures only;
- actual V2 values remain inaccessible to the G3 verifier;
- `C_tie_max`, `C_tie_learn`, `T_retention_learn`, and `C_actual_learn` remain `UNEVALUATED` throughout G3;
- actual V2 autopsy computation is strictly downstream of an immutable primary-result fossil.

The frozen G2 `ROOT_AUTOPSY_CONTRACT.json` remains authoritative and byte-unchanged.

## Result-isolated architecture

Two execution surfaces must be separated:

```text
v2_g3_verify
  CAN:
    verify G2 manifest/custody
    load TRAIN identities
    construct all V2 TRAIN row identities
    compare all five frozen row strata sizes/offsets/hashes
    verify constants/schemas/source boundaries
    verify result-capable G4 code exists and compiles
    verify G4 workflow topology

  CANNOT:
    fit V2 LEARN
    fit V2 SCRAMBLED
    create learned V2 theta
    load frozen V2 EVAL into evaluation
    compute ignition
    evaluate real V2 root autopsy
```

```text
v2_g4_execute
  MAY EXIST IN G3 SOURCE BUT MUST NOT RUN IN G3.
```

The official G3 verification must leave no V2 result-bearing artifact.

## Future G4 execution order

G3 must freeze a future G4 workflow whose result-bearing ordering is:

```text
verify exact G3 implementation
verify exact G2 protocol + manifest
verify no previous G4 start lock/result
CREATE EXACTLY-ONCE G4 START LOCK
fit LEARN
fit SCRAMBLED
materialize FROZEN
serialize artifacts + receipts
evaluate frozen EVAL
perform frozen replay check
compute frozen ignition
FOSSILIZE PRIMARY SCIENTIFIC RESULT
ONLY AFTER PRIMARY RESULT IS DURABLE:
  compute root-autopsy diagnostics
  fossilize downstream nonacceptance autopsy record
```

The G4 exactly-once lock must precede the first V2 fit because learned theta is result-bearing information.

## G3 verification residue prohibition

A successful G3 verification must leave:

```text
NO learned theta artifact
NO SCRAMBLED theta artifact
NO fit receipt
NO EVAL trace
NO SUMMARY.json
NO TRANSPLANT/replay result
NO root-autopsy value
NO ignition value
```

## G3 success boundary

The only permitted positive conclusion is:

```text
V2 G3 EXECUTABLE IMPLEMENTATION: PASS
IMPLEMENTATION_FROZEN

NO LEARN FIT
NO SCRAMBLED FIT
NO EVAL EXECUTION
NO ROOT-AUTOPSY VALUES
NO IGNITION
NO V2 SCIENTIFIC RESULT

G4 RESULT-BEARING EXECUTION AUTHORIZED ONLY
```

## Lineage rule

The G3 design fossil is created from `5689645287c41a71e109f1b022529e8b98f2006d`.

After design review, executable implementation must start again from that same G2 protocol record, not from the design commit. The implementation must record the design fossil SHA as a non-ancestral design reference.
