# ARC-MKII V2 G4 Execution Order Contract

**Status:** `FROZEN IN G3 / DORMANT / NOT EXECUTED`

This contract defines the only authorized ordering for the future result-bearing V2 G4 execution. Its existence does not authorize or perform G4.

## Trigger

The official G4 workflow may trigger only from an explicitly created future branch:

```text
run/v2-g4-official
```

That branch must point exactly to the already-fossilized `freeze/v2-g3-executable` commit. Creating/fossilizing G3 must not trigger G4 automatically.

## Ordering

```text
verify run/v2-g4-official == freeze/v2-g3-executable
verify freeze/v2-g3-executable parent == freeze/v2-g3-implementation
verify exact G3 implementation and frozen G2 protocol
verify no prior G4 start lock / primary record / autopsy record
        ↓
CREATE lock/v2-g4-started
        ↓
FIRST RESULT-BEARING OPERATION MAY BEGIN
        ↓
fit LEARN
fit SCRAMBLED
materialize FROZEN
serialize artifacts + fit receipts
        ↓
load serialized artifacts into fresh-host V2 evaluator
evaluate exact frozen EVAL families
perform frozen replay-equivalence condition
compute frozen ignition predicate
        ↓
write primary scientific result
verify no root-autopsy value exists
commit + push record/v2-g4-primary
        ↓
ONLY AFTER PRIMARY COMMIT IS DURABLE
compute C_tie_max
compute C_tie_learn
compute T_retention_learn
compute C_actual_learn
        ↓
commit + push record/v2-g4-autopsy as direct child of primary
```

## Exactly-once boundary

The start lock precedes the first fit because the learned `theta` is itself result-bearing information. If execution fails after this lock, the official workflow must not silently rerun from scratch. Recovery requires an explicit separately reasoned custody decision.

## Primary/autopsy separation

`record/v2-g4-primary` must contain the frozen PASS/FAIL scientific result before any real V2 root-autopsy diagnostic is computed. Root-autopsy values are downstream explanatory diagnostics only and have no effect on ignition, dataset membership, learner, features, coefficients, thresholds, or arena inclusion.

## Replay ceiling

The legacy `TRANSPLANT` result field remains mechanically compatible. Its scientific meaning is capped at:

```text
fresh-host serialized-artifact replay equivalence
```

It is not evidence for stronger cross-architecture portability.

## G3 prohibition

During G3:

```text
NO run/v2-g4-official branch
NO G4 start lock
NO V2 fit
NO frozen-EVAL execution
NO ignition
NO real root-autopsy values
```
