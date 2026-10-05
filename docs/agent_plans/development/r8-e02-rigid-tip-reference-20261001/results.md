# E02 rigid-tip physical comparison — development result

Decision: retain the GE reference-linear rigid-footprint candidate for the
restricted out-of-plane investigation. Stop at the planned third mesh level.
This executed comparison advances physical transfer evidence; E02, F04 and
aggregate acceptance remain open. No normal-spin or complete connection
equivalence is inferred.

## Physically declared comparison

Both models have a1m x.2m isotropic panel, thickness.02m, E210GPa, nu.3,
clamped at x=0. The full-width region x>=.8 is rigid. Native Q4 selects every
vertex of its complete patch cells and all six nodal channels. CalculiX2.23
C3D20R rigidifies every corresponding volume node, including midsides and
through-thickness nodes. REF/ROT nodes lie outside body/element membership.
The common port is(.9,0,+/-.05)m. Its three separate loads are Fz10N, Mx1Nm
and My1Nm. These are reference-linear loads, not finite equilibrium states.

The native GE member is an unloaded free stub attached at that port. It creates
no additional support or material load path. Actual native shell cross-block
inspection establishes membrane/drilling versus bending/shear decoupling;
normal spin is <=5.05e-20rad, direct patch Mz<=2.25e-14Nm, and stub work is
negligible. The corresponding physical directors are fixed by the solid rigid
patch's top/bottom motion. This makes the out-of-plane comparison defensible;
it does not prove general shell/solid or six-channel equivalence.

## Complete bounded batch

Positive port offset uses fixed10x4/20x8/40x16 Q4 grids and corresponding solid
in-plane grids, with two quadratic solid cells through thickness. Coarse
negative-offset runs check even out-of-plane compliance and odd port in-plane
translation. This is offset kinematics, not an eccentric force-to-moment test.

| Final-load work quantity | Native finest J | External finest J | Difference | Native last refinement | External last refinement |
|---|---:|---:|---:|---:|---:|
| Fz | 8.49387443e-4 | 8.481342e-4 | +0.147765% | +0.144016% | +0.143639% |
| Mx | 1.73385811e-5 | 1.744681e-5 | -0.620336% | +1.358324% | +0.148327% |
| My | 2.81079146e-5 | 2.807432e-5 | +0.119663% | +0.074192% | +0.107081% |

Final-load pairing is F dot u+M dot theta; linear-ramp work is half of it.
No asymptotic extrapolation or converged1% acceptance is claimed. In particular,
native torque's last refinement is still1.36%. Through-thickness resolution was
fixed and has not received its own convergence check. All recorded native root
wrench errors are <=6.90e-9 in the declared SI components; patch translation
gaps<=1.87e-20m. Reference rigid mapping falls within printed rounding bounds.
Printed coarse offset work agrees, with precision limits retained.

The pinned external executable SHA is
27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f.
Every final external run has an exact ASCII deck identity, zero exit status,
warning/error-free output, one completed step/increment at1.0 and reported
one-CPU numerical work. Seven-digit DAT quantities cannot certify1e-8 balance;
for example fine Fz has unloaded Fx=-7.41e-8N, while principal printed forces
allow rounding bounds up to5e-6N. Preserve the scientific criterion.

The installed solver wheel is unchanged27660d...f47ec,391 module bytes verified
against source/wheel/site before the batch. Native jobs run serially with
effective numerical pools1/JIT off and a600s/1GiB process-tree supervisor.
Largest native job:26.64s and274,550,784 sampled bytes. These are run observations,
not a performance gain or resource/scale qualification. No wheel rebuild,
unchanged regression campaign or F03 execution was needed.

## Failed screens and corrections

- B2 V1 one-member fixture is outside the current multi-member owner admission.
  V2 uses two physical members but its40-cell Fz screen returns the existing
  public `panel mixed-load resolution insufficient`. The recorded global
  contribution floor is8.326e-8N, or8.326e-9 of the10N applied component, compared
  with the1e-9 guard. This is numerical admission evidence, not a footprint
  physics failure. B2 accuracy was not compared. No guard, load, section or
  geometry tuning was used to force a pass.
- A read-only exception trace observes the same public failure and contributes
  its scalar diagnostic. That short trace was an ordinary disposable check,
  without the numerical batch supervisor; it supplies no resource qualification.
- Initial coarse GE V2 energy was inferred half external work and is not used
  as independent internal-energy evidence. Final native source computes0.5qKq
  and checks physical work, status, root wrench and pose mapping. All reused
  coarse controls receive the same post-checks; numerical inputs are unchanged.
- V2 external deck text underwent CRLF conversion. Its actual identity remains
  recorded; V3 stages exact ASCII bytes and verifies the metadata SHA. The
  earlier runs are preserved, not silently relabelled.
- Initial comparison code expected the wrong parser status. Its failed source
  is retained; corrected code verifies `PARSED_DEVELOPMENT_ONLY` with no
  qualification claim. It made no replacement numerical runs.

## Resulting action

Separate [independent review](review.md) finds no blocker to this development
slice and agrees with the stopping decision. It is not a scientific acceptance
or completed different-family review. Keep rigid-footprint physical transfer
evidence separate from BL5, point laws and distributing footprints.

Next: resolve the B2 component-resolution obstruction using its actual stored
matrix, loads and independent numerical controls. Do not relax tolerances or
launch another physical refinement automatically. Remaining E02 convergence,
thickness, precision and general connection obligations stay visible. The
complete programme and mandatory external/scale/release gates remain active.

[Raw identities and commands](raw-v1-identity.json) preserve inputs, source,
failures, output, supervisor settings and combined comparison. No main merge,
publication, default/version change or other-task communication occurred.
