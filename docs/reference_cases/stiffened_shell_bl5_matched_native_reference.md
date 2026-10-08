# Matched native / released-director development reference

This tool constructs the adopted public native reference-linear model and checks
common physical work against the executed released-director specimen. It does
not score response accuracy, qualify BL5, or identify the two discrete spaces.
The previous released reference and its executed inputs remain immutable.

## Definition and independent section data

The plate is 1 m by .2 m, centered at y=0, midsurface z=0, thickness .02 m.
The Q4 grid has x=0,.25,.5,.75,1 and y=-.1,0,.1: 15 nodes / 8 facets. The
material line follows interior shared Q4 edges. The straight bar centroid is
(x,0,.04), width .04 m, height .06 m, physical section axes I. Two native B3
members share five nodes and retain all 48 internal coordinates / four cells.
No retained moment/history is changed or condensed by this tooling.

E=210 GPa, nu=.3. Four virgin physical fibres at y=+/-.04/sqrt(12),
z=+/-.06/sqrt(12), each area A/4, exactly integrate A=.0024 m2,
Iy=7.2e-7 m4 and Iz=3.2e-7 m4. Axial/biaxial stiffness is supplied ONLY by
these fibres; their unchanged flow curve starts at 1e20 Pa. Background contains
only shear and torsion. Rectangle parabolic traction complementary energy gives
integral(tau^2 dA)=6 V^2/(5A), hence k=5/6. This is a reduced beam approximation,
not exact three-dimensional continuum shear. Saint-Venant rectangle torsion uses
the odd Fourier solution of -Laplacian(Psi)=2, Psi=0 on the perimeter,
J=2 integral(Psi), with the analytic series and conservative positive tail bound
in `rectangular_section`. The tail bound certifies omitted mathematical terms,
not floating-point rounding. No observed displacement sets section constants.

Explicit rho=7850 kg/m3 supplies required native metadata:
rho diag(A,A,A,Iy+Iz,Iy,Iz), in centroid physical axes. The continuum static
reference has no density. There is no mass/dynamic comparison or qualification.
The public static solve uses stiffness and nodal loads, not this inertia.

The full shell x=0 edge is fixed in all six native shell coordinates; the bar
has no additional support. Only +1 N global Fz at bar centroid tip x=1 is applied.
The shell top arm is +.01 ez and bar bottom arm -.03 ez. The native BL5 arm is
(0,0,-.03), five channels, P0 / span1. This is an existing experimental
representation, not a selected qualified multiplier policy.

## Work correspondence and its limits

At the flat reference the native basis is ex,ey and reference director ez.
The original continuum physical gap is c_ext=(ubottom-utop, db_xy-ds_xy).
Native c_native is shell minus beam in the beam frame: c_native=-c_ext on the
common infinitesimal material face-pair lift. Its actual local Jacobian includes
the shell .01 arm and the beam -.03 arm. Actual nodal/cell covectors and continuum
face forces are checked through their transpose work and common-origin wrench.

Native rows integrate ds*c: units m2 for three position rows, m for two director
rows. Density multipliers have units N/m and N. Continuum station multipliers
have units N and Nm. For a genuinely continuous affine common gap on each .25 m
support, lambda_ext(j)=-.125 times the sum of adjacent native density vectors.
This 20-to-25 dual pullback preserves common virtual work; it is not invertible
and does not prove row-space equivalence or equality of constraint kernels.

The global common controls use actual 102-node C3D20 coordinates/connectivity
and its serendipity interpolation at all eight native Gauss points. Shell
translations are globally affine in x, directors uniform and independent of
the geometric normal; shell thickness lifting is not a rigid rotation of the
whole plate. The bar section lift includes both y and z centroid arms, with a
single uniform section spin. Exact supported common controls require zero shell
constant translation and zero shell spin, so the whole root face is fixed.
Clipping a nonzero uniform shell spin at the native root produces a .25 m kink
inside a .5 m continuum brick and is explicitly rejected as a common-field proof.
Arbitrary local five-channel algebra is separately tested and is not a claim
of global continuum representability.

At x=.25,.5,.75 native cells have TWO independent rotation sides. Their two
physical directors can disagree; one shared continuum station cannot represent
both. No averaging, identification or discarded side is introduced. The native
weak four-support / 20-row space and continuum strong five-station / 25-row space
remain different. Finite common rigid motion and actual physical/chart derivative
controls concern the finite native operator only; the continuum law is linear.

Released normal spin and nonzero transverse shear are independent controls. A
supported field uz=.2 x with both directors ez yields zero five-channel gap while
the actual compensated native chord has gamma_xz=.2; its geometric normal tilts.
The script preserves this freedom rather than reconstructing the director from
the surface normal. A normal-spin field has zero interface work on the declared
zero normal arm. Neither condition chooses a new law or multiplier space.

## Verification state

Implementation prepared for one installed-artifact controls batch plus one
virgin public reference-linear solve, under 600 s / 2 GiB process-tree bound,
one affinity CPU / numerical pools one / JIT off. Results will record actual
imports, versions, source/input SHA, JUnit, equilibrium/constraint and complete
support wrench. The solve is an operator/equilibrium calibration only. No CCX
execution, refinement, native response score or acceptance campaign is part of
this slice. Scientific acceptance, body model correspondence,
discrete-space convergence and physical accuracy remain open. Scientific
independent review remains required under its applicable contracts; a different
model family is preferred. The cached OpenAI fallback is supporting evidence.
Calibration work closure is tested with the prospectively declared denominator
max(abs(applied work),1e-12 J), and internal/applied plus interface ratios <=1e-8.

## Executed outcome (2026-10-06)

Verified against the assigned development controls, with scientific acceptance
open. The installed wheel is SHA256
`b3d5f572797f3c2954d1bf9dc1c6b4293da14c5812e543dbde7f314a60207291`.
All 424 installed Python module hashes matched the prior installed manifest.
Actual imports remain inside that artifact; dependency imports use the existing
CI4 site: NumPy 2.5.3, SciPy 1.18.1, Numba .68.0, llvmlite .50.0. Pytest 9.0.3
and psutil 7.2.2 are recorded with actual paths. Effective loaded numerical pools
one, Numba threads one / JIT disabled, affinity [0]; OPENBLAS_CORETYPE unforced.
These measured settings are not a claim of general CI equivalence.

One public virgin `solve_linear` completed. Free equilibrium ratio
7.820467370209954e-13, constraint maximum 1.4665879521961728e-22, complete global
support/applied wrench residual maximum 4.027889133340068e-12. Applied pairing
1.2775155904068065e-6 J; internal/applied relative discrepancy
4.802004896500546e-13; interface-work ratio 9.495052772090266e-17. The pairing is
calibration evidence, not a continuum/native displacement or accuracy score.
The exact public input record includes native immutable definition bytes, shell
geometry, section data, support IDs, load, arm, basis and model identity.

The complete control coverage is 13 tests: V2 ten passed / three failed; V3 one
repaired shear control passed / two failed; V4 the two repaired common-field
controls passed. Passing unaffected tests and the one calibration were not
repeated. V2 failures were reversed helper wrench arguments and a three-field
beam-parts tuple unpacked as two. V3 preserved shifted-origin cancellation:
directly forming (point-origin) cross opposing face forces gave 2.9843e-13 at
the unchanged 2e-13 assertion. The new own-tool helper sums F and M0 first, then
transports M(origin)=M0-origin cross F. No physical map, fields, density or
tolerance changed; the original external helper remains immutable.

Preflight sandbox access refusal and the V1 thread-ceiling failure are retained.
V1 stopped before collection/calibration after the sampler counted the exact
Python314 `_wmi.pyd` query helper plus main thread. Root prospectively classified
ONLY `C:/Python/Python314/DLLs/_wmi.pyd` with successful queried start address as
support, using CPython 3.14 `PC/_wmimodule.cpp` `_query_thread` COM/WMI semantics.
The local pyd hash and primary URL are preserved in WMI classification records.
All original/total/support thread records remain in the samples; unresolved or
numerical start ceiling stays one. No numerical pool/resource bound was relaxed.

Raw root: `.qualification/b3-ge-e4-pl/r8-bl5-matched-native-dev-20261005-v1`.
V2 supervisor 3.2872344 s, sampled RSS 184299520 B; V3 2.9291402 s / 183250944 B;
V4 2.5763561 s / 181272576 B. Each numerical/unresolved maximum was one; bounds
600 s / 2 GiB tree. Sampling is not comprehensive peak/thread qualification.
Bindings, script/test snapshots, JUnit, stdout/stderr, runtime, input and single
calibration remain versioned. Final prose postdates the executed bindings.

Final source SHA256:
`068ae3ae16fe167d3052a02e8ecf0b7c6c0c3ba83f0db1f79ab5dfd07a75d9a8`;
test SHA256:
`76cf6ea815fc45441daad13bdca50ba8221f43369a32af162d94922b7f52b74a`.
The V2 calibration-bound source was
`d594aeb320e78a1eefc9d4fa619448384b9d167c988f3703427716223e954935`;
the sole subsequent source addition is the independent origin-transport helper,
unused by the public calibration. V2 input SHA256
`5fe2568e4688b9d9c6aad8560ccab724b109ec87dc7a9458e0d26bbb2a25685c`;
calibration SHA256
`ffdbe095aa64a303c9d67e75f84db1fab8ca3b6dbac0f87b609d6d826478f7ee`.

Exact executed commands were Python314 `run-v2.py`, `run-v3.py`, `run-v4.py`
inside that raw root; their saved commands and entry files declare selection and
actual environment. They refuse reused output destinations. For a new authorized
standalone calibration, the public definition is reproducible with
`python -m scripts.r8_bl5_matched_native_reference --output <fresh-directory>`
under the same installed-site/dependency environment and bounded supervisor.
This command is documentation, not new execution authority.

The actionable result is a valid affine common-work pullback and a working native
reference input; general broken-side traces and the strong-versus-weak spaces
remain unmatched. There is no justified response score or automatic continuum
refinement. Root must decide the matched discrete-space/reference question before
any subsequent physical comparison; no law selection follows from this result.
