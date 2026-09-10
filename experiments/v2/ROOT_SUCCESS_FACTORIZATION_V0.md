# ROOT-SUCCESS-FACTORIZATION-V0

**Status:** `POST-G1 DERIVED ANALYTIC IDENTITY / NO LEARNED VALUES OBSERVED`

This identity is frozen before V2 fitting or evaluation. It defines how a later learned root result can be decomposed without changing the V2 acceptance criterion.

For frozen EVAL arena `a`, let:

```math
T_a = immediate-information-optimal 4/4 tied roots,
```

```math
O_a = argmax_{q in T_a} V_2(q),
```

and let `theta_L` be the future fitted LEARN vector with `beta_L=(theta_{L,7},theta_{L,8})`.

Define:

```math
R_a(theta_L)=1[q_a(theta_L) in T_a],
```

```math
G_a(beta_L)=1[q_a^T(beta_L) in O_a],
```

```math
A_a(theta_L)=1[q_a(theta_L) in O_a].
```

Because `O_a subseteq T_a`, `R_a=0` implies `A_a=0`.

If `R_a=1`, the full selector's chosen action lies in `T_a`. Within `T_a`, the first six frozen feature coordinates are identical, so the full scorer and the conditional scorer induced by `beta_L` have exactly the same action ordering and the same minimum-public-ID tie rule. Hence `A_a=G_a` whenever `R_a=1`.

Therefore, pointwise:

```math
A_a = R_a G_a.
```

Summing over frozen EVAL arenas:

```math
C_actual(theta_L)=sum_a R_a G_a.
```

The following later diagnostic differences therefore have exact meanings:

```math
C_tie(beta_L)-C_actual(theta_L)
= sum_a G_a(1-R_a),
```

which counts arenas where the learned future-resolution orientation would choose a planner-optimal tied root but the full learned scorer exits `T_a`; and

```math
T_retention(theta_L)-C_actual(theta_L)
= sum_a R_a(1-G_a),
```

which counts arenas where the full learned scorer remains in `T_a` but its conditional future-resolution orientation chooses the wrong tied member.

The quantity

```math
C_tie_max-C_tie(beta_L)
```

is only a best-achievable conditional-orientation **count shortfall**. Because multiple maximizing ranking cells may attain the same cardinality on different arena subsets, it must not be interpreted as a canonical set of missed arenas.

This record contains no learned coefficient and no evaluated diagnostic value.
