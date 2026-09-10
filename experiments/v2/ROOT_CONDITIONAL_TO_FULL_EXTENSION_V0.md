# ROOT-CONDITIONAL-TO-FULL-EXTENSION-V0

**Status:** `POST-G1 DERIVED THEOREM / NO G1 RESULT-DATA DEPENDENCY`

This result is analytic. It is derived from the already frozen root feature/rule definitions and does not use the G1 census values, G1 family identities, future TRAIN/EVAL membership, fitted coefficients, or evaluation outcomes.

## Minimal domain

Consider any root satisfying all of the following:

1. the hidden-state candidate set has size eight;
2. `T` is the set of useful root queries achieving a `4/4` split, hence `b(q)=1/2` for `q in T`;
3. every useful `q not in T` has `b(q) <= 3/8`;
4. the two frozen future-resolution features satisfy `0 <= w(q), r(q) <= 1/2`;
5. among queries in `T`, the first six frozen feature coordinates are identical;
6. the selector uses exact linear scores and resolves equal maximum scores by minimum public query ID.

For `beta=(beta_1,beta_2) in Q^2`, define the conditional tied-root choice

```math
q^T(beta)=min argmax_{q in T} beta^T (w(q),r(q)).
```

Define

```math
M_beta = 4 ||beta||_1 + 1
```

and the full eight-parameter scorer

```math
theta_beta=(0,0,0,M_beta,0,0,beta_1,beta_2).
```

## Proposition

For every root in the minimal domain and every rational `beta`,

```math
q(theta_beta)=q^T(beta).
```

## Proof

Let `q_T=q^T(beta)` and let `q not in T` be any useful root query. The frozen root geometry gives

```math
b(q_T)-b(q) >= 1/8.
```

Since each coordinate of `z=(w,r)` lies in `[0,1/2]`,

```math
|beta^T(z(q_T)-z(q))| <= ||beta||_1/2.
```

Therefore

```math
s_{theta_beta}(q_T)-s_{theta_beta}(q)
>= M_beta/8 - ||beta||_1/2
= 1/8 > 0.
```

Thus no useful query outside `T` can tie or outrank `q_T` under `theta_beta`.

Inside `T`, the immediate-balance term and the other first-six coordinates are equal across actions, so the full scorer's relative ordering is exactly `beta^T z(q)`. The selector uses the same minimum-public-ID tie rule as the conditional definition. Hence the unrestricted selector chooses exactly `q^T(beta)`.

## Capacity consequence on a finite evaluation set

For any finite frozen EVAL set define:

```math
C_actual(theta)=sum_a 1[q_a(theta) in O_a]
```

and

```math
C_tie(beta)=sum_a 1[q_a^T(beta) in O_a].
```

Any successful unrestricted full scorer, restricted to its own `beta=(theta_7,theta_8)`, cannot do better at a root in `O_a subseteq T_a` than the conditional scorer induced by that beta. Conversely the explicit extension above realizes every conditional beta policy as an unrestricted full root policy. Therefore:

```math
max_{theta in Q^8} C_actual(theta)
=
max_{beta in Q^2} C_tie(beta).
```

This closes unrestricted root-level scorer expressivity relative to conditional tied-root expressivity. It does not characterize whole-trajectory policy realizability or learning.

## Tightness ceiling

The explicit witness `4||beta||_1+1` is sufficient. More generally any `M>4||beta||_1` is sufficient under the displayed coarse bounds. This record does not claim that the coefficient `4` is the smallest universal constant permitted by the complete frozen query geometry.
