# Reduced-integration research boundary for improved Q4 shells

## Decision

The production element on this branch remains the full `2 x 2` MITC4+/D
formulation. A reduced element, flag, alias, or compatibility stub is not
exposed. The current decision is **no-go for product activation** and **go only
for a later, dedicated research branch** after the full element has passed its
scientific and performance gates.

This is a formulation boundary, not a claim that reduced integration has no
value. One-point integration can remove three of four surface constitutive
updates, but it also removes stiffness rank. A valid sibling must restore the
missing physical fields, including the continuum `/D` drilling construction,
without a user coefficient, a legacy drilling penalty, or an empirical
hourglass scale.

## Primary evidence reviewed

- Cui, Peng, Ran, Zhang, and Li, “Derivation and implementation of one-point
  quadrature quadrilateral shell element with MITC4+ method (MITC4+R),”
  *Computers & Structures* 291 (2024) 107207,
  DOI `10.1016/j.compstruc.2023.107207`. This is the direct MITC4+R anchor. It
  uses one surface point plus a stabilization contribution and reports static
  and explicit-dynamic examples.
- Ko, Lee, and Bathe, “A new MITC4+ shell element,” *Computers & Structures*
  182 (2017) 404–418, DOI `10.1016/j.compstruc.2016.03.002`, and “The MITC4+
  shell element in geometric nonlinear analysis,” *Computers & Structures*
  185 (2017) 1–14, DOI `10.1016/j.compstruc.2017.01.015`. These define the
  assumed membrane field and its nonlinear use; they do not by themselves
  provide a one-point `/D` element.
- Ko, Zhang, and Bathe, “Continuum mechanics-based shell elements with six
  degrees of freedom at each node—the MITC4/D and MITC4+/D elements,”
  *Computers & Structures* 307 (2025) 107622,
  DOI `10.1016/j.compstruc.2024.107622`. This is the physical drilling anchor
  for the full element. It is not evidence that the MITC4+R stabilization and
  `/D` enrichment commute or preserve rank when simply combined.
- Gruttmann and Wagner, “A nonlinear 4-node shell element with one point
  quadrature and stabilization based on a Hu–Washizu variational formulation,”
  *Computational Mechanics* 76 (2025) 613–633,
  DOI `10.1007/s00466-025-02616-2`. This is a modern example in which
  stabilization follows from a mixed variational construction, is integrated
  analytically, and requires no problem-dependent input parameter. It is a
  different formulation, not a drop-in MITC4+R/D implementation.
- Belytschko and Leviathan, “Physical stabilization of the 4-node shell element
  with one point quadrature,” *Computer Methods in Applied Mechanics and
  Engineering* 113 (1994) 321–350. This is an important physical-stabilization
  precedent, but predates MITC4+ and the published `/D` construction.

No source from another solver was inspected or used.

## What MITC4+R establishes—and what it does not

MITC4+R establishes that an MITC4+-based degenerated shell can be evaluated at
one surface point when its lost modes are supplied by an accompanying
stabilization derivation. It motivates a potentially large saving when the
constitutive update dominates.

It does not establish the element required by this repository. ANYsolver's
target has 24 degrees of freedom and obtains drilling behavior from continuum
`/D` kinematics: fictitious midside geometry, a common drill direction, the
rotation decomposition, and drilling-driven displacement enrichment. The
reviewed MITC4+R evidence does not derive the first and second variations of a
combined one-point MITC4+R/D energy. Therefore adding the full-element `/D`
terms to an MITC4+R stiffness, or adding MITC4+R stabilization to the full
MITC4+/D residual, would be an unqualified hybrid.

## Missing derivation for MITC4+R/D

A dedicated branch must derive all of the following from one variationally
consistent discrete field:

1. The centre-point membrane, bending, and transverse-shear operators and the
   `/D` edge-enrichment operator on actual warped continuum geometry.
2. A decomposition of the full `2 x 2` energy into centre-point and omitted
   fields, proving which omitted terms are represented by physical
   stabilization.
3. The residual of every stabilization term and its exact linearization with
   respect to translations and finite nodal rotations.
4. The interaction between MITC4+ membrane tying, MITC4 shear tying, and the
   fictitious midside `/D` geometry. Duplicate or contradictory control of the
   same mode must be excluded.
5. Generalized `A/B/D/As` behavior, including nonsymmetric supplied `B`, without
   assuming an isotropic scalar shear or hourglass modulus.
6. J2 and Hill-48 updates with a stabilization tangent based on the current
   consistent material tangent. Using an old-step or secant modulus merely to
   stabilize the omitted field must be shown not to introduce path dependence.
7. Initial stress/prestrain, geometric stiffness, follower-load tangent, mass,
   recovery, state commit/reject, and restart from the same reduced fields.

Until those equations exist, no implementation flag belongs in the public API.

## Exact rank and invariance requirements

For a free, valid four-node shell with 24 degrees of freedom, the completed
linear elastic operator must have exactly six rigid modes and rank 18. The
one-point centre operator alone cannot supply that rank. The stabilization
subspace must:

- add every missing non-rigid mode and no rigid mode;
- be orthogonal to constant membrane, bending, and transverse-shear patch
  fields in the appropriate energy pairing;
- retain cyclic-numbering, rigid-translation, rigid-rotation, and material-axis
  invariance;
- remain positive semidefinite for stable elastic material data;
- preserve correct behavior for skewed, tapered, high-aspect, and warped
  elements; and
- retain the physical `/D` drilling response without a penalty coefficient.

Rank must be checked over distortion and thickness sweeps, not only on a unit
square. Passing a square-element eigenvalue check is insufficient evidence.

## Nonlinear and constitutive consistency

Reduced quadrature changes more than loop count. The full element owns four
surface history stations. Replacing those with one station changes the spatial
resolution of yielding and the serialized state contract. A future element
must either define a new persistent state layout or rigorously derive how
omitted-field stabilization consumes four-station history. It must never
silently reuse a legacy or full-element state with different meaning.

For hyperelastic and elastoplastic response, the stabilization force must be
work-conjugate to its field and the tangent must be the exact derivative of the
trial residual. Commit, reject, cutback, displacement-control, and arc-length
paths must produce the same accepted state regardless of rejected iterations.
Finite differences remain a test oracle only.

## Mass, modal, buckling, and post-buckling risks

A centre-sampled consistent mass is rank deficient. A future sibling must
derive a physical mass treatment for translations, rotary inertia, and `/D`
enrichment; blindly lumping mass can conceal spurious drilling/hourglass modes.
Qualification must cover total mass, centre of mass, inertia, free-free rank,
repeated modes, MAC, and the absence of artificial low frequencies.

Buckling and post-buckling are especially sensitive because stabilization can
shift weak eigenmodes or become load-path dependent. Required evidence includes
distorted plate and shell spectra, repeated-mode subspaces, preload scaling,
eigen/nonlinear trends, imperfect shells, the first limit point, and a
controlled descending branch. A stable static patch test does not qualify
buckling or post-buckling.

## Expected cost model

The full-element measurements must be partitioned before a reduced branch is
authorized. For a homogeneous batch, record

```text
T_full = T_fixed_full + 4 * (T_kin + T_constitutive + T_contraction) + T_scatter

T_reduced = T_fixed_reduced
          + 1 * (T_kin + T_constitutive + T_contraction)
          + T_physical_stabilization
          + T_scatter
```

The constitutive-only upper bound approaches four, but whole-solver speedup is

```text
speedup = T_full / T_reduced
```

and will be lower whenever reference updates, stabilization, sparse scatter,
factorization, recovery, or solver iterations dominate. For plasticity, count
actual constitutive calls and state bytes; for generalized linear sections,
the saved constitutive work may be too small to justify added complexity.

No completed full-element, paired 11-sample cost partition exists at the time
of this pre-implementation decision, and no PERF lease has been used for this
document. Accordingly, measured values and a numerical speedup are explicitly
**unavailable**, not zero and not passed. `scripts/benchmark_s4_improved.py`
records the required full-element inputs once lease-gated evidence exists.

## Architecture reservation

The full implementation should keep immutable reference kinematics,
quadrature data, constitutive packs, scatter maps, and recovery output layouts
separate. This permits a future sibling to reuse common geometry/director
primitives. It does not justify a `reduced=True` branch inside a hot kernel:
the stabilization, state, mass, KG, and recovery contracts differ enough to
require distinct homogeneous batches and an explicit formulation name.

## Go/no-go gates for a later branch

Research may proceed only after the full MITC4+/D element has completed its
qualification and produced a measured cost partition. Product activation then
requires all of the following:

- a reviewed MITC4+R/D variational derivation and exact tangent;
- rank 18 with exactly six rigid modes across the frozen distortion sweep;
- parameter-free physical stabilization and no legacy-theory fallback;
- four-station compatibility or a new explicit state/serialization contract;
- independent static, modal, mass, buckling, nonlinear, plasticity, recovery,
  and coupling qualification;
- scalar/compiled and full/direct-reduced scatter parity;
- paired 11-sample whole-solver evidence showing a useful advantage at matched
  accuracy; and
- an explicit formulation identifier, migration policy, and failure-closed
  dispatch.

Until all gates pass, the permanent recommendation is **no-go**.
