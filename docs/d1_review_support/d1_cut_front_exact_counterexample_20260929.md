# Exact cut-front pressure-work counterexample — candidate scope

**29 September 2026. Analytic development result; no production-law change or
D1 acceptance claim.** This follows the independent pressure-space review's
smallest decisive question. It constructs a signed pressure direction whose
discrete work collapses faster than its work on an admissible continuous
motion as a target rim approaches a source node. The construction applies
to a fixed-target, flat Q1 source trace. The bridge to the actual coupled
E4-PL Q4/S3 route remains to be checked independently.

## Exact one-dimensional cut calculation

Take shape-regular source cells `[0,1]` and `[1,2]` in coordinate `y`.
The target covers `[0,1+θ]`, `0<θ≤1`. Let `q0,q1,q2` be the continuous
piecewise-linear hats at `y=0,1,2`. Use the same hats as the discrete
normal-displacement tests. All three pressure hats have positive clipped
support; `q2` has support `S2=θ²/2`.

Set

```
b(θ) = θ²/2 − θ³/3,
d(θ) = 1/4 + θ − θ² + θ³/3,
β(θ) = −b(θ)/d(θ),
α(θ) = −β(θ)/2,
pθ(y) = α q0(y) + β q1(y) + q2(y).
```

Here `d(θ)>0`. Exact integration over `[0,1+θ]` gives the clipped
mass/work matrix

```
         q0          q1                           q2
v0       1/3         1/6                          0
v1       1/6         1/3+θ−θ²+θ³/3                b(θ)
v2       0           b(θ)                         θ³/3.
```

Consequently `∫pθ v0=∫pθ v1=0` and
`∫pθ v2=θ³/3−b(θ)²/d(θ)=O(θ³)`. In the implementation's
force variables `z_i=S_i λ_i`, these are exactly the fixed-pose entries
of `zᵀ Dgbar`; positive support normalization does not erase the mode.
No positive-support mode has been deleted. The coefficients have both
signs, but a sufficiently small signed perturbation of a strictly positive
three-row baseline pressure remains inside the nonnegative active cone at
every fixed `θ>0`. This is an abstract all-active front, not the saved
16×8 front: its middle row has zero pressure and strictly positive
normalized gap. For that saved row pattern, `−pθ` is only a one-sided
tangent direction for the nonnegative-pressure cone if the outer rows are
strictly active. It is not in the fixed-pose KKT critical cone while the
middle row remains strictly open; a switching-front family would be needed
for that comparison.

On the full cell `[0,1]`, `pθ/θ² → q0−2q1 = 1−3y`. Choose the
smooth continuous motion

```
w(y) = y²(1−y)²  for 0≤y≤1;  w(y)=0  for 1≤y≤2.
```

Both `w` and its first derivative vanish at 0 and 1, so this is an
admissible H² witness on the patch. Exact integration gives

```
lim[θ→0+] θ⁻² ∫_0^(1+θ) pθ(y) w(y) dy
    = ∫_0^1 (1−3y)y²(1−y)² dy = −1/60.
```

Indeed the finite-`θ` continuous work is exactly `β(θ)/120`, because
the witness is zero on the cut cell and its integrals against `q0` and
`q1` are both `1/60`.

Thus the continuous work is bounded below by `c θ²` in any finite-energy
trace space containing this witness, whereas all Q1 test work is `O(θ³)`.
For a fixed coercive discrete stiffness and fixed positive witness energy,
the ratio of discrete to continuous energy-dual work is at most `C θ` and
tends to zero. This is an analytic cut-phase sequence at fixed shape-regular
mesh, not a mesh-refinement plot. It tests signed active directions; testing
each nonnegative hat separately would miss it.

## Tensor extension and limit of the inference

On a Cartesian Q1 patch, take the x-hat centered at `x=2`, supported on
`[1,3]` in a mesh with a prescribed edge at `x=0`. Its whole physical
support stays one length unit from that edge. Multiply `pθ` by this x-hat.
Tensor-product Q1 source work factors into an x mass entry and one of the
three y entries above, so every free source nodal normal-displacement work
entry is `O(θ³)`. A smooth x bubble supported within `[1,3]`, times `w(y)`,
is an admissible continuous witness with `O(θ²)` pressure work. This removes
the earlier prescribed-edge null as an explanation for this sequence.

At a flat, aligned physical shell skin, first-order normal work of a Q4
source translation has this tensor form. The construction is therefore a
specific warning for an unrestricted positive cut-front pressure profile.
It has **not** yet established that every admitted nonlinear shell pose has
this degeneracy: source director/rotation work, target freedom, boundary
constraints, and the actual E4-PL energy must be evaluated in the full
work map. A deformable, nonmatching S3 target can supply additional tests.
The analytic scalar result cannot by itself reject the entire D1 profile.
An independent read-only audit confirmed the exact one-dimensional algebra,
the H² witness and the tensor source-Q1 inference. It also identified the
saved-front cone distinction above and required a full nonmatching
two-body work and uniformly coercive energy check before a production
cut-uniform conclusion.

**Next decision:** independently check the exact algebra and the flat
source/target shell work map on one prospective family of cut poses. If
the same `O(θ³)` versus `O(θ²)` gap persists for the actual required
profile, unchanged fine Q1 pressure cannot receive a cut-uniform stability
claim. Then derive and qualify a changed pressure/displacement pairing.
If extra shell/target work arrests the collapse, state precisely which
boundary and target assumptions support the narrower admitted profile.
