# ARC-MKII-V1 GLADIATOR — Feedback-to-Inquiry Arena Design

**Status:** `DESIGN_ONLY / NO_IMPLEMENTATION / NO_CENSUS / NO_TRAINING / NO_SCIENTIFIC_RUN`

**Base implementation freeze:** `c9897ae02829aeed31cccdaef662de4c715b312e`

## Scientific question

> Under a fixed query-selection learner and matched primitive tools, can informative feedback teach a portable selector to prefer queries that preserve greater downstream diagnostic resolvability when immediate information gain is tied?

V1 is a chamber change, not a learner redesign.

The entire V0 learning mechanism remains frozen. V1 changes only the problem grammar so that the distinction of interest is actually present with nontrivial headroom:

```text
same immediate split quality
        !=
same future diagnostic value
```

The intended causal chain is:

```text
informative feedback
        ->
changed eight-coefficient selector
        ->
more continuation-optimal tied root queries
        ->
better bounded diagnosis
        ->
better repair on prospectively frozen fresh arenas
```

A V1 win is not evidence that learning to ask questions is novel. It is evidence that this fixed reusable selector can convert informative feedback into better future inquiry in a chamber where local information gain is intentionally insufficient.

---

## 1. Frozen from V0

V1 must not change the following scientific machinery after observing the V0 result:

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
- exact dynamic-programming planner reference;
- minimal artifact serialization;
- fresh-host evaluation;
- bidirectional selector-state transplant;
- raw resource-vector accounting;
- the V0 ignition acceptance rule.

The existing frozen eight features remain exactly:

1. `intercept`
2. `remaining_budget_over_3`
3. `candidate_count_over_8`
4. `smaller_child_fraction`
5. `child_fraction_product`
6. `singleton_child_candidate_fraction`
7. `weighted_best_next_split`
8. `worst_child_best_next_split`

No coefficient, feature, regularizer, corruption scheme, learner, repair rule, or acceptance threshold may be changed in response to V1 census or learned results.

### Allowed plumbing generalization

V1 increases the primitive query menu from four to five queries. Code that currently assumes `range(4)` or a four-query tuple may be generalized to the menu's declared query count. This is environment plumbing, not a new learner.

V1 must preserve the public presentation order of the five queries because the frozen selector uses public query ID for exact-score tie breaking. V0 behavior must remain behavior-compatible on the already frozen four-query manifests.

---

## 2. Finite apparatus

The hidden fault universe remains the eight states `0..7`.

A V1 arena contains exactly five distinct nonconstant binary queries over those eight states. Each primitive query costs one unit and returns its deterministic binary answer. Terminal repair has the same fixed charge in every arm.

Evaluation still enumerates both budgets and all eight hidden faults for every frozen arena.

The public selector interface remains conceptually:

```text
choose_query(theta, candidate_set, remaining_queries, remaining_budget)
    -> query_id or STOP
```

The selector never receives the hidden fault, correctness before terminal feedback, a privileged candidate pair, or evaluation labels.

---

## 3. Prospectively finite arena universe

A literal sweep over all `C(127,5) = 254,231,775` normalized five-query subsets is unnecessary for the V1 scientific claim and would violate the project's economy requirement.

Instead V1 defines a finite deterministic raw universe before any V1 learner is fit:

```text
RAW_COUNTERS = 2^20 = 1,048,576
SEED = "arc-reactor-mk-ii/v1-gladiator/menu-seed/2026-09-09"
```

For counter `c in [0, 2^20)` and public query slot `s in [0,5)`:

```text
payload = SEED || uint64_be(c) || uint8(s)
digest  = SHA256(payload)
mask    = 1 + (uint64_be(digest[0:8]) mod 127)
```

Masks `1..127` are the normalized representatives of the nonconstant answer-complement pairs. The five slot positions are the public query IDs `0..4` for that ordered raw arena.

A raw counter is grammar-valid iff its five masks are distinct.

The entire `2^20` counter window is the prospective V1 candidate universe. The census must process it exhaustively or stop without scientific interpretation.

This finite window was chosen during design, before V1 implementation or V1 learner outcomes. It is not changed if the observed census yield is inconvenient.

---

## 4. Ordered arena identity versus canonical freshness family

V1 deliberately separates two notions that V0 could safely collapse.

### Operational arena identity

Public query order is operational in V1 because FROZEN breaks exact score ties by the smallest public query ID. Therefore a permutation of query IDs can change FROZEN behavior even when the underlying five partitions are otherwise the same.

Arena admission is consequently evaluated on the **ordered raw presentation** produced by the deterministic counter stream. The presentation is not reordered to help or hurt FROZEN.

### Canonical family identity

After an ordered arena passes the structural Gladiator admission rule, compute a separate canonical **freshness-family ID** that ignores nuisance relabelings:

- permutation of the eight fault names;
- permutation of the five query names;
- complement of any individual binary answer convention.

Canonicalization extends the V0 row-signature construction from four to five columns: enumerate all `5!` column permutations and all `2^5` answer-complement patterns, construct the eight five-bit row signatures, sort the eight rows, and retain the lexicographically least eight-byte sequence.

The family ID is:

```text
SHA256("arc-mkii-v1-gladiator-family\0" || canonical_bytes)
```

This family ID is used conservatively to prevent structurally aliased arenas from crossing the train/evaluation boundary. It is **not** a claim that differently ordered presentations are behaviorally equivalent under FROZEN.

### First-admitted-family rule

Process raw counters in ascending order. Structural admission is evaluated first on the ordered presentation. Only admitted ordered arenas are canonicalized. For each canonical family ID, retain the **first admitted ordered presentation** encountered and discard later admitted aliases.

Thus:

```text
raw ordered arena
  -> structural admission
  -> canonical freshness family
  -> first admitted presentation per family
```

and never:

```text
all ordered aliases
  -> inspect LEARN/SCRAMBLED outcomes
  -> choose favorable presentation
```

No learned parameter or learned outcome participates in presentation retention.

This ordering is also an economy requirement: the expensive `5! * 2^5` canonical-family transform is paid only for the rare structurally admitted arenas, not for all 1,048,576 raw counters.

---

## 5. Gladiator admission rule

Arena admission uses only public query truth tables, the frozen feature map, the frozen FROZEN rule, and the exact planner. It may not inspect LEARN or SCRAMBLED parameters or outcomes.

At the root candidate set `S = Omega`, define immediate balance for each public query `q`:

```math
b(q)=\frac{\min(|S_0(q)|,|S_1(q)|)}{8}.
```

Let:

```math
b^*=\max_q b(q),
\qquad
T=\{q:b(q)=b^*\}.
```

An arena is eligible only if:

```math
b^*=\frac12
\qquad\text{and}\qquad
|T|\ge2.
```

So at least two root queries are tied at the maximum immediate `4/4` split.

Under `THETA0`, all members of `T` receive the same selector score because FROZEN weights only immediate split balance. Therefore its chosen root query is:

```math
q_F=\min T,
```

using the already frozen public-ID tie rule.

### Exact continuation value

For each tied root query `q in T`, define:

```math
V_2(q)
=
\sum_{a\in\{0,1\}}
V^*(S_a(q),Q\setminus\{q\},2),
```

where `V*` is the exact planner's maximum number of hidden faults that can be correctly repaired under the fixed terminal repair semantics with two primitive queries remaining.

Require genuine headroom above FROZEN:

```math
\max_{q\in T}V_2(q)-V_2(q_F)\ge2.
```

This guarantees at least two whole hidden-fault cases of planner-certified repair headroom among root queries that are indistinguishable to immediate split balance.

Let:

```math
T^*=\arg\max_{q\in T}V_2(q).
```

### Frozen-feature representability gate

V1 is not intended to fail merely because the frozen eight-feature selector cannot represent any distinction between the useful and harmful tied queries.

For each root query `q`, retain the already frozen features:

```math
w(q)=\texttt{weighted_best_next_split}(q),
```

```math
r(q)=\texttt{worst_child_best_next_split}(q).
```

Require that at least one continuation-optimal tied query `q* in T*` satisfies:

```math
r(q^*)>r(q_F)
```

or, if those values are equal,

```math
w(q^*)>w(q_F).
```

This gate uses no learned coefficient. It establishes only that the frozen feature interface exposes a prospective structural signal capable of distinguishing at least one better continuation route.

### Admission summary

Every admitted ordered arena therefore contains:

```text
multiple 4/4 root queries
        ->
FROZEN cannot distinguish them by its only nonzero weight
        ->
FROZEN's deterministic tied choice has >=2 repair cases of headroom
        ->
at least one better tied route preserves stronger downstream
resolvability visible through the already-frozen feature interface
```

This is the V1 fuel condition.

---

## 6. Census gate before learning

The census is a structural pre-experiment and must occur before any V1 training.

It records at least:

- `N_raw_counters = 1,048,576`;
- `N_grammar_valid`;
- `N_root_matched_tie`;
- `N_planner_gap`;
- `N_feature_representable_ordered`;
- `N_admitted_ordered`;
- `N_admitted_canonical_families`.

Canonical-family computation occurs only after structural admission. No fitted selector is loaded or computed during this census.

The hard gate is:

```math
N_{admitted\ canonical\ families}\ge320.
```

If fewer than 320 canonical families survive, V1 stops:

```text
ARENA_UNIVERSE_INSUFFICIENT -> STOP -> NO TRAINING -> NO V1 RESULT
```

The `2^20` window and the 320 threshold are not enlarged, relaxed, or resampled after seeing the census.

If at least 320 survive, the arena design passes only this construction gate. It is not evidence that LEARN will beat either control.

---

## 7. Prospective train/evaluation split

For every retained admitted canonical family, compute a split rank:

```text
SHA256("arc-mkii-v1-gladiator-split\0" || family_id)
```

Sort by this rank, with family ID as the deterministic secondary key.

Freeze the associated retained ordered presentation for:

- first 256 families as TRAIN;
- next 64 families as EVAL.

All remaining admitted families are outside the V1 scientific run. They may be retained for custody but cannot be promoted into V1 evaluation after results are known.

Train/evaluation inclusion therefore depends only on the prospectively declared structural grammar and cryptographic rank, never on repair outcomes from LEARN/SCRAMBLED or learned coefficients.

---

## 8. Training and controls

Training collection is the exact V0 policy-independent exhaustive corpus generalized from four to five available query IDs.

For each training arena, budget in `{2,3}`, fault in `0..7`, and every ordered sequence of distinct primitive queries of the permitted length, execute the fixed sequence until singleton or budget exhaustion. Terminal success is copied to every actually executed state/action row from that sequence.

LEARN fits the same exact ridge regression to the true feedback.

SCRAMBLED uses the same prospectively fixed corruption rule as V0: one deterministic permutation of the same feedback values within equal `(budget, decision_depth)` strata, retained by reconstructible descriptor and never redrawn.

FROZEN uses `THETA0` unchanged and consumes no training.

No V1 arm receives a query unavailable to another arm. All arms share the same public truth tables, budgets, feature schema, storage schema, repair rule, manifests, and evaluation cases.

---

## 9. Primary acceptance rule — unchanged from V0

V1 deliberately does not weaken the V0 ignition criterion.

Let exact repair success at budget `B` be `R_L(B)`, `R_S(B)`, and `R_F(B)` for LEARN, SCRAMBLED, and FROZEN.

Ignition requires both:

```math
\exists B\in\{2,3\}:\quad
R_L(B)>R_S(B)\ \land\ R_L(B)>R_F(B),
```

and:

```math
\forall B\in\{2,3\}:\quad
R_L(B)\ge R_S(B)\ \land\ R_L(B)\ge R_F(B).
```

The already frozen bidirectional selector-state transplant must also pass.

A gain at budget 3 with a loss at budget 2 is a tradeoff and fails ignition. A win only over SCRAMBLED is insufficient. A win only over FROZEN is insufficient.

V1 is designed so budget 3 is the main Gladiator battleground; budget 2 remains a real non-regression/control condition. This interpretation does not modify the mathematical acceptance rule.

---

## 10. Mechanism diagnostics — not acceptance criteria

The following are preregistered descriptive diagnostics.

### Root continuation-optimal choice rate

For each arm and budget-3 root decision:

```math
P(q_{chosen}\in T^*).
```

Report exact counts and fractions for LEARN, SCRAMBLED, and FROZEN.

### Root-route transfer

For cases where LEARN and FROZEN select different root queries, report whether LEARN moved from `q_F` into `T*`, away from `T*`, or between equally valued roots.

### Repair mediation table

Cross-tabulate:

```text
root choice changed?
continuation value improved?
final repair changed?
final repair became correct/incorrect?
```

These diagnostics help test the intended chain:

```text
feedback -> theta -> root inquiry -> continuation quality -> repair
```

but they do not independently authorize an ignition claim.

### Planner headroom

Report exact planner, FROZEN, SCRAMBLED, and LEARN repair success per budget, plus how much of the prospectively available FROZEN-to-planner headroom each arm captures.

Do not treat individual fault cases as independent statistical replications.

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

No hidden scalarization is introduced.

Ignition and useful power remain separate thresholds. V1 first asks whether informative feedback causally improves the reusable selector. Any amortized engineering-payback claim requires a separately declared future-task horizon and cost weights.

---

## 12. Prospective gates

### G0 — design freeze

Freeze this scientific design before V1 implementation.

### G1 — structural census

Implement only enough arena machinery to exhaust the fixed `2^20` raw counter universe and produce the census. No training is permitted.

If `N_admitted_canonical_families < 320`, stop.

### G2 — protocol freeze

If G1 passes, freeze the exact 256/64 manifests, family identities, retained ordered presentations, scramble descriptor, protocol constants, and file hashes before fitting.

### G3 — implementation validation

All V0 regression tests plus V1-specific tests must pass. V0 frozen manifests must retain V0 behavior under the query-count plumbing generalization.

Record an exact `IMPLEMENTATION_FREEZE_ID_V1` and stop.

### G4 — scientific run

Only after explicit authorization may the frozen V1 implementation fit LEARN and SCRAMBLED and inspect the 64-arena evaluation family.

No manifest redraw, coefficient tuning, feature change, grammar change, raw-window extension, or acceptance-rule change is permitted after G2.

---

## 13. Interpretation ladder

### If the census fails

Claim only that this prospective arena generator did not yield the required 320 canonical Gladiator families. Do not infer anything about feedback learning.

### If LEARN changes `theta` but does not improve root continuation choice

The frozen learner did not convert feedback into the intended query-selection distinction on this arena family.

### If LEARN improves continuation-optimal root choice but not final repair

Better first inquiry was observed, but the improvement did not propagate to net repair under the fixed downstream policy and budget.

### If LEARN beats SCRAMBLED but not FROZEN

Informative feedback carried useful signal relative to the specified corruption control, but reusable improvement over the competent frozen heuristic was not established.

### If LEARN beats FROZEN but not SCRAMBLED

The learned artifact changed behavior beneficially, but the specified feedback relation was not isolated as the cause.

### If ignition passes

The allowed claim is narrow:

> On the prospectively frozen finite V1 Gladiator arena family, informative terminal feedback changed the same eight-coefficient portable selector so that an identical fresh host selected better future inquiries and achieved higher bounded repair than both the frozen greedy-balance baseline and the prospectively scrambled-feedback control, without regression at the other declared budget; the behavior and performance change followed the selector under bidirectional state transplant.

This does not establish general active learning, hidden-change detection, learned primitive sensing, safe forgetting, protected corrective-frontier expansion, transformer self-improvement, general intelligence, or compatibility with other research repositories.

---

## 14. Nonclaims and boundary discipline

V1 does not claim:

- invention of learning to ask questions;
- that balance is generally a bad heuristic;
- that the exact planner is unavailable in this toy domain;
- that five-query arenas model realistic software diagnosis;
- that root-route improvement implies general future counterfactual accessibility;
- that an available better query implies a learner can discover it outside this frozen feature interface;
- that success establishes safe self-modification or corrigibility;
- that V1 transfers to MATRIX, OpenCore, Revisics, transformers, or neural systems.

V1 exists to earn one thing cleanly:

```text
same primitive tools
+ same learner
+ informative feedback
        ->
a portable selector that asks better questions tomorrow
```

---

## 15. Design invariant

> **Do not make the gladiator stronger after seeing the fight. Make the arena contain the distinction before the gate opens.**

The V0 learner is the gladiator. V1 changes the arena, freezes it prospectively, and asks whether feedback teaches that unchanged gladiator to choose the route that preserves future resolvability.
