# Native GE-B3 spatial nodal moments and static force control

Base: `1c01755ea822a0d0ecf0c7286a59d3dc44e461f3`, tree
`c0b0a9ec75cbb8ae4923299f26114b7b38f14cd5`. Existing arch evidence and all
earlier requests remain immutable. This stage adds a missing applied-load
capability, not merely a new label for internally recovered moments.

## Work and derivative authority

Spatial multiplicative virtual rotation gives external work

    delta W_ext = lambda (f dot delta x + m dot delta theta).

Here f and m have fixed spatial axes; their spatial-component derivatives with
respect to the state are zero. A general constant spatial moment is not a
globally conservative SO(3) load. This distinction is consistent with
[Ritto-Correa and Camotim, Work-conjugacy between rotation-dependent moments
and finite rotations](https://www.sciencedirect.com/science/article/pii/S0020768303000787).
The indexed source text was consulted; direct full-text access returned 403.
No newly hash-bound PDF, independent authorship or formal source review is
claimed by this development record.

The native internal energy already supplies H_exp, its Hessian in a spatial
Exp increment chart. With internal spatial moment M_int:

    D M_int = H_exp - (1/2) skew(M_int)
    R = g_int - lambda f_ext
    D R = D g_int                  (fixed spatial external components).

The skew correction must therefore use the INTERNAL moment, not the net
residual moment M_int-lambda*m. Replacing it with the net moment introduces
an erroneous +(lambda/2)*skew(m). Tests explicitly measure that difference
and check independent residual directional derivatives at 1e-7. No frame
differentiation or constitutive/tolerance modification is used in the driver.

A closed orientation loop has nonzero work under the constant moment. This
test prevents inventing a potential such as -m dot Log(Q), asserting symmetry
of a nonconservative load problem, or treating the scalar internal potential
as an external energy merit. Conservative modal/buckling use of this new
development checkpoint fails closed pending its separate load authority.

## Native implementation and state safety

`SpatialNodalMoments` requires explicit, sorted, unique positive node IDs and
finite binary64 spatial components. No ambiguous material/follower axis is
inferred. Its descriptor and physical components enter the captured layout
and checkpoint authority. No-pattern capture remains byte-compatible with
the existing force-only path; a preserved six-macro checkpoint must replay
exactly without a new equilibrium solve.

Only optional moment loading is added to the private retained-fibre layout.
The internal beam potential, all geometric/SO(3) kinematics, physical fibre
constitutive law, section quadrature, recovery and original force/translation
drivers are unchanged. A separate private static driver uses the complete
spatial residual Jacobian, bounded frozen-Jacobian correction merit and the
existing half-remaining-chart step bound. No hidden internal condensation,
automatic retry, relaxed residual threshold or state commit inside a rejected
trial is permitted. Accepted histories and recovery are replayed through the
existing native transaction implementation.

The new programme ID is
`GE_BEAM3_SPATIAL_FORCE_AND_COUPLE_CONTROL_DEVELOPMENT_V1`.
Old checkpoints cannot be relabelled as this programme or vice versa. Changed
moment axes, magnitudes, section, programme or hash reject restart. The new
route remains private and unqualified, with no public dispatch or default.

## Rehearsal and bounded cycles

Initial mechanics/local smoke: 15 passed in 4.71 seconds. This includes pure
torsion through 1.2 radians, unloading/reversal, byte-identical split restart,
biaxial bending, large common-rotation covariance and the spatial derivative.
Additional parity lane: four passed in 9.55 seconds (30 deselected by its
explicit selection). It covers all six force/moment components with coupled
physical fibre plasticity, reactions, rollback, restart and original arch
checkpoint replay. Allocation/capture lane: 15 passed in 1.63 seconds. These
are separate inventories, not a combined test count or production gate.

After process-supervisor tests and source freeze, run the fixed 34-node lane
twice in fresh external directories under
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-moments-20260907-v1`.
Use the same candidate commit and pytest 9.0.3, existing runtime guard, one
numerical thread, complete 24-GiB Windows Job, 600-second wall and 120-second
inactivity bounds. The native context/driver also retains its 120-second
cooperative deadline. Active Normal-token worker-owned scheduling applies.
There is no global lock acquisition or modification of resource history.

The cycle requires 34 passed, zero failures/errors/skips and exactly six named
state/restart JSON artifacts. Check complete process-tree termination before
exclusive same-volume publication. Preserve stdout, stderr, XML, checkpoints
and timing externally. Require byte-identical canonical cycles and all six
state artifacts. Failure preserves diagnostics and causes no automatic retry.

This is bounded development reproducibility, not full independent engineering
qualification. Curved moment loading, general distributed/coupled loads,
wide-slenderness engineering, full nonlinear sections, dynamic/prestress/
buckling integration and objective beam-shell coupling remain to qualify.
Existing B2/B3, qualified Q4/S3, aliases, production defaults, package metadata,
dependencies, source evidence and historical qualification remain unchanged.
