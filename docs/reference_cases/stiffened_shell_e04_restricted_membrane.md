# Supplemental restricted nonlinear membrane feasibility

This is a new development fixture. It does not close E04's mandatory CalculiX
external row, roof response, capacity, G4D, release, or scientific acceptance.
The OpenSees comparator supplies supplemental material and axial-patch evidence.
The orchestrator completed the bounded v3 native/external supplemental screen;
its measured response is reported below without an acceptance claim.

## Frozen physical fixture and exact connector subspace

The shell occupies `0 <= x <= 1 m`, `0 <= y <= .1 m`, `z=0`, thickness `.002 m`.
Two rectangular Q4 cells use x stations `0,.5,1`; two straight three-node native
GE members occupy y edges `0,.1`, z `.01 m`, with the same x stations. Each beam
has centroidal rectangle `.01 x .004 m`. E is 210 GPa, nu .3. Density 7850 kg/m3
is static bookkeeping only. The offset enters the point bond once.

Every shell node has uy, uz and all three physical rotations fixed. Shell ux is
fixed at x=0. All six beam nodes are point-pose bonded to shell nodes, without
additional beam fixities. The two right shell nodes each receive 200 N times
the load factor. The frozen factor history is `.05,.15,.35,.6,1,.6,.2,1`.
It includes a subyield control, yielding, unloading and reloading.

Symmetry and uniform rectangular sections give ux=epsilon*x on both edges.
All physical and fitted shell rotations and both retained beam cell frames are
identity on this admitted pure-extension solution. The exact relative-pose
bond is `ub-us=(Rs-I)d`, `Rb=Rs`; at Rs=I it is exactly ub=us. The affine
OpenSees rigidLink thus equals the finite pose law on this subspace. This is
an exact restriction, not a small-rotation approximation of a rotating roof.
Every node, retained cell frame, resultant, multiplier and material-history
variable remains present. Runtime admission rejects nonaffine displacement,
nonzero constrained components, nonidentity frames, and connector gap.

Native selection is the public `CURVED_Q4_POINT_MATERIAL_REFERENCE_V1_DEV`
policy with `native_force_moment_roles_v1` scaling and algorithmic Q4 pullback.
The geometry is explicitly flat; this policy permits a flat special case and
publishes authoritative retained generalized station recovery. The plain flat
route currently omits those public station records. Preflight records the
actual policy, scaling and geometry, without claiming curved geometry.

## Source-grounded material and strain contracts

The canonical DNVC208MaterialCurve has sigma_prop=1 MPa, sigma_yield=2 MPa,
sigma_yield_2=2 MPa, eps_p_y1=.01, eps_p_y2=.02, K=2 MPa, n=.2. On alpha<.01,
the exact flow stress is `1e6+1e8*alpha Pa`; the harness checks the effective
canonical curve at every actual accepted native alpha. This changes no existing
material fixture or scientific tolerance. Actual native alpha must stay in
the first branch and become positive. The beam generalized section remains
elastic, with actual accumulated history identically zero.

OpenSees uses J2Plasticity with bulk `E/[3(1-2nu)]`, shear `E/[2(1+nu)]`,
sig0=sigInf=1 MPa, delta=0, H=100 MPa, eta=0, inside a PlateFiber section.
The official [J2Plasticity source](https://raw.githubusercontent.com/OpenSees/OpenSees/master/SRC/material/nD/J2Plasticity.cpp)
defines the exponential-plus-linear isotropic law; equal saturation and initial
stresses remove the exponential term. Its accumulated xi increments by
sqrt(2/3) times the radial-return multiplier, matching the equivalent plastic
strain invariant used by native J2. Native's projected plane-stress return map
and OpenSees' 3D return map with plane-stress condensation are separate
implementations; no exact discretized constitutive equality is assumed.

The [J2PlateFiber source](https://raw.githubusercontent.com/OpenSees/OpenSees/master/SRC/material/nD/J2PlateFiber.cpp)
enforces sigma_zz=0 by an internal solve. Its five components are
`eps_xx,eps_yy,gamma_xy,gamma_yz,gamma_zx`; shear strains are engineering
components and returned shear stresses are tensor components. Native layer
recovery uses the first three in the same order. Transverse shear, bending and
rotation are zero in this fixture; their differing shell formulations cannot
be inferred equivalent outside the admitted patch.

The external ShellMITC4 has four in-plane Gauss points and the PlateFiber
section five thickness fibers; native Q4 has four points and three Lobatto
layers. All material points experience the same uniform membrane strain here,
so thickness integration is exact for this mode. Actual fiber stress/strain
responses are requested using `material p fiber f stress/strain`, as supported
by [ShellMITC4](https://raw.githubusercontent.com/OpenSees/OpenSees/master/SRC/element/shell/ShellMITC4.cpp)
and [MembranePlateFiberSection](https://raw.githubusercontent.com/OpenSees/OpenSees/master/SRC/material/section/MembranePlateFiberSection.cpp).
Missing, malformed, or nonfinite quantities raise UnsupportedQuantity; an
elastic stress formula is never substituted for plastic material recovery.

The beam contract is established from `_ge_beam3_p5/compensated.py` and
`_ge_beam3_retained_generalized.py`: each half-cell chord change is
`U.T*d-d0`, mapped at stations by `reference.frame(xi).T/jacobian(xi)`.
For the straight midpoint reference, identity frames and ux=epsilon*x,
this is engineering epsilon, not logarithmic or Green strain. The section
returns N=EA*epsilon and zero remaining strain/resultant components.
One native GE member therefore matches two external ElasticTimoshenkoBeam
halves in this axial mode. Actual native station strain/resultants verify
this statement before any comparison. Centroidal area, both second moments,
Saint-Venant rectangle torsion and 5/6 shear areas are supplied identically.
No general element equality or bending comparison follows from this patch.

## Observables, controls and evidence limits

At each factor both owners retain actual shell layers, engineering axial
strain, shell stress uniformity, beam axial virtual work, shell axial virtual
work and applied virtual work. Native saves complete public material records,
the last accepted binary checkpoint and preflight. External saves actual
beam end resisting forces and all 40 fiber strain/stress records. Failures
retain prior records and status/error; no failed output is replaced by zeros.

The first factor has the independent elastic solution
`epsilon=F/[width*t*E/(1-nu^2)+2*E*A]`, with shell sigma_xx=E/(1-nu^2)*epsilon
and sigma_yy=nu*sigma_xx. Runtime checks this before the plastic comparison.
At every endpoint the axial balance is
`width*t*sigma_xx+2*EA*epsilon=F`. Virtual work is
`width*t*L*sigma_xx*epsilon + sum(w*N*epsilon) = F*L*epsilon`.
Native uses actual paired station fields and reference measures in the sum;
external uses actual beam resisting forces dotted with nodal displacement.
This is endpoint virtual work, not stored energy or accumulated dissipative work.
The harness does not apply half of F*u to nonlinear energy.

Runtime routes are separate. Native uses the installed Python 3.14 dependency
environment with actual ANYsolver, SciPy and Numba; external uses Python 3.12,
its compatible NumPy and OpenSees, without importing ANYsolver, SciPy or Numba.
The OpenSees site is appended after the supervised Python 3.12 dependency paths.
Runtime evidence records the executable/version, route-specific actual import
paths and source hashes, external extension-binary SHA256, applicable JIT/thread
settings and effective numerical pools after importing numerical libraries.
External verifies the supervisor's JIT-off and numerical environment, explicitly
recording that the unimported Numba runtime is not measured. Native
material recovery requires exactly elements 1 and 2 with complete finite
12x3 strain/stress and 12-entry alpha arrays. The raw last-accepted material
and checkpoint are written before inventory checks, preserving unexpected
shapes as failure evidence instead of truncating a zip.

Native actual alpha is authoritative. OpenSees' public fiber response does not
provide xi/plastic-history here, so external alpha is explicitly an inferred
constitutive diagnostic: plastic strain equals total strain minus elastic
compliance times actual stress, with plastic zz inferred from plastic
incompressibility. Increment norms accumulate sqrt(2/3 dep:dep), including
half the engineering plastic shear square. This is not a claimed direct
external history oracle. It must remain below .01 and evidence positive
plastic activity; cross-engine alpha equality is not scored. The comparison
reports measured strain/stress differences and has no newly invented
acceptance threshold. External support wrench, capacity, eigenpairs,
finite-port moments, and beam fiber stresses are not claimed observables.

## Next bounded check

The orchestrator must schedule each authorised route as a serial job within
the existing aggregate budget of 600 s,
2 GiB, numerical pools=1 and NUMBA_DISABLE_JIT=1, using the established
supervisor and installed Python 3.12/OpenSees environment. No sweeps, penalties,
artificial mass, symmetrization, or qualification campaign are authorized.

`<python314> scripts/r8_e04_restricted_membrane.py --route native --output <new-native-directory>`

`<python312> scripts/r8_e04_restricted_membrane.py --route external --opensees-site <installed-opensees-site> --output <new-external-directory>`

`<python> scripts/r8_e04_restricted_membrane.py --route compare --native-input <new-native-directory>/native.json --external-input <new-external-directory>/external.json --output <new-comparison-directory>`

Comparison imports no numerical runtimes, requires both adjacent status records
to show completed matching routes and matching nonempty originating script
SHA256 identities, and records input SHA256 identities. A comparator-only edit
does not require rerunning unchanged historical mechanics: comparison checks
the originating native/external identities against one another, rather than
the later comparator's own full-script hash. Future route evidence also carries
an explicit frozen geometry/material/history signature; present signatures must
match, and mixed signed/unsigned evidence is rejected. Historical v3 predates
that field and retains its original matching-source identity. All
routes use identical frozen geometry, materials, targets and checks; only
runtime/dependency routing changes. Every output directory must be new.
The combined screen-v1 failed before mechanics because compatible SciPy was
absent from Python 3.12 and the appended site exposed Python 3.14 SciPy.
That failed evidence remains retained; it is not constitutive failure evidence.
The first separated native attempt also stopped before evaluation: its
25-iteration request exceeded the public route's maximum of 24. The harness
now requests 24 with the existing 12-backtrack control; solver budgets and
public admission are unchanged, and the failed attempt remains retained.

Focused tests: `pytest tests/test_stiffened_shell_e04_restricted_membrane.py`.
The orchestrator passed the eight pre-identity-delta focused contracts in
1.45 s. This final comparison-identity repair adds one focused regression;
its rerun remains pending. The two Python sources pass AST inspection.

The retained evidence root is
`.qualification/b3-ge-e4-pl/r8-restricted-nonlinear-reference-dev-20261005-v1`.
The orchestrator reports v3 native 6.164 s, external .297 s and comparison
.157 s, all completed with the same originating script SHA256
`b9e0d3294d2c5cbd9e3763f601d72d869f623fe374e7b84400683d29dfb1032a`.
Actual native alpha reached approximately `5.837e-6`, safely inside the matched
first branch. Maximum observed shell stress difference was `.01575 Pa` and
axial strain difference `1.870e-13`. These are measured differences from this
fixture/history, not an adopted external acceptance threshold or general
nonlinear shell/beam equivalence claim. Files `native-screen-v3`,
`external-screen-v3` and `comparison-v3` retain raw route records/status;
they are unchanged by the comparator identity repair.
The byte-exact executed v3 harness is preserved as `raw/executed-script-v3.py`
under the same evidence root, allowing the recorded source SHA to be checked
independently of later comparator-only changes.

Native v3 imported installed candidate ANYsolver from the recorded
`r8-native-turning-dev-20261005-v1/site-progress-v1/anysolver` directory,
but canonical ANYmaterial came from sibling source
`C:/Github/ANYmaterial/src/anymaterial/__init__.py`, not an installed material
wheel. Native status records that actual path and its SHA256. This is explicit
development dependency provenance, not installed-artifact qualification of
the complete solver/material package pair.
If a local constitutive or patch precondition fails, retain the failure and
resolve its equation/response boundary before any refinement or new run.

The mandatory future CalculiX comparator remains separate. A matched CPS4
plane-stress membrane plus independently verified T3D2 axial reduction or a
derived elastic SPRING2 axial-work reduction is a possible future control.
T3D2's internal beam/solid expansion means its EA response cannot be assumed
from its element label. CPS4 expansion also requires its own plane-stress and
thickness checks. Neither route is implemented or authorized by this fixture;
there is no U1 nonlinear substitute and no general finite-port/spectral claim.
