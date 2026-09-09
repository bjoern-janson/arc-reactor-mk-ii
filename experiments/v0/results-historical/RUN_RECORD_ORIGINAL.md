# Arc Reactor Mk II — V0 Ignition Run Record

Date: 2026-09-09

## Custody

Canonical remote implementation freeze:
`c9897ae02829aeed31cccdaef662de4c715b312e`

Execution checkout commit:
`a625013dfd6b1184c8f55b0861dc2eb540c3ec93`

The execution checkout has the same frozen scientific subtrees as the canonical remote freeze:

- `src/arc_mkii`: `29487e962e3030ecdc7859d29bfbfbc1fd3bd2f2`
- `tests`: `1cf28a570ff2a1a7122026f69dd38953f2b4d605`
- `experiments/v0/protocol`: `ad1ce29c3c21fedef593c79bf826076e0b235776`

Pre-run verification: 39/39 tests passed; all four frozen manifest SHA-256 checks passed.

## Frozen protocol

- 8 faults
- 4 binary queries per menu
- budgets 2 and 3
- 256 training menus
- 64 held-out evaluation menus
- 8-coefficient selector
- ridge lambda = 1/100
- LEARN / SCRAMBLED / FROZEN controls

## Result

`IGNITION_PASS = false`

| Budget | LEARN | SCRAMBLED | FROZEN | Exact planner |
| --- | ---: | ---: | ---: | ---: |
| 2 | 256 | 256 | 255 | 256 |
| 3 | 394 | 385 | 399 | 401 |

Bidirectional selector-state transplant check: PASS.

The frozen acceptance rule therefore fails: LEARN does not strictly beat both controls at either common budget while remaining no worse than both at the other budget.

## Read-only paired analysis

Against FROZEN:

- Budget 2: 4 case wins, 3 losses, 505 ties; 32/512 query traces changed.
- Budget 3: 2 case wins, 7 losses, 503 ties; 234/512 query traces changed.

Against SCRAMBLED:

- Budget 2: 36 wins, 36 losses, 440 ties.
- Budget 3: 16 wins, 7 losses, 489 ties.

The exact planner shows that FROZEN already occupies almost all available headroom: it is only 1 correct case below planner at budget 2 and 2 below planner at budget 3. LEARN captures the sole budget-2 headroom menu and one budget-3 headroom menu, but introduces more regressions elsewhere.

## Claim ceiling

V0 does **not** establish ignition or a reusable feedback-to-better-inquiry core under the preregistered acceptance rule.

It does establish that the serialized learned selector changes future query behavior in the frozen apparatus, and informative feedback outperforms the specified scrambled-feedback control at budget 3, but the learned selector does not outperform the competent FROZEN baseline overall.

No post-result tuning, redraw, or evaluation-family modification occurred in this run.
