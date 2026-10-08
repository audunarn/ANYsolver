# F06 loaded native B3 beam-chart transport, development v1

26 September 2026. F06 remains in progress. The registered v3 diagnostic
checked shell chart descriptions, and v4 issued and restored a loaded S3
shell-anchor rebase. Neither transported the native B3 beam chart. The
retained B3 mechanical state currently owns physical nodal/cell rotation
matrices and resultants; it has no accepted beam chart-anchor field or beam
rebase transaction. A production ownership claim is therefore premature.

**Decision question:** On one already accepted curved S3/native generalized
B3 loaded prefix, can the same nontrivial B3 nodal and retained-cell poses
be represented in reference-anchored additive charts and re-anchored zero
charts without changing physical beam response, section/material state,
joint pose gap, support force/moment reactions or the accepted prefix?
Competing causes for disagreement are incorrect Exp/Log reconstruction,
pose-port chart pullback, retained-state reinterpretation, or changed
equilibrium assembly. A passing comparison permits a subsequent explicit
beam chart-owner design; a failure identifies the affected component before
that design proceeds.

Use only the existing v4 curved S3 fixture's two-step accepted prefix, with
no shell rebase or successor solve. Preserve its checkpoint bytes and complete
accepted descriptor. Represent each physical beam nodal/cell frame using
`Q=Exp(theta) anchor`, first with reference anchors and then with physical
frames as anchors and zero coordinates. Feed the reconstructed matrices,
unchanged positions/low parts/resultants and unchanged accepted histories to
the private retained owner for loaded response. Compare physical frames,
section high/low strain/resultants, pose constraints/spatial wrenches, loaded
residual and fixed-support force/moment reactions. Check chart-covector
virtual work with a spatial rotation variation at the eccentric pose port.
Require a nonzero loaded beam rotation, multiplier and reaction; retain
per-field absolute and relative differences with explicit units. For this
development screen a field passes when its same-unit absolute difference
is within the stated floor or its relative difference is at most `1e-8`.
The floors are `1e-9` for length, rotation, force and moment and `1e-12`
for strain/curvature; mixed solver rows are reported separately. Use one
bounded development run, one BLAS thread, Python bytecode disabled and
`NUMBA_DISABLE_JIT=1` for the observed local import stall.

The bounded result can establish only beam chart-description feasibility at
one accepted state. It cannot issue a beam-rebased accepted state, transport
an accepted continuation or checkpoint through a changed beam chart, prove
large noncommuting paths, or accept F06/G0B. Those require a new owner-held
beam anchor and atomic state/history/restart contract. Frozen F06 v3/v4
evidence and formal F03 authority remain untouched.

## Run disposition

Five source-bound attempts were retained in
`../reference_cases/b3_e4_g0_f06_beam_chart_dev_v1{a,b,c,d,e}_{manifest,result}.json`.
All used the same curved S3/native B3 loaded two-step fixture and the
non-JIT single-thread environment. The attempts have distinct source hashes:

- `v1a` stopped at a fixture selection error: the fixed support is on the
  shell side, so no fixed beam reaction rows exist. The next source revision
  selected the actual fixed nodal force and moment rows.
- `v1b` stopped after the physical comparisons at an output-only cell-angle
  indexing error (`axis 2` on a two-dimensional chart-coordinate array).
- `v1c` reached the numerical predicate. The largest raw difference was the
  rotational pose gap, `2.77645e-17 rad`. It failed a provisional normalized
  `1e-8` threshold against a `1e-9 rad` floor, implicitly demanding less
  than `1e-17 rad` near zero. The physical comparison did not reveal a
  mechanics discrepancy. The next source revision made the declared
  same-unit absolute-or-relative development predicate explicit; the `v1c`
  failure remains preserved.
- `v1d` passed that predicate with the unchanged physical fixture. Its
  source manifest omitted the imported v3/v4 fixture hashes.
- `v1e` passed the same physical screen and records both fixture hashes;
  it also labels frame-angle comparison against a 1 rad normalization. This
  is the terminal development result. The raw v1e manifest/result SHA-256
  values are `9e0bffdc d34958d7 4991ab6f 15b85167 05488410 501e53d4 e3d63362 372700e6`
  and `d0911cd1 88924227 4541290b bfd621df 1d36708f fdfa721d 3e3e6099 f9b1df4f`
  (spaces group hex digits for reading).

The accepted prefix and checkpoint SHA-256 values in the terminal result are
`c6c0089bc587cfab855c963a7a0ebf5dce75522137d044b3f5460ed2829ecee0`
and `93663ba004343d4d507dcd1321a070117c62cdac0c4244afbb7ca84f8e2c2aec`;
both bytes remained unchanged. The reference-anchored beam nodal and cell
chart angles reached `0.00274808` and `0.00274013 rad`; their rebased
coordinates were zero. The multiplier norm was `5.00004e-4`, and fixed
support force and moment norms were `2.23607e-4` and `4.47757e-4` in the
fixture units. Chart virtual work matched at the recorded precision.
The largest mixed loaded-residual difference was `1.37771e-16` in its
solver-scaled rows. The near-zero rotational gap difference above is below
the declared `1e-9 rad` absolute limit; every other physical field also
passed its same-unit absolute or relative check. Recovered station histories
were bit-identical in this fixture, while the accepted history was never
promoted or replaced.

**Decision:** This supports one loaded beam chart-description transport at
an accepted prefix. It does not implement an owner-held beam rebase. The
smallest next contract dependency is an authenticated beam chart anchor and
coordinates in the accepted state, with an atomic transport event binding
physical nodal and retained-cell frames, origins/histories, reactions,
attachment pose gaps, cursor/generation, and direct snapshot restore.
An actual loaded continuation across that event and independent mechanics
review are still required for F06. G0B remains open and G1 barred.
