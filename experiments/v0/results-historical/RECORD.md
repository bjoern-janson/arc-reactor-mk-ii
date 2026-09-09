# ARC-MKII V0 — Historical Ignition Run Bundle Record

**Status:** `HISTORICAL_LOCAL_RUN_RECOVERED_POST_EXECUTION / IGNITION_FAIL / NO_POST_RESULT_TUNING_CLAIM`

**Canonical remote implementation freeze:** `c9897ae02829aeed31cccdaef662de4c715b312e`

## Provenance warning

This record was committed after the V0 execution from the preserved conversation run bundle `arc-mkii-v0-ignition-2026-09-09.zip`. It is **not** a contemporaneous execution fossil and must not be represented as one.

The preserved run record states that the execution checkout had the same frozen scientific subtrees as the canonical remote freeze:

- `src/arc_mkii`: `29487e962e3030ecdc7859d29bfbfbc1fd3bd2f2`
- `tests`: `1cf28a570ff2a1a7122026f69dd38953f2b4d605`
- `experiments/v0/protocol`: `ad1ce29c3c21fedef593c79bf826076e0b235776`

It also records 39/39 pre-run tests passing and the four frozen protocol payload hashes matching before execution.

The historical execution checkout commit recorded in the bundle is `a625013dfd6b1184c8f55b0861dc2eb540c3ec93`; that local commit is not treated as a remote authority object here.

## Frozen protocol

- 8 hidden faults
- 4 binary queries per menu
- budgets 2 and 3
- 256 TRAIN menus
- 64 held-out EVAL menus
- 8-coefficient selector
- exact ridge lambda `1/100`
- LEARN / SCRAMBLED / FROZEN controls

Frozen protocol payload hashes recorded by all three fit receipts:

```text
03689adbb578594c700ea5c07e5a897b56cff464a2bbbca0ea6df9689fd9e411  EVAL_MENUS.jsonl
47a13a4eebe57b53ec52f0198b796aabebe67562ab7fa472a5082392628dc58f  PROTOCOL.json
98d74ac4e4fdc94747d8f32dc5a827d23db09d4884e5521d7969332cfadee152  SCRAMBLE.json
9fcd6dc6f6379ad9b28b88b9a8880250ea95b8ab30cf83bf72df2758e299a2a7  TRAIN_MENUS.jsonl
```

## Result

`IGNITION_PASS = false`

| Budget | LEARN | SCRAMBLED | FROZEN | Exact planner |
| --- | ---: | ---: | ---: | ---: |
| 2 | 256 | 256 | 255 | 256 |
| 3 | 394 | 385 | 399 | 401 |

The frozen acceptance rule therefore fails: LEARN does not strictly beat both controls at either common budget while remaining no worse than both at the other budget.

The historical artifact replay check recorded `all_pass = true`. This should be interpreted as deterministic fresh-host replay of the same serialized `theta`, not as an independent cross-architecture transplant demonstration.

## Read-only paired analysis from the preserved run record

Against FROZEN:

- Budget 2: 4 case wins, 3 losses, 505 ties; 32/512 query traces changed.
- Budget 3: 2 wins, 7 losses, 503 ties; 234/512 query traces changed.

Against SCRAMBLED:

- Budget 2: 36 wins, 36 losses, 440 ties.
- Budget 3: 16 wins, 7 losses, 489 ties.

The exact planner leaves only one correct case of headroom above FROZEN at budget 2 and two at budget 3.

## Known limitations discovered after the run

1. The historical fit/evaluate entry points did not themselves fail closed by recomputing all protocol hashes before execution. The preserved run record says the hashes were checked pre-run, but the software enforcement gap is real and is repaired separately in the V2 preflight-hardening branch.
2. The historical `public_truth_table_bit_inspections` counters undercount selector usefulness-filter work. Resource totals in this bundle therefore remain historical measurements and must not be used as corrected cost measurements.
3. SCRAMBLED is a prospectively fixed matched corrupted-feedback control with preserved within-stratum label marginals. Its deterministic row ordering is not a pristine label-blind conditional-independence null.
4. The replay check historically named `TRANSPLANT` is a deterministic fresh-host artifact replay check, not a stronger independent transplant experiment.

None of these post-hoc clarifications changes the recorded V0 PASS/FAIL decision or repair-success counts.

## Claim ceiling

This historical bundle supports only:

> In the frozen V0 finite apparatus, informative feedback changed the serialized selector and beat the specified scrambled-feedback control at budget 3, but it did not beat the competent FROZEN baseline overall and therefore failed the preregistered ignition criterion.

It does not establish a reusable feedback-to-better-inquiry core, general active learning, corrigibility, safe forgetting, neural transfer, or general self-improvement.

## Bundle identity

Preserved ZIP SHA-256:

```text
5dd3f848661c05a07a9c92c6240d5a9b10413f99080383caa8d05b5207e85201
```

See `BUNDLE_SHA256.txt` for hashes of every file in the preserved archive. Large case-trace JSONL files are represented by their hashes rather than duplicated into GitHub in this recovery record.
