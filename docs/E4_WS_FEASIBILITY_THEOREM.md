# E4-WS local-condensation feasibility theorem

## Result

The study `study_e4_ws.wg2020_local_weak_symmetry_feasibility_v1` receives

```text
NO_GO_E4_WS_LOCAL_CONDENSATION_AND_RANK
```

for the exact zero-energy local-multiplier identity frozen by E4-0. This is a
necessary algebraic result obtained before choosing a multiplier space. It is
not a claim that weak-symmetry elasticity methods are generally impossible.

## Frozen simultaneous requirements

The branch asks a nonzero element-local multiplier to enforce a drill
constraint while retaining all of the following:

1. 24 unconstrained external coordinates;
2. no multiplier compliance, penalty, stabilization, or other added energy;
3. no retained global saddle unknown;
4. exact element-local condensation of the multiplier; and
5. a finite positive-semidefinite condensed stiffness of rank 18.

With `m>0`, the frozen quadratic functional is

```text
Pi(q,lambda) = Pi0(q) + lambda^T C q,
```

where `q` has 24 entries, `lambda` has `m` entries, and `rank(C)>0` is needed
to act on at least one of the four core drill-null directions.

## Theorem

There is no exact local Schur condensation of `lambda` that produces a
finite 24-by-24 rank-18 PSD stiffness while all five frozen requirements are
retained.

### Proof

The linear stationarity system has the KKT form

```text
[ K0  C^T ] [q     ] = [f]
[ C    0  ] [lambda]   [0].
```

Static condensation of a local variable requires solving its stationarity
equation uniquely for that variable at fixed external coordinates. Here

```text
dPi/dlambda = C q = 0
```

contains no `lambda`. Equivalently, the multiplier diagonal block is the
zero `m x m` matrix and has no inverse. Hence a multiplier Schur complement
does not exist.

There are only four algebraic exits:

- Retain `lambda` in a saddle system. This violates the no-retained-mixed-
  unknown requirement.
- Parameterize `q=N qhat`, where `range(N)=ker(C)`. If `rank(C)=m_c>0`, the
  unconstrained external dimension becomes `24-m_c`, violating the fixed
  24-coordinate requirement.
- Add a nonsingular multiplier block, such as `-S`. Eliminating the multiplier
  then adds `C^T S^-1 C`; `S` is compliance or regularization and violates the
  zero-added-energy identity.
- Add a primal penalty or stabilization. This also violates the identity.

Taking `C=0` avoids the first three conflicts but cannot change the open-core
rank from 14 to 18. A pseudoinverse does not provide another exit: it either
leaves an arbitrary multiplier component, projects `q` into `ker(C)`, or
selects a finite regularization metric. Each is one of the alternatives above.

Therefore no formulation satisfying all five requirements exists. QED.

## Scope and weak-symmetry boundary

Public quadrilateral weak-symmetry elasticity theory uses globally coupled
`H(div)` stress fields together with discontinuous displacement/rotation
spaces and a stability argument. It is background evidence for a different
mixed architecture. It does not turn the zero block above into an invertible
local block and does not source a nodal-Q1 shell pair.

A larger local variational system could in principle couple the multiplier to
additional energetic or dual fields so that the combined internal block is
invertible. Such a functional is not `Pi0(q)+lambda^T Cq`; it changes the
frozen E4-WS identity and would require a separately named source and
stability program. Likewise, retaining a saddle multiplier or reducing the
external coordinates defines a different product interface.

Because the necessary theorem fails before any space selection, no WS
macroelement, inf-sup, numerical singular-value, or benchmark campaign is
run. The theorem does not alter the open-core GO and does not constrain the
independent E4-PL branch.

Production remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
