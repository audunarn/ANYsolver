# Complete-member affine BL5 candidate — 3 October 2026

**Decision:** retain the distinct affine-density pairing as the next development
candidate. Constant P0 density's transfer-resolution limitation is materially
reduced in the independent beam reference, and the actual flexible native mixed
system passes its bounded nominal kernel/inertia/parity checks. This does not
select a qualified multiplier policy, change defaults or close M2/F03.

Candidate source `7d24f90679ea834da64056e76df2828ea7399d92`; subsequent reuse of
the existing mechanical oracle is source `0f902f88` (script-only change).
The unchanged installed wheel binds all 417 module bytes before both runs.

## Declared pairing and executed checks

`ExperimentalBL5Line(basis="discontinuous_p1")` preserves the continuous
five-channel law. On each support all channels use physical `[1, xi]` density,
`xi=2*(x-left)/width-1`. Supports contain complete native member pairs; physical
endpoints, not index averaging, define the affine coordinate. The uniform
development rule is `span=2*ceil(max(1,halfcell_count/shell_segments))` with exact
coverage. No partial support or individual channel tuning is inferred.

The source checks include independent rational quintic-displacement BVP controls
for the new continuous Timoshenko reference, actual nonuniform support work,
both displacement moments, signs, equivalent units and ownership. Bounded 2:1
and 1:2 native cases check supported rows, full KKT work and restart. Actual-update
nonzero-multiplier curvature passes the existing `1e-6` criterion. Accepted finite
stepping, physical station-density reconstruction, exact checkpoint restore and
continued stepping pass. Seven-ratio construction is not seven-ratio stability.

**104 installed checks pass in 49.28 s**, including legacy line assembly,
aggregation and finite paths. Supervised route 51.403 s, sampled peak
213,827,584 bytes. Wheel SHA256:
`ef96a35e7d24912500d42422be59171b0f4e9f5830157e0088d226960ce5a06b`.
Actual solver imports come from the isolated site; ANYmaterial remains the
recorded editable dependency. Python3.14/NumPy2.4.6/SciPy1.17.1/Numba0.65.1,
effective numerical pools1/JIT off;600s/1GiB limits pass. This is not G6 graph or
platform acceptance. No performance saving is claimed from these timings.

## Transfer discriminator: distinguish the partitions

Same one-metre uncoupled section, EI_z=1.75e6 Nm², kGA_y=646153846.1538463 N,
normal-spin tip moment10Nm, endpoint uy restraints/free root normal spin.
Independent continuous beam references use the **same** 8/16/32 physical
supports. The strong-restraint reference is analytic. This is normal-spin
bending, not Saint-Venant torsion or a flexible-shell reference.

| Supports | Width / sqrt(EI/kGA) | P0 versus strong: force moments0–3 | Affine versus strong: force moments0–3 |
|---:|---:|---:|---:|
|8|2.40192|−24.119…−28.027%|−5.287…−6.151%|
|16|1.20096|−8.678…−10.096%|−1.077…−1.253%|
|32|.60048|−2.577…−2.999%|−.180…−.209%|

One existing native16x4/32-halfcell rigid-carrier fixture has **eight affine
supports**. Its moments agree with that same-affine reference by+.744…+.848%,
but differ from continuous restraint by−4.583…−5.355%. These are not the
32-support reference result. Native/reference work and weak-equilibrium controls
pass; small gaps do not erase the remaining physical transfer discrepancy.
The screen completed in3.301s, sampled185,933,824B. No finer native grid was run.

Third force-moment recovery uses analytic affine integration, after validating
coefficient mapping against actual physical station actions. Production two-point
quadrature remains unchanged; it integrates the linear constraint work and the
first three force moments, but not `x^3*Fy` for affine Fy.

## Actual flexible mixed-system discriminator

Reuse the existing supported16x4/32-halfcell mechanical oracle; only replace P0
rows by80 affine rows. All native nodal/cell rotations are retained. Independently
verify negative18-resultant local blocks, their stationary lift and work maps;
bounded dense QR/eigenanalysis is an oracle, never a production reduction.

- Supported physical order769; full native free order1057;80 constraint rows.
- Smallest norm-scaled constraint singular value .122313 exceeds rank budget
  `2.09449e-11`; no row is discarded.
- Smallest physical-kernel eigenvalue `1.75362e-5` exceeds nominal uncertainty
  `3.10896e-11`. All modes are retained.
- Reduced saddle inertia769positive/80negative/0unresolved. With288 independently
  checked negative resultant directions, **implied** native inertia is
  769positive/368negative/0unresolved. This is not a direct full-native spectrum
  or an SPD interpretation of its mixed tangent.
- Stationary work pullback relative difference `2.52668e-18`; constraint parity0.
- Fy/Mx/Mz reconstructed/native shell, nodal, retained, resultant, multiplier and
  support parity all≤`1.875e-12`; equilibrium/work/gap and one-factor reuse pass.

The check completed in4.822s, sampled217,866,240B. Triangle-completion error is
recorded as uncertainty; the actual tangent is neither averaged nor repaired.
Binary64 uncertainty accounting remains **nominal**, not certified coercivity,
uniform stability, locking or physical accuracy acceptance.

## Failures, review, evidence and next action

First source run:2failed/41passed. A nonuniform quadratic member violated native
regularity; the checkpoint test expected different error wording. Next run:
1failed/5passed because the replacement non-midpoint geometry violated declared
reference correspondence. The fixture now uses actual member midpoints with
unequal complete-member lengths; that control passes. No admission guard changed.
Failed snapshots/logs are retained. Initial wheel build lacked cache-directory
write access; an isolated no-cache build succeeded. Its failed installation
attempt is also retained.

Independent Read review found the third-moment quadrature defect before screen
execution. Its quartic counterexample and exact recovery repair pass. Review's
finite accepted-state density/restart control was added and passed. Development
reviews and their scope are in [review](review.md).

[Initial raw manifest](raw-v1.json) retains installed artifacts, source/check
bindings, failed fixtures, reference/screen data and commands.
[Mixed-system raw manifest](raw-v2.json) adds the unchanged-fixture oracle,
all saved modes, numerical results and resources; raw-v1 remains unchanged.
Explicit safe whitelists include no historical canary, F03 runner or history sweep.

Next scientific action is matched flexible-shell physical transfer and locking/
resolution assessment for this complete pairing, reusing the actual saved
reference geometry/actions at their valid scope. No fourth rigid-carrier grid,
isolated coarsening or auxiliary norm sweep follows automatically. The new space
needs its own justified norm and full ratio/refinement/physical acceptance.
Strong-transfer failures, external evidence and other mandatory rows stay open.
Formal F03 is UNCONSUMED; criteria/resources/pressure/publication authority and
the full Revision8 goal are unchanged. All owned numerical jobs are TERMINAL.
