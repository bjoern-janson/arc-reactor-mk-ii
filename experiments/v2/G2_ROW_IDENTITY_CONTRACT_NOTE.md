# V2 G2 Row-Identity Execution Contract Note

**Status:** `POST-DESIGN / PRE-IMPLEMENTATION EXECUTION CLARIFICATION / NO RESULT INFORMATION USED`

The G2 design freezes the V0 row-ID serialization on the six-query TRAIN population. One field requires an explicit V2 binding before implementation because it affects deterministic row ordering and therefore the frozen SCRAMBLED descriptor:

```text
canonical_task_id = family_id
```

for every V2 TRAIN row.

Rationale: the G1 fossil's `family_id` is the frozen canonical structural task identity used to define TRAIN/EVAL freshness, while `queries` preserves the first-admitted operational presentation separately inside the row identity. This binding therefore keeps canonical identity and operational presentation distinct while preserving the V0 row-ID field structure.

This clarification is made after G1 but before G2 protocol construction, before any V2 fitting or evaluation, and before any root-autopsy value is computed. It does not change G1 membership, the G2 split rule, the learner, features, feedback rule, corruption rule, or acceptance criterion.
