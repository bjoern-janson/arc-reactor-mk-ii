# ROOT-AUTOPSY-CONTRACT-V0

**Status:** `POST-G1 / PRE-G4 DIAGNOSTIC FREEZE / VALUES UNEVALUATED / NONACCEPTANCE ONLY`

This contract freezes explanatory root diagnostics before V2 fitting and EVAL execution. None of these quantities may affect ignition, dataset membership, learner design, feature design, coefficients, refitting, thresholds, or arena exclusions.

## Definitions

For each frozen EVAL arena `a` at budget 3:

```math
T_a = {q : b(q)=1/2},
```

```math
O_a = argmax_{q in T_a} V_2(q),
```

and for each `q in T_a` define

```math
z_a(q)=(w_a(q),r_a(q)).
```

For `beta in Q^2`, define the conditional tied-root selector with the frozen public-ID tie rule:

```math
q_a^T(beta)=min argmax_{q in T_a} beta^T z_a(q).
```

Freeze the following quantities:

```math
C_tie_max = max_{beta in Q^2} sum_a 1[q_a^T(beta) in O_a],
```

```math
C_tie_learn = sum_a 1[q_a^T(beta_L) in O_a],
```

```math
T_retention_learn = sum_a 1[q_a(theta_L) in T_a],
```

```math
C_actual_learn = sum_a 1[q_a(theta_L) in O_a].
```

`C_tie_max-C_tie_learn` is a best-common-orientation count shortfall only. It is not a canonical set of missed arenas.

`C_tie_learn-C_actual_learn` is the off-manifold interference count.

`T_retention_learn-C_actual_learn` is the within-manifold ranking error count.

## Exact finite geometry for C_tie_max

The eventual post-result calculation must use exact rational arithmetic. It must not use floating point, an optimizer tolerance, an angular grid, or an arbitrary coefficient box.

For every frozen EVAL arena, construct all pairwise differences

```math
d=z_i-z_j
```

among queries in `T_a`. Then:

1. discard `d=0`, which represents a pair tied for every beta and therefore does not define a boundary line;
2. deduplicate coincident homogeneous lines `beta^T d=0`;
3. enumerate the resulting open angular sectors;
4. evaluate both oriented rays of every distinct boundary line;
5. evaluate `beta=0` separately;
6. use the actual minimum-public-ID tie rule at every evaluated regime.

All boundary coefficients are rational. A rational direction on a boundary with normal `(a,b)` is `(b,-a)`. Every nonempty open sector contains a rational witness. Hence this finite regime enumeration is complete for the ranking patterns available over `Q^2` and `R^2` under the frozen geometry.

## Relationship to root-extension theorem

`ROOT-CONDITIONAL-TO-FULL-EXTENSION-V0` proves that unrestricted eight-dimensional root-level oracle capacity equals `C_tie_max`. No second unrestricted eight-dimensional root oracle is required.

This does not establish whole-trajectory policy realizability, because later states are endogenous to earlier selector choices.

## Prohibitions

Before G4 is explicitly authorized, do not compute or record any value for:

```text
C_tie_max
C_tie_learn
T_retention_learn
C_actual_learn
```

Do not use this contract to change:

```text
ignition
TRAIN/EVAL membership
SCRAMBLED construction
learner or regularizer
feature schema
arena grammar
thresholds
repair rule
replay criterion
```

The contract exists only to make a later result easier to localize after the scientific outcome has been opened.
