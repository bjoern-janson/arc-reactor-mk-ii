# ARC-MKII-V2 SIX-QUERY GLADIATOR — Feedback-to-Inquiry Arena Design

**Status:** `DESIGN_ONLY / NO_IMPLEMENTATION / NO_CENSUS / NO_TRAINING / NO_SCIENTIFIC_RUN`

**Scientific learner base:** `c9897ae02829aeed31cccdaef662de4c715b312e`

**V1 reconstructed negative record:** `6428126d6531f1fea3aff891f222b57eb8979d96`

## Scientific question

> Under a fixed query-selection learner and matched primitive tools, can informative feedback teach a portable selector to prefer queries that preserve greater downstream diagnostic resolvability when immediate information gain is tied?

V2 is a **chamber-diversity repair**, not a learner redesign.

V0 showed that the competent FROZEN baseline had almost no available headroom on the original four-query random chamber. V1 introduced a matched-tie structural chamber where locally identical root splits could differ in downstream diagnostic value, but its frozen G1 census yielded only 40 canonical structural families, below the required 320.

A post-closure autopsy found that V1 repeatedly instantiated the same narrow mechanism: FROZEN selected a tied 4/4 root with continuation value 6 while another tied root preserved continuation value 8, and the frozen future-resolution features exposed the distinction. A separate sacrificial six-query exploration showed that adding one primitive query sharply reduced the collapse from operational presentations to canonical families. That exploratory stream is permanently ineligible for V2 scientific use.

V2 therefore changes exactly one scientific chamber parameter relative to the V1 chamber concept:

```text
five primitive queries -> six primitive queries
```

Everything that learns remains frozen at the V0 learner base.

### Executable-authority boundary

The reconstructed V1 negative record is research lineage, not executable authority. The original local V1 G1 implementation fossil is unavailable and must not be silently reconstructed as an implementation dependency.

V2 implementation must therefore descend scientifically from the sealed V0 learner at `c9897ae...` and add only the generic query-count/chamber/census plumbing required by this design. No fitted learner, feature, coefficient, training rule, or evaluation rule may be inherited from sacrificial probe code or from an unavailable V1 implementation.

---

## 1. Frozen scientific machinery

V2 must not change the following from the V0 learner design:

- the eight-feature selector schema;
- the eight serialized coefficients `theta`;
- `THETA0`, with weight `1` only on `smaller_child_fraction` and zero on the other seven features;
- exact rational feature arithmetic;
- exact ridge fitting with `lambda = 1/100` toward `THETA0`;
- LEARN, SCRAMBLED, and FROZEN arm meanings;
- policy-independent exhaustive training collection;
- terminal binary repair-success feedback;
- the fixed belief update;
- the fixed terminal repair rule;
- budgets `2` and `3`;
- exact planner reference;
- minimal selector artifact serialization;
- fresh-host evaluation;
- bidirectional selector-state transplant;
- raw resource-vector accounting;
- the V0 ignition acceptance rule;
- the V0 deterministic SCRAMBLED-feedback construction, including its stratum definition and offset rule.

The frozen eight features remain exactly:

1. `intercept`
2. `remaining_budget_over_3`
3. `candidate_count_over_8`
4. `smaller_child_fraction`
5. `child_fraction_product`
6. `singleton_child_candidate_fraction`
7. `weighted_best_next_split`
8. `worst_child_best_next_split`

No coefficient, feature, regularizer, corruption rule, learner, repair rule, budget, or acceptance threshold may be changed in response to V2 census or learned results.

---

## 2. Finite apparatus

The hidden fault universe remains exactly the eight states `0..7`.

A V2 arena contains exactly **six distinct nonconstant binary queries** over those eight states. Each query costs one unit and deterministically returns one bit. Terminal repair semantics remain unchanged.

The public selector interface remains conceptually:

```text
choose_query(theta, candidate_set, remaining_queries, remaining_budget)
    -> query_id or STOP
```

The selector never receives the hidden fault, correctness before terminal feedback, privileged planner values, arena-admission labels, canonical-family labels, or evaluation outcomes.

Public query order remains operational because the frozen selector breaks exact score ties by smallest public query ID.

---

## 3. Fresh confirmatory arena universe

The V2 scientific universe uses a new seed literal first introduced by this design and not used by the sacrificial six-query exploration:

```text
RAW_COUNTERS = 2^20 = 1,048,576
SEED = "arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001"
```

For each counter `c in [0, 2^20)` and public query slot `s in [0,6)`:

```text
payload = SEED || uint64_be(c) || uint8(s)
digest  = SHA256(payload)
mask    = 1 + (uint64_be(digest[0:8]) mod 127)
```

Masks `1..127` are the normalized representatives of the nonconstant answer-complement pairs over eight faults.

A raw arena is grammar-valid iff all six masks are distinct. Slot order `0..5` is retained exactly as the operational public query order.

The full `2^20` counter interval is frozen prospectively. It must not be expanded, reseeded, truncated, or redrawn after its census yield is known.

The sacrificial exploratory seed and all arenas inspected under it are permanently excluded from V2 TRAIN and EVAL.

---

## 4. Operational arena versus canonical freshness family

V2 preserves the V1 distinction between operational presentation and structural freshness family.

### Operational arena

Structural admission is evaluated on the ordered six-query presentation emitted by the fresh counter stream. Query order is not canonicalized before FROZEN chooses its root action.

### Canonical family

Only after an ordered arena passes structural admission, compute a separate family identity invariant under:

- permutation of the eight fault names;
- permutation of the six query names;
- complement of any individual binary answer convention.

The exact canonical object is the lexicographically least sorted eight-row six-bit signature representation over this equivalence class.

The family ID is:

```text
SHA256("arc-mkii-v2-six-query-gladiator-family\0" || canonical_bytes)
```

An implementation may use an optimized exact algorithm, but it must be proven behaviorally identical to the explicit quotient on test fixtures before the V2 census. Hash equality is identity bookkeeping, not evidence that the quotient is scientifically correct by itself.

### First-admitted-family rule

Process counters in ascending order. Structural admission occurs before canonicalization. For each family ID, retain the first admitted ordered presentation and discard later admitted aliases.

No LEARN or SCRAMBLED result may participate in retaining a presentation.

---

## 5. Gladiator admission rule — unchanged in substance

Admission uses only public truth tables, the frozen feature map, the frozen FROZEN rule, and exact planner continuation values.

At the root state `S = Omega`, define immediate balance:

```math
b(q)=\frac{\min(|S_0(q)|,|S_1(q)|)}{8}.
```

Let:

```math
b^*=\max_q b(q),
\qquad
T=\{q:b(q)=b^*\}.
```

Require:

```math
b^*=\frac12,
\qquad
|T|\ge2.
```

Thus at least two available root queries are tied at the maximum immediate 4/4 split.

Because `THETA0` weights only immediate balance, FROZEN chooses:

```math
q_F=\min T.
```

For each tied root `q`, define its exact two-query continuation value:

```math
V_2(q)
=
\sum_{a\in\{0,1\}}
V^*(S_a(q), Q\setminus\{q\}, 2),
```

where `V*` is the exact maximum number of hidden faults that can be correctly repaired with two primitive queries remaining under the fixed repair semantics.

Require:

```math
\max_{q\in T} V_2(q)-V_2(q_F)\ge2.
```

Let:

```math
T^*=\arg\max_{q\in T}V_2(q).
```

### Frozen-feature representability gate

For each tied root retain the already-frozen features:

```math
w(q)=\texttt{weighted_best_next_split}(q),
```

```math
r(q)=\texttt{worst_child_best_next_split}(q).
```

Require at least one `q* in T*` satisfying:

```math
r(q^*)>r(q_F)
```

or, if equal,

```math
w(q^*)>w(q_F).
```

This gate establishes only that the fixed feature interface exposes a structural distinction. It does not assert that the fitted learner will use it correctly.

---

## 6. G1 structural census gate

Before any V2 fitting, exhaust the full fresh `2^20` raw universe and record at least:

- `N_raw_counters`;
- `N_grammar_valid`;
- `N_root_matched_tie`;
- `N_planner_gap`;
- `N_feature_representable`;
- `N_admitted_presentations`;
- `N_admitted_canonical`.

No fitted selector may be loaded or computed during G1.

The hard gate remains:

```math
N_{admitted\ canonical}\ge320.
```

If fewer than 320 canonical families survive:

```text
ARENA_UNIVERSE_INSUFFICIENT -> STOP -> NO TRAINING -> NO V2 RESULT
```

The threshold, seed, counter interval, or admission grammar may not be relaxed after seeing the census.

If at least 320 survive, V2 earns only the right to freeze a protocol. It has not yet produced evidence for learned improvement.

---

## 7. Prospective TRAIN/EVAL split if and only if G1 passes

For every admitted canonical family compute:

```text
SHA256("arc-mkii-v2-six-query-gladiator-split\0" || family_id)
```

Sort by this rank, with family ID as the deterministic secondary key.

Freeze:

- first 256 families as TRAIN;
- next 64 families as EVAL.

Use the first admitted ordered presentation retained for each selected family.

All remaining admitted families are outside the confirmatory V2 scientific run and cannot be promoted after results are known.

---

## 8. Training and controls — unchanged learner

If G1 passes and the protocol is frozen, the V2 implementation starts from the four-query V0 learner and generalizes only query-count-dependent environment plumbing so that the same training algorithm can enumerate six public query IDs.

For each TRAIN arena, budget in `{2,3}`, hidden fault in `0..7`, and every ordered sequence of distinct queries of permitted length, execute the fixed sequence until singleton or budget exhaustion. Terminal repair success is assigned to each actually executed state/action row from that sequence exactly as in V0.

LEARN fits the same exact ridge regression to informative feedback.

SCRAMBLED uses the exact V0 corruption construction on the V2 row population: the same `(budget, decision_depth)` strata, deterministic row ordering, and deterministic offset rule. The resulting V2 scramble descriptor is frozen at G2 before fitting.

FROZEN uses `THETA0` unchanged and consumes no training.

All three arms share the same primitive truth tables, budgets, feature interface, repair rule, storage schema, TRAIN/EVAL manifests, and evaluation cases.

---

## 9. Primary ignition criterion — unchanged

Let exact repair success at budget `B` be `R_L(B)`, `R_S(B)`, and `R_F(B)`.

Ignition requires:

```math
\exists B\in\{2,3\}:\quad
R_L(B)>R_S(B)\land R_L(B)>R_F(B),
```

and simultaneously:

```math
\forall B\in\{2,3\}:\quad
R_L(B)\ge R_S(B)\land R_L(B)\ge R_F(B).
```

The already-declared bidirectional selector-state transplant must also pass.

A gain at one budget with a loss at the other is a tradeoff, not ignition. Beating only SCRAMBLED or only FROZEN is insufficient.

---

## 10. Prospectively declared mechanism diagnostics — not acceptance criteria

V2 reports, without using them to determine PASS/FAIL:

### Continuation-optimal root choice

For each arm at budget 3:

```math
P(q_{chosen}\in T^*).
```

### Root continuation value

Report the distribution and mean of:

```math
V_2(q_{chosen})-V_2(q_F)
```

for each arm.

### Frozen-feature movement

For root choices, report exact `(w,r)` values and whether LEARN moves from the FROZEN root to a tied root with strictly larger `r`, or equal `r` and larger `w`.

### Repair mediation

Cross-tabulate:

```text
root query changed?
continuation value improved?
final repair changed?
final repair became correct/incorrect?
```

### Structural diversity

Report the admitted-presentation to canonical-family ratio and exact family multiplicities. This is a chamber diagnostic, not evidence of learning.

These diagnostics are intended to make the hypothesized chain inspectable:

```text
feedback
 -> changed theta
 -> changed present query
 -> greater preserved downstream resolvability
 -> better repair
```

---

## 11. Resource accounting

Retain the V0 raw resource vector:

- artifact bytes;
- peak Python bytes;
- wall-clock nanoseconds;
- training rows consumed;
- feature vectors computed;
- public truth-table bit inspections;
- primitive query executions;
- terminal actions;
- planner states expanded.

Do not collapse this vector into a post-hoc weighted scalar.

---

## 12. Gates and custody

### G0 — design freeze

Freeze this document before V2 implementation.

### G1 — fresh six-query structural census

Implement only enough environment/census machinery to exhaust the fresh frozen universe and determine whether `N_admitted_canonical >= 320`.

No training at G1.

### G2 — protocol freeze

Only if G1 passes, freeze exact TRAIN/EVAL manifests, first-admitted operational presentations, canonical family IDs, split ranks, scramble descriptor, protocol constants, and file hashes.

### G3 — implementation freeze

All legacy V0 tests plus V2-specific tests must pass. Record an exact `IMPLEMENTATION_FREEZE_ID_V2` before fitting.

### G4 — scientific run

Only after explicit authorization may the frozen V2 implementation fit LEARN and SCRAMBLED and inspect the 64-family EVAL manifest.

After G2, no seed redraw, manifest substitution, feature change, learner change, grammar change, or acceptance-rule change is permitted.

---

## 13. Interpretation ladder and claim ceiling

If G1 fails, claim only that the fresh V2 six-query generator did not yield the required canonical diversity.

If G1 passes but LEARN does not beat both controls under the frozen criterion, claim a V2 negative or tradeoff result exactly as observed.

If V2 ignites, the maximum supported claim is:

> In this frozen finite six-query diagnostic apparatus, informative terminal feedback changed a portable eight-parameter query selector such that, on structurally fresh held-out arenas with tied immediate information gain, it selected questions that preserved more useful downstream diagnostic structure and achieved more correct repairs than both its frozen initial policy and a matched scrambled-feedback control, without losing at the other tested budget.

V2 does **not** establish general active learning, general intelligence, unknown-change detection, safe forgetting, protected corrective-frontier expansion, human corrigibility, neural transfer, or general self-improvement.

---

## 14. Design rationale

The sixth query is not justified merely as "more data." V1 showed that five-query Gladiator arenas repeatedly collapsed into a small number of structural families despite many operational presentations. The sacrificial six-query probe indicated that one additional primitive query substantially increases the number of genuinely distinct diagnostic-route geometries while preserving the same local-vs-future distinction and the same frozen learner interface.

The V2 chamber therefore tests a sharper object:

```text
Can feedback teach a system to choose a present distinction partly by the future distinctions that choice leaves operationally available?
```

The chamber is intentionally minimal: one additional query, nothing else.
