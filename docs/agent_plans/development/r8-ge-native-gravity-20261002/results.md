# Experimental native GE gravity delivery — 2 October 2026

The public `GEBodyLoad(model_identity, acceleration_m_s2)` now runs through the
existing reference-linear and finite point-owner APIs. Constant spatial gravity
uses explicit shell density/thickness and physically admitted native section
inertia, never stiffness-derived mass. Native curved reference lifts and offset
mass centres contribute retained-cell rotation work and its actual-update
Jacobian. No global mass assembly or static condensation is needed for this load.

Compiled immutable load data is reused for unchanged linear requests and finite
continuation. Linear factors remain reusable for the unchanged virgin operator;
nonlinear solves use their actual tangents. Recovery distinguishes reference
linear and current finite wrenches and returns conservative external work.
The new bounded BODY envelope binds model, acceleration, numerical policy and
inner checkpoint without altering legacy schemas. Restore publishes atomically.

Finite Q4 gravity requires the explicit objective algorithmic pullback. Elastic
S3 body execution uses the existing stable-translation arithmetic and native
stable-history checkpoint, bound to this new load identity. Historical defaults
and existing nodal/staged paths are unchanged. New line/footprint attachment
loads remain explicitly unsupported in this slice.

## Executed evidence

Source kernel/context controls: 21 passed. Final isolated installed campaign:
**37 passed, zero failed/skipped** in pytest66.56s; complete supervised route
68.940s, sampled peak tree187084800B. Covers analytical mass/force, actual-left
rotation derivatives, same-quadrature line-work and kinetic oracles, curved and
eccentric mass, ownership and invalid inertia, assembled eccentric load/Jacobian,
Q4/mixed/all-S3 solves, physical balance, linear factor reuse, typed model/load
binding, fixed/adaptive cancellation/rejection/exception, chart reset, checkpoint
restore/continuation, generalized/shell-J2 history serialization and eight
existing staged-load lifecycle regressions. Material-history tests do not by
themselves establish a new simultaneous-plasticity or fibre-gravity qualification.

Installed public example `examples/stiffened_shell_ge_gravity.py`: two Q4 shells,
two native elements, explicit off-axis physical mass, three accepted factors
0.25/0.5/1, prefix restore and identical final checkpoint. Completed in20.970s,
peak156786688B. Total mass1256kg; force(0,0,-12321.36)N; equilibrium
3.22052e-10, compatibility4.06576e-20. This is a runnable engineering development
example, not an independent external comparison.

New wheel SHA256:
`4a287d5596f0aab7c16056e47932730ce95aba9971317dd198158ba754b72b06`.
393 Python modules are bound source/wheel/site. Test216 and example215 actual
ANYsolver imports are exclusively onsite. Windows/Python3.14.2, effective one
numerical thread, JIT disabled; exact dependencies/runtime in raw records.
Each job had600s/1GiB bounds. No competing owned numerical job was launched.

## Failed development runs and interpretation

- owner-v1: tuple-negation error in the new test assertion, repaired.
- owner-v2: historical Q4 finite force map failed physical moment balance at
  unchanged tolerance. The objective pullback passes; finite gravity now rejects
  the historical map in both solve and restore. No legacy equation was changed.
- owner-v4: elastic mixed/all-S3 trials exhausted backtracking on the inherited
  arithmetic path. Reusing existing stable translation plus its bound checkpoint
  passed the unchanged cases. This is a controlled arithmetic-path observation,
  not a proof allocating every conditioning cause or a new formulation claim.
- installed-v1 build could not write pip's cache. The no-cache build succeeded;
  no numerical test was claimed from the failed build.

These logs are retained. Final candidate source and test copies, manifests,
wheel, commands, complete outputs and runtime records are in [raw-v1.zip](raw-v1.zip),
with [member hashes](raw-v1.json). Archive SHA256
`02b88d823ecc57e2ba774b9c4b960abbf758a31b618627c9d666f25f8635daef`.
53 members; sensitive-value scan found zero matches. This does not remediate the
historical archive or lift its dissemination restriction.

## Acceptance boundary and next action

Independent implementation/mechanics review is recorded in [review.md](review.md).
This is implemented and focused-installed-tested experimental M4/G4A behavior;
G0/G4 and all aggregate gates remain open. No performance improvement is claimed.
Consumer native-project gravity persistence, full material/attachment envelope,
curved coupled engineering/external references, combined/staged body loads,
practical scale and Windows/Linux release verification remain required.

Next usable slice: expose the same immutable gravity descriptor and checkpoint
through the ANYfem native Project consumer, with one installed round-trip;
then advance the next required load/material envelope. Keep the unresolved native
connection/transfer decisions visible without repeating completed refinements.
No contact-worker coordination, formal F03 consumption, main merge, push,
publication, default change or version change occurred.
