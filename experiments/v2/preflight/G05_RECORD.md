# ARC-MKII-V2 G0.5 Preflight Record

**Status:** `VERIFIED / BEHAVIOR-PRESERVING / NO_V2_CENSUS / NO_TRAINING / NO_V2_RESULT`

## Compared executable states

- Frozen V0 scientific base: `c9897ae02829aeed31cccdaef662de4c715b312e`
- Hardening scientific source state: `f794a157213636c4a9e52540e667a3892d6a2e26`
- Semantic-equivalence gate implementation: `3b8ce5f0a62f46211633cee2e83133e176a9722b`

The gate itself verifies that `src/arc_mkii/` and `experiments/v0/protocol/` remain byte-diff-equivalent to the declared hardening scientific source commit before performing the semantic comparison. Later documentation, CI, or record commits therefore cannot silently change the compared executable state without failing the gate.

## Fresh CI verification

GitHub Actions run:

`https://github.com/bjoern-janson/arc-reactor-mk-ii/actions/runs/34408135412`

Environment recorded by the runner:

```text
Ubuntu 24.04.4 LTS
CPython 3.13.15
```

Full repository test suite:

```text
46 passed in 18.14s
```

G0.5 semantic-equivalence result:

```text
G0.5 SEMANTIC EQUIVALENCE: PASS
base=c9897ae02829aeed31cccdaef662de4c715b312e
hardened_source=f794a157213636c4a9e52540e667a3892d6a2e26
frozen_menus=320 (256 TRAIN + 64 EVAL)
training_rows=189177
semantic_vector_sha256=4aa007b39b060a954695b0d484a28723f9eb0c1949fc98e10c9c6c7ded4c20f0
eval_success={"FROZEN":{"2":255,"3":399},"LEARN":{"2":256,"3":394},"SCRAMBLED":{"2":256,"3":385}}
ignition_pass=false
```

## Semantic observable vector

The comparison reconstructs the complete frozen V0 TRAIN and EVAL memberships from the committed manifests and requires exact equality between the frozen V0 base and the hardened source for:

- exact TRAIN membership and ordered query masks;
- exact EVAL membership and ordered query masks;
- full policy-independent training-row count;
- exact fitted LEARN coefficients;
- exact fitted SCRAMBLED coefficients;
- exact FROZEN coefficients;
- deterministic SCRAMBLED assignment, represented by the canonical SHA-256 of every `(row_id, reassigned_feedback)` pair across the full training corpus;
- query scores at every evaluated decision state;
- chosen query at every evaluated decision state;
- observed answer bits;
- candidate-mask transitions;
- terminal repairs;
- per-case success;
- aggregate success at both budgets;
- original 64-menu EVAL success counts;
- ignition decision.

Behavior is evaluated for all 320 frozen menus, both budgets, and all eight hidden faults under LEARN, SCRAMBLED, and FROZEN.

Resource reports, wall-clock measurements, peak-memory measurements, and newly added custody metadata are deliberately excluded from the semantic equality object because the G0.5 hardening intentionally changes measurement accuracy and custody enforcement while requiring scientific behavior to remain fixed.

Thus the verified boundary is:

```math
\Delta\text{scientific observable vector}=0
```

while the intended permitted changes are:

```math
\Delta\text{custody enforcement}>0,
\qquad
\Delta\text{resource-accounting accuracy}>0.
```

## Historical-measurement boundary

This record does not rerun V0 as a new scientific experiment and does not replace the recovered historical V0 resource measurements. Historical resource numbers remain historical measurements produced by the instrumentation that existed at the time. Corrected resource accounting applies prospectively to future executions.

## Scientific authorization boundary

G0.5 verifies only that the preflight hardening preserves the frozen V0 scientific mechanism and observables while strengthening custody and measurement plumbing.

It does **not** authorize or report a V2 scientific result.

The next legal V2 action remains **G1 implementation/census only** under the already frozen fresh six-query design. No V2 fitting or evaluation is authorized by this record.
